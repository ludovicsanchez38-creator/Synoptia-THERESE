"""Une seule fenêtre locale pour le bornage R2 et le transport Ollama."""
import os
from typing import Any


def plafond_memoire() -> int:
    """BUG-052 sous 8 Gio, 16k sous 16 Gio, fenêtre modèle plafonnée à 128k au-delà."""
    try:
        ram = os.sysconf('SC_PHYS_PAGES') * os.sysconf('SC_PAGE_SIZE')
    except (AttributeError, ValueError, OSError):
        return 8192
    return 8192 if ram < 8 * 1024**3 else (16384 if ram < 16 * 1024**3 else 131072)


def fenetre_ollama(config: Any) -> int:
    # Ne jamais augmenter une petite fenêtre annoncée par le modèle.
    fenetre = config.context_window
    return min(fenetre, plafond_memoire()) if isinstance(fenetre, int) else 0


def estimer_jetons(texte: str) -> int:
    """Estimation locale explicite, jamais des octets comparés à des jetons.

    Le banc Qwen français/JSON mesure 3,8 à 4 octets/jeton. 3,5 garde
    une marge de 8 à 14 %, plus les enveloppes du chat. Les caractères hors
    alphabet latin gardent leur coût UTF-8 pessimiste. Aucun téléchargement.
    Ce n'est pas un tokenizer exact : les compteurs du banc restent l'oracle.
    """
    latin = sum(len(c.encode('utf-8')) for c in texte if ord(c) < 0x250)
    autres = sum(len(c.encode('utf-8')) for c in texte if ord(c) >= 0x250)
    return (latin * 2 + 6) // 7 + autres


async def actualiser_fenetre(config: Any, client: Any) -> None:
    """Lire /api/show local une fois par configuration, avant toute sélection.

    Échec/serveur distant : catalogue et plafond RAM conservés. Le POST show
    ne génère rien et ne charge pas le modèle. Aucune supposition par nom.
    """
    from urllib.parse import urlsplit
    if getattr(config, 'ollama_show_lu', False):
        return
    config.ollama_show_lu = True
    adresse = (config.base_url or 'http://127.0.0.1:11434').rstrip('/')
    if urlsplit(adresse).hostname not in ('localhost', '127.0.0.1', '::1'):
        return
    try:
        response = await client.post(adresse + '/api/show', json={'model': config.model}, timeout=3)
        response.raise_for_status()
        info = response.json().get('model_info', {})
        architecture = info.get('general.architecture')
        fenetre = info.get(f'{architecture}.context_length')
        if isinstance(fenetre, int) and not isinstance(fenetre, bool) and 0 < fenetre <= 10_000_000:
            config.context_window = fenetre
    except Exception:
        # Un serveur ancien/hors ligne ne ferme pas le chat.
        return
