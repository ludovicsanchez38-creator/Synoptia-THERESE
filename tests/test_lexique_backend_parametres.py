"""B-580 (05/09/2026) : le lexique 0.48 nomme l'onglet « Paramètres ».

Le frontend a été aligné (B-366) ; cinq messages du backend destinés à
l'écran disaient encore « Réglages ». Cette garde lit les sources, en
ignorant les commentaires, et refuse le mot dans une chaîne.
"""

import re
import tokenize
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1] / "src" / "backend" / "app"


def _chaines_avec_reglages() -> list[str]:
    fautes: list[str] = []
    for fichier in RACINE.rglob("*.py"):
        with fichier.open(mode="rb") as flux:
            for jeton in tokenize.tokenize(flux.readline):
                if jeton.type == tokenize.STRING and re.search(r"R[ée]glages", jeton.string):
                    fautes.append(f"{fichier.relative_to(RACINE)}:{jeton.start[0]}")
    return fautes


def test_aucune_chaine_du_backend_ne_dit_reglages():
    assert _chaines_avec_reglages() == []
