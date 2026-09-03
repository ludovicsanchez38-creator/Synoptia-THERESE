"""B-283 : la page d'erreur OAuth servie par le navigateur système doit rester lisible.

Cette page est du HTML écrit à la main dans `routers/email.py` : elle échappe
aux jetons de thème du frontend, donc rien ne l'empêchait de dériver hors de la
palette. La ligne « Erreur Google » était en #6B7BA4 sur #0B1226 à 0,85 rem,
soit 4,42:1 pour du texte courant, sous le seuil AA de 4,5:1
(docs/rules/RULES-DESIGN.md §1.2 et §9.1, WCAG 2.1 critère 1.4.3).

Le test ne verrouille aucune couleur en particulier : il relit le HTML servi,
apparie chaque déclaration `color:` avec la taille de texte de son bloc, et
applique le seuil correspondant (3:1 à partir de 24 px, 4,5:1 en dessous).
Un h1 magenta à 1,5 rem reste donc conforme, une mention de bas de page ne
peut plus l'être en dessous de 4,5:1.
"""

import re

import pytest

# Formule de luminance relative WCAG 2.1, identique à
# src/frontend/src/lib/accessibility.ts.
_SEUIL_TEXTE_COURANT = 4.5
_SEUIL_GRAND_TEXTE = 3.0
_PX_GRAND_TEXTE = 24.0
_PX_GRAND_TEXTE_GRAS = 18.66
_PX_PAR_REM = 16.0

# `background-color:` ne doit pas être pris pour une couleur de texte.
_COULEUR = re.compile(r"(?<![-a-zA-Z])color\s*:\s*(#[0-9A-Fa-f]{6})\b")
_TAILLE = re.compile(r"font-size\s*:\s*([0-9.]+)\s*(rem|px|em)")
_GRAISSE = re.compile(r"font-weight\s*:\s*(bold|[6-9]00)")
_FOND = re.compile(r"background\s*:\s*(#[0-9A-Fa-f]{6})")


def _canal(valeur: int) -> float:
    c = valeur / 255
    return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4


def _luminance(hexa: str) -> float:
    h = hexa.lstrip("#")
    r, v, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return 0.2126 * _canal(r) + 0.7152 * _canal(v) + 0.0722 * _canal(b)


def _contraste(avant: str, arriere: str) -> float:
    la, lb = _luminance(avant), _luminance(arriere)
    haut, bas = max(la, lb), min(la, lb)
    return (haut + 0.05) / (bas + 0.05)


def _blocs_de_declarations(html: str) -> list[tuple[str, str]]:
    """(origine lisible, déclarations CSS) pour le <style> et chaque style inline."""
    blocs: list[tuple[str, str]] = []
    for feuille in re.findall(r"<style>(.*?)</style>", html, re.S):
        for regle in feuille.split("}"):
            selecteur, sep, declarations = regle.partition("{")
            if sep:
                blocs.append((selecteur.strip() or "?", declarations))
    for inline in re.findall(r'style="([^"]*)"', html):
        blocs.append(("style inline", inline))
    return blocs


def _taille_en_px(declarations: str) -> float:
    trouve = _TAILLE.search(declarations)
    if not trouve:
        return _PX_PAR_REM  # défaut du navigateur, aucune taille déclarée
    valeur, unite = float(trouve.group(1)), trouve.group(2)
    return valeur if unite == "px" else valeur * _PX_PAR_REM


def _seuil(declarations: str, selecteur: str) -> float:
    px = _taille_en_px(declarations)
    gras = bool(_GRAISSE.search(declarations)) or selecteur.strip() in {
        "strong", "b", "h1", "h2", "h3",
    }
    if px >= _PX_GRAND_TEXTE or (gras and px >= _PX_GRAND_TEXTE_GRAS):
        return _SEUIL_GRAND_TEXTE
    return _SEUIL_TEXTE_COURANT


def _fond_de_page(html: str) -> str:
    for selecteur, declarations in _blocs_de_declarations(html):
        if selecteur.startswith("body"):
            trouve = _FOND.search(declarations)
            if trouve:
                return trouve.group(1)
    raise AssertionError("aucun fond de page trouvé dans la feuille de style")


def _defauts_de_contraste(html: str) -> list[str]:
    fond = _fond_de_page(html)
    defauts: list[str] = []
    for selecteur, declarations in _blocs_de_declarations(html):
        for couleur in _COULEUR.findall(declarations):
            seuil = _seuil(declarations, selecteur)
            mesure = _contraste(couleur, fond)
            if mesure < seuil:
                defauts.append(
                    f"{selecteur} : {couleur} sur {fond} = {mesure:.3f} "
                    f"(seuil {seuil}, taille {_taille_en_px(declarations):.1f} px)"
                )
    return defauts


class TestContrasteDeLaPageOAuth:
    """Les trois branches HTML atteignables sans mock du service OAuth."""

    @pytest.mark.asyncio
    async def test_refus_google_access_denied(self, client):
        reponse = await client.get(
            "/api/email/auth/callback-redirect", params={"error": "access_denied"}
        )
        assert reponse.status_code == 400
        assert "Erreur Google" in reponse.text
        assert _defauts_de_contraste(reponse.text) == []

    @pytest.mark.asyncio
    async def test_autre_erreur_oauth(self, client):
        reponse = await client.get(
            "/api/email/auth/callback-redirect", params={"error": "invalid_scope"}
        )
        assert reponse.status_code == 400
        assert _defauts_de_contraste(reponse.text) == []

    @pytest.mark.asyncio
    async def test_parametres_manquants(self, client):
        reponse = await client.get("/api/email/auth/callback-redirect")
        assert reponse.status_code == 400
        assert _defauts_de_contraste(reponse.text) == []


class TestLInstrumentMesureBien:
    """Un test de contraste qui ne sait pas mesurer rendrait toute page verte."""

    def test_les_reperes_wcag_connus(self):
        # Valeurs de référence recalculées par la reproduction c2-RP24.
        assert round(_contraste("#6B7BA4", "#0B1226"), 3) == 4.425
        assert round(_contraste("#B6C7DA", "#0B1226"), 3) == 10.783
        assert round(_contraste("#FFFFFF", "#000000"), 1) == 21.0

    def test_un_defaut_fabrique_est_bien_vu(self):
        html = (
            "<style>body{background:#0B1226}"
            "p{color:#6B7BA4;font-size:0.85rem}</style><body></body>"
        )
        assert len(_defauts_de_contraste(html)) == 1

    def test_le_grand_texte_garde_son_seuil_de_3(self):
        html = "<style>body{background:#0B1226}h1{color:#E11D8D;font-size:1.5rem}</style>"
        assert _defauts_de_contraste(html) == []
