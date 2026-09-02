"""B-039 : plafond anti-croissance des tests qui lisent le CODE, pas son effet.

`tests/test_regression.py` fait 8409 lignes et 584 tests, dont 467 ouvrent un
fichier source par `read_text()` pour y chercher une chaîne. Un tel test est
aveugle à un reformatage, à un renommage, à un déplacement de code ; une chaîne
posée en COMMENTAIRE suffit à le satisfaire. C'est le défaut que B-013 a montré
en grandeur nature : le garde anti-fuite de secrets restait vert alors qu'un
code fuyant réellement les arguments d'outils passait ses deux assertions.

Convertir 467 lectures de source en tests de comportement est un CHANTIER, pas
un correctif : chacune demande un harnais propre au domaine qu'elle prétend
couvrir. Ce fichier ne le fait donc pas. Il pose seulement la digue : le compte
ne monte plus. Un nouveau test de régression s'écrit contre le comportement.

Quand une conversion fait baisser le compte, baisser le plafond dans la foulée
- un plafond qu'on ne descend jamais finit par ne plus rien retenir.
"""
from pathlib import Path

# Mesuré le 02/09/2026 sur tests/test_regression.py. À BAISSER, jamais à monter.
PLAFOND_LECTURES_DE_SOURCE = 467

_CIBLE = Path(__file__).resolve().parent / "test_regression.py"


def _lectures_de_source(chemin: Path) -> int:
    return chemin.read_text(encoding="utf-8").count(".read_text(")


def test_le_nombre_de_tests_qui_lisent_le_code_ne_monte_plus():
    compte = _lectures_de_source(_CIBLE)

    assert compte <= PLAFOND_LECTURES_DE_SOURCE, (
        f"{_CIBLE.name} contient {compte} lectures de source "
        f"(plafond {PLAFOND_LECTURES_DE_SOURCE}). Un test qui cherche une "
        "chaîne dans un fichier source ne prouve rien sur le comportement : "
        "un reformatage le rend aveugle sans le faire rougir, et une chaîne en "
        "commentaire le satisfait. Écrire le nouveau test contre l'effet, pas "
        "contre le texte."
    )


def test_le_plafond_reste_collant():
    """Un plafond très au-dessus du réel ne retient rien."""
    compte = _lectures_de_source(_CIBLE)

    assert PLAFOND_LECTURES_DE_SOURCE - compte <= 10, (
        f"le plafond ({PLAFOND_LECTURES_DE_SOURCE}) a pris {PLAFOND_LECTURES_DE_SOURCE - compte} "
        f"de mou sur le réel ({compte}) : le descendre à {compte}"
    )
