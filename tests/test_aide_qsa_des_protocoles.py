"""
B-150 : l'aide `qsa` des protocoles était appelée sans jamais avoir été définie.

Elle a été introduite le 01/09/2026 pour remplacer un `||` entre deux NodeList
qui rendait les verdicts vides (« pas de doublon », « zéro donnée restante »
étaient vrais quoi qu'il arrive). Mais elle n'existait que dans un BLOCQUOTE
d'en-tête, qui n'est aucune des étapes numérotées : la première étape qui
l'appelle lève `ReferenceError: qsa is not defined`. Le recueil est passé d'un
faux vert silencieux à un arrêt brut.

Deux faits imposent la forme du correctif :

1. chaque étape `javascript_tool` est une ÉVALUATION séparée dans la page ;
2. un `navigate →` recharge la page et remet `window` à zéro - le scénario 10
   navigue entre ses étapes 21, 24 et 27, qui appellent toutes `qsa`.

Une injection unique en tête de scénario ne suffirait donc pas. L'invariant
posé ici : **toute étape qui appelle `qsa` la dépose elle-même**, sur `window`,
dans la même étape.
"""

import re
from pathlib import Path

import pytest

PROTOCOLES = Path(__file__).resolve().parent / "protocols"

# Deux recueils, deux mises en page : catastrophes.md numerote ses etapes
# (« 13. javascript_tool : »), S3-dsi-admin.md les titre (« #### Etape 22 »).
# L unite qui compte dans les deux cas est l EVALUATION : ce qui part d un
# coup dans la page. Une nouvelle evaluation commence a une etape numerotee, a
# un titre, a un appel « javascript_tool » ou a une bordure de bloc de code.
BORDURE = re.compile(r"^\s*(\d+\.|#{1,6}\s|```|- \*\*|javascript_tool)")
APPEL_JS = "javascript_tool"
LIGNE_CITEE = re.compile(r"^\s*>")
DEFINITION = "window.qsa"


def _fichiers_qui_utilisent_qsa() -> list[Path]:
    return sorted(
        chemin
        for chemin in PROTOCOLES.rglob("*.md")
        if "qsa(" in chemin.read_text(encoding="utf-8")
    )


def _etapes_qui_appellent_qsa(chemin: Path) -> list[tuple[int, list[str]]]:
    """Découpe le document en évaluations et rend celles qui appellent qsa.

    Les lignes de citation (`>`) sont écartées : la prose d'en-tête n'est pas
    une étape, et c'est précisément le défaut d'origine.
    """
    etapes: list[tuple[int, list[str]]] = []
    courante: list[str] = []
    premiere_ligne = 0

    for numero, ligne in enumerate(chemin.read_text(encoding="utf-8").splitlines(), 1):
        if LIGNE_CITEE.match(ligne):
            continue
        if BORDURE.match(ligne) or APPEL_JS in ligne:
            if courante:
                etapes.append((premiere_ligne, courante))
            courante = [ligne]
            premiere_ligne = numero
        elif courante:
            courante.append(ligne)
    if courante:
        etapes.append((premiere_ligne, courante))

    appelantes = []
    for debut, lignes in etapes:
        appels = [ligne for ligne in lignes if "qsa(" in ligne and DEFINITION not in ligne]
        if appels:
            appelantes.append((debut, lignes))
    return appelantes


class TestChaqueEtapeDeposeLAideQuElleAppelle:
    def test_le_recueil_utilise_bien_l_aide(self):
        """Sans ce garde-fou, le test passerait à vide le jour où qsa disparaît."""
        fichiers = _fichiers_qui_utilisent_qsa()
        assert fichiers, "aucun protocole n'utilise qsa : ce test ne vérifie plus rien"
        total = sum(len(_etapes_qui_appellent_qsa(f)) for f in fichiers)
        assert total >= 9, f"seulement {total} étape(s) appelante(s) trouvée(s), 9 attendues"

    @pytest.mark.parametrize(
        "chemin", _fichiers_qui_utilisent_qsa(), ids=lambda c: c.name
    )
    def test_aucune_etape_n_appelle_qsa_sans_l_avoir_deposee(self, chemin: Path):
        manquantes = [
            debut
            for debut, lignes in _etapes_qui_appellent_qsa(chemin)
            if not any(DEFINITION in ligne for ligne in lignes)
        ]
        assert not manquantes, (
            f"{chemin.relative_to(PROTOCOLES.parent.parent)} : "
            f"étape(s) commençant ligne(s) {manquantes} appellent qsa sans la déposer. "
            "Chaque javascript_tool est une évaluation séparée et un navigate remet "
            "la page à zéro : l'aide se redépose dans l'étape qui s'en sert."
        )

    @pytest.mark.parametrize(
        "chemin", _fichiers_qui_utilisent_qsa(), ids=lambda c: c.name
    )
    def test_l_aide_est_posee_sur_window_pas_declaree_localement(self, chemin: Path):
        """`function qsa(...)` dans une évaluation ne garantit rien d'une
        évaluation à l'autre ; `window.qsa` dit explicitement la portée."""
        for debut, lignes in _etapes_qui_appellent_qsa(chemin):
            depots = [ligne for ligne in lignes if DEFINITION in ligne]
            assert depots, f"ligne {debut} : aucun dépôt"
            assert any("=" in depot for depot in depots), (
                f"ligne {debut} : l'aide est mentionnée mais pas affectée à window.qsa"
            )
