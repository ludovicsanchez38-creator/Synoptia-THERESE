"""
THÉRÈSE v2 - Browser Agent Service

Navigation web automatisée via Playwright.
v0.6 - Inspiré de Manus Browser Operator.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from app.config import settings

logger = logging.getLogger(__name__)

# Timeout global par action (secondes)
ACTION_TIMEOUT_MS = 30_000

# Protocoles autorisés
ALLOWED_SCHEMES = {"http", "https"}

# User-Agent réaliste (Chrome 120 sur macOS)
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

# Limite de caractères pour le contenu extrait
MAX_CONTENT_LENGTH = 5_000

# Limite de liens retournés
MAX_LINKS = 50


@dataclass
class BrowserResult:
    """Résultat d'une action du browser agent."""

    success: bool
    action: str
    url: str = ""
    title: str = ""
    content: str = ""
    screenshot_path: str | None = None
    links: list[dict[str, str]] = field(default_factory=list)
    error: str | None = None


def _validate_url(url: str) -> str | None:
    """Valide qu'une URL utilise un protocole autorisé.

    Retourne un message d'erreur si l'URL est invalide, None sinon.
    """
    from urllib.parse import urlparse

    try:
        parsed = urlparse(url)
    except (ValueError, TypeError) as e:
        logger.debug("URL invalide: %s", e)
        return f"URL invalide : {url}"

    if not parsed.scheme:
        return "URL sans protocole. Utilisez http:// ou https://"

    if parsed.scheme.lower() not in ALLOWED_SCHEMES:
        return (
            f"Protocole '{parsed.scheme}' interdit. "
            f"Seuls {', '.join(sorted(ALLOWED_SCHEMES))} sont autorisés."
        )

    # Cycle 6 (revue des lecteurs, confirmé par Grok) : le protocole ne
    # suffit pas. Le moteur écoute sur 127.0.0.1 et `/api/auth/token` est
    # exempté d'authentification : une URL proposée par le modèle vers la
    # machine elle-même ou le réseau privé ramènerait le jeton de session
    # (ou un service LAN) dans la conversation.
    if _cible_locale_ou_privee(parsed.hostname):
        return "Cible interdite : le navigateur interne ne visite ni la machine locale ni le réseau privé."

    return None


def _cible_locale_ou_privee(hostname: str | None) -> bool:
    """Vrai pour localhost, une adresse de boucle, privée, de lien local,
    réservée ou non spécifiée. Un nom d'hôte public passe (pas de résolution DNS ici)."""
    import ipaddress

    if not hostname:
        return True
    hote = hostname.strip("[]").lower()
    if hote == "localhost" or hote.endswith(".localhost") or hote.endswith(".local") or hote.endswith(".internal"):
        return True
    try:
        adresse = ipaddress.ip_address(hote)
    except ValueError:
        return False
    return (
        adresse.is_private or adresse.is_loopback or adresse.is_link_local
        or adresse.is_reserved or adresse.is_unspecified or adresse.is_multicast
    )


class BrowserAgent:
    """Agent de navigation web via Playwright (Chromium headless).

    Gère une instance unique de browser par session.
    Lazy initialization : le browser n'est lancé qu'au premier usage.
    """

    def __init__(self) -> None:
        # Typés `Any` à dessein : sans annotation, mypy inférait tantôt `None`
        # (et signalait l'affectation du Playwright), tantôt rien, d'où un
        # compte d'erreurs qui flottait d'une exécution à l'autre (CI du
        # 08/09/2026, 978 contre 977). Les objets Playwright sont importés
        # paresseusement, l'extra e2e n'étant pas toujours installé.
        self._playwright: Any = None
        self._browser: Any = None
        self._page: Any = None
        self._outputs_dir = self._ensure_outputs_dir()

    def _ensure_outputs_dir(self) -> Path:
        """Crée et retourne le répertoire de sortie pour les screenshots."""
        outputs_dir = settings.data_dir / "outputs"
        outputs_dir.mkdir(parents=True, exist_ok=True)
        return outputs_dir

    @property
    def is_active(self) -> bool:
        """Indique si le browser est actuellement lancé."""
        return self._browser is not None and self._browser.is_connected()

    @property
    def current_url(self) -> str | None:
        """URL de la page courante, ou None si pas de page active."""
        if self._page and not self._page.is_closed():
            return self._page.url
        return None

    async def start(self) -> None:
        """Lance le browser Chromium headless si pas déjà lancé."""
        if self.is_active:
            return

        from playwright.async_api import async_playwright

        logger.info("Lancement du browser Chromium headless")
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
            ],
        )
        self._page = await self._browser.new_page(
            user_agent=USER_AGENT,
            viewport={"width": 1280, "height": 720},
            java_script_enabled=True,
        )
        logger.info("Browser Chromium démarré")

    async def stop(self) -> None:
        """Ferme le browser et libère les ressources."""
        if self._browser:
            try:
                await self._browser.close()
            except Exception as e:
                logger.warning(f"Erreur fermeture browser : {e}")
            self._browser = None
            self._page = None

        if self._playwright:
            try:
                await self._playwright.stop()
            except Exception as e:
                logger.warning(f"Erreur arrêt Playwright : {e}")
            self._playwright = None

        logger.info("Browser fermé")

    async def _ensure_page(self) -> None:
        """S'assure qu'une page active est disponible."""
        await self.start()
        if self._page is None or self._page.is_closed():
            self._page = await self._browser.new_page(
                user_agent=USER_AGENT,
                viewport={"width": 1280, "height": 720},
            )

    async def navigate(self, url: str) -> BrowserResult:
        """Navigue vers une URL et retourne le titre + contenu textuel."""
        error = _validate_url(url)
        if error:
            return BrowserResult(success=False, action="navigate", error=error)

        try:
            await self._ensure_page()
            response = await self._page.goto(url, timeout=ACTION_TIMEOUT_MS, wait_until="domcontentloaded")

            if response and response.status >= 400:
                return BrowserResult(
                    success=False,
                    action="navigate",
                    url=self._page.url,
                    error=f"HTTP {response.status}",
                )

            title = await self._page.title()
            text = await self._page.inner_text("body")
            content = text[:MAX_CONTENT_LENGTH] if text else ""

            logger.info(f"Navigation vers {url} - titre : {title}")
            return BrowserResult(
                success=True,
                action="navigate",
                url=self._page.url,
                title=title,
                content=content,
            )
        except Exception as e:
            logger.error(f"Erreur navigation vers {url} : {e}")
            return BrowserResult(
                success=False,
                action="navigate",
                url=url,
                error=str(e),
            )

    async def extract_text(self, selector: str | None = None) -> BrowserResult:
        """Extrait le texte de la page courante ou d'un sélecteur CSS."""
        try:
            await self._ensure_page()
            target = selector or "body"
            text = await self._page.inner_text(target, timeout=ACTION_TIMEOUT_MS)
            content = text[:MAX_CONTENT_LENGTH] if text else ""
            title = await self._page.title()

            return BrowserResult(
                success=True,
                action="extract_text",
                url=self._page.url,
                title=title,
                content=content,
            )
        except Exception as e:
            logger.error(f"Erreur extraction texte (sélecteur={selector}) : {e}")
            return BrowserResult(
                success=False,
                action="extract_text",
                url=self.current_url or "",
                error=str(e),
            )

    async def screenshot(self) -> BrowserResult:
        """Prend un screenshot de la page courante."""
        try:
            await self._ensure_page()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"screenshot_{timestamp}.png"
            filepath = self._outputs_dir / filename

            await self._page.screenshot(path=str(filepath), full_page=False, timeout=ACTION_TIMEOUT_MS)
            title = await self._page.title()

            logger.info(f"Screenshot sauvegardé : {filepath}")
            return BrowserResult(
                success=True,
                action="screenshot",
                url=self._page.url,
                title=title,
                screenshot_path=str(filepath),
            )
        except Exception as e:
            logger.error(f"Erreur screenshot : {e}")
            return BrowserResult(
                success=False,
                action="screenshot",
                url=self.current_url or "",
                error=str(e),
            )

    async def click(self, selector: str) -> BrowserResult:
        """Clique sur un élément identifié par un sélecteur CSS."""
        try:
            await self._ensure_page()
            await self._page.click(selector, timeout=ACTION_TIMEOUT_MS)
            # Attendre la stabilisation après le clic
            await self._page.wait_for_load_state("domcontentloaded", timeout=ACTION_TIMEOUT_MS)
            title = await self._page.title()

            return BrowserResult(
                success=True,
                action="click",
                url=self._page.url,
                title=title,
                content=f"Clic effectué sur '{selector}'",
            )
        except Exception as e:
            logger.error(f"Erreur clic sur '{selector}' : {e}")
            return BrowserResult(
                success=False,
                action="click",
                url=self.current_url or "",
                error=str(e),
            )

    async def fill(self, selector: str, value: str) -> BrowserResult:
        """Remplit un champ de formulaire identifié par un sélecteur CSS."""
        try:
            await self._ensure_page()
            await self._page.fill(selector, value, timeout=ACTION_TIMEOUT_MS)
            title = await self._page.title()

            return BrowserResult(
                success=True,
                action="fill",
                url=self._page.url,
                title=title,
                content=f"Champ '{selector}' rempli",
            )
        except Exception as e:
            logger.error(f"Erreur remplissage '{selector}' : {e}")
            return BrowserResult(
                success=False,
                action="fill",
                url=self.current_url or "",
                error=str(e),
            )

    async def get_links(self) -> BrowserResult:
        """Liste les liens de la page courante (titre + href, max 50)."""
        try:
            await self._ensure_page()
            title = await self._page.title()

            links_data = await self._page.evaluate("""
                () => {
                    const links = Array.from(document.querySelectorAll('a[href]'));
                    return links.slice(0, %d).map(a => ({
                        text: (a.textContent || '').trim().substring(0, 200),
                        href: a.href
                    })).filter(l => l.href && l.href.startsWith('http'));
                }
            """ % MAX_LINKS)

            return BrowserResult(
                success=True,
                action="get_links",
                url=self._page.url,
                title=title,
                content=f"{len(links_data)} lien(s) trouvé(s)",
                links=links_data,
            )
        except Exception as e:
            logger.error(f"Erreur extraction des liens : {e}")
            return BrowserResult(
                success=False,
                action="get_links",
                url=self.current_url or "",
                error=str(e),
            )

    async def execute_action(self, action: str, params: dict) -> BrowserResult:
        """Dispatcher générique qui appelle la bonne méthode selon l'action.

        Actions supportées : navigate, extract_text, screenshot, click, fill, get_links.
        """
        dispatch = {
            "navigate": lambda: self.navigate(params.get("url", "")),
            "extract_text": lambda: self.extract_text(params.get("selector")),
            "extract": lambda: self.extract_text(params.get("selector")),
            "screenshot": lambda: self.screenshot(),
            "click": lambda: self.click(params.get("selector", "")),
            "fill": lambda: self.fill(params.get("selector", ""), params.get("value", "")),
            "get_links": lambda: self.get_links(),
            "links": lambda: self.get_links(),
        }

        handler = dispatch.get(action)
        if handler is None:
            return BrowserResult(
                success=False,
                action=action,
                error=f"Action inconnue : '{action}'. "
                      f"Actions disponibles : {', '.join(sorted(dispatch.keys()))}",
            )

        return await handler()


# --- Singleton global ---

_browser_agent: BrowserAgent | None = None


def get_browser_agent() -> BrowserAgent:
    """Retourne l'instance singleton du BrowserAgent."""
    global _browser_agent
    if _browser_agent is None:
        _browser_agent = BrowserAgent()
    return _browser_agent
