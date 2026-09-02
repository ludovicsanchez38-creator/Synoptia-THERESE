"""B-043 : un balayage à vide conclut « aucune violation ».

Plusieurs gardes de sécurité de `test_regression.py` parcouraient un
répertoire et n'affirmaient rien sur ce qu'elles avaient lu. Un glob qui ne
rend rien - répertoire renommé, déplacé, exclu du build, chemin relatif lancé
depuis un autre dossier - laisse `violations == []` et le test passe SANS
avoir ouvert un seul fichier : il ne distingue plus « aucune faute » de
« aucune donnée ». Une seule des gardes portait ce témoin, avec le commentaire
qui nommait le trou.

Ce fichier ferme la porte pour toutes les autres, et pour celles à venir : une
fonction qui balaie un répertoire doit compter ce qu'elle a lu.

Il vit à part de `test_regression.py` parce qu'il le PREND POUR CIBLE, comme
`test_plafond_tests_textuels.py` : un gate qui mesure un fichier n'a pas sa
place dedans.
"""

import ast
from pathlib import Path

CIBLE = Path(__file__).resolve().parent / "test_regression.py"


def _balaye_un_repertoire(fonction: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    return any(
        isinstance(noeud, ast.Call)
        and isinstance(noeud.func, ast.Attribute)
        and noeud.func.attr in {"glob", "rglob"}
        for noeud in ast.walk(fonction)
    )


def _compte_ce_qu_elle_a_lu(fonction: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    """Une assertion de cardinalité, c'est-à-dire un `len(...)` sous un `assert`."""
    return any(
        isinstance(interne, ast.Call)
        and isinstance(interne.func, ast.Name)
        and interne.func.id == "len"
        for assertion in ast.walk(fonction)
        if isinstance(assertion, ast.Assert)
        for interne in ast.walk(assertion)
    )


def _fonctions_sans_temoin(source: str) -> list[str]:
    arbre = ast.parse(source)
    return [
        f"{noeud.name} (l.{noeud.lineno})"
        for noeud in ast.walk(arbre)
        if isinstance(noeud, ast.FunctionDef | ast.AsyncFunctionDef)
        and _balaye_un_repertoire(noeud)
        and not _compte_ce_qu_elle_a_lu(noeud)
    ]


def test_tout_balayage_de_repertoire_a_son_temoin():
    sans_temoin = _fonctions_sans_temoin(CIBLE.read_text(encoding="utf-8"))
    assert sans_temoin == [], (
        f"balayages sans témoin de cardinalité dans {CIBLE.name} : {sans_temoin}. "
        "Un glob vide y rendrait « aucune violation » sans avoir rien lu. "
        "Poser `assert len(fichiers) >= N` AVANT la boucle."
    )


def test_le_gate_voit_bien_un_balayage_sans_temoin():
    """L'instrument doit reconnaître le défaut qu'il prétend interdire."""
    sans = (
        "def test_rien_de_dangereux():\n"
        "    violations = []\n"
        '    for fichier in dossier.rglob("*.tsx"):\n'
        '        if "danger" in fichier.read_text():\n'
        "            violations.append(fichier.name)\n"
        "    assert violations == []\n"
    )
    assert _fonctions_sans_temoin(sans) != [], (
        "un balayage sans plancher de cardinalité doit être signalé"
    )

    avec = sans.replace(
        '    for fichier in dossier.rglob("*.tsx"):\n',
        '    fichiers = sorted(dossier.rglob("*.tsx"))\n'
        "    assert len(fichiers) >= 10\n"
        "    for fichier in fichiers:\n",
    )
    assert _fonctions_sans_temoin(avec) == [], (
        "un balayage qui compte ce qu'il a lu n'est pas une faute"
    )
