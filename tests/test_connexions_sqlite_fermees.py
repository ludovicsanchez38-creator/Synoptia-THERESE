"""
Une connexion SQLite ouverte dans un test doit être FERMÉE, pas seulement
sortie de sa transaction.

Six tests étaient rouges sur Windows depuis longtemps, tous sur la même
exception :

    os.replace(tmp, p)
    E  PermissionError: [WinError 5] Access is denied

Cause : `with sqlite3.connect(...)` gère la TRANSACTION, pas la connexion -
piège documenté de la bibliothèque standard. Le fichier reste donc ouvert.
Sur POSIX, renommer par-dessus un fichier ouvert fonctionne ; sur Windows,
non. Les aides de test laissaient un handle, et la migration vers SQLCipher
échouait au dernier geste.

Vérifié avant de conclure : le PRODUIT n'a pas ce défaut. `ensure_db_encrypted`
n'utilise que des `closing()`, `db_is_encrypted` un `with open(...)`, et
l'appel tourne AVANT la seule fuite du code applicatif
(`ensure_invoice_legacy_columns`). Ce sont donc bien les tests qui mentaient
sur une plateforme que personne ne regardait.

Ce gate empêche le motif de revenir. Il ne juge pas le code applicatif : là,
un `with` sur une connexion peut être délibéré si la connexion est réutilisée.
"""

import ast
from pathlib import Path

RACINE = Path(__file__).parent


def _fichiers_balayes() -> list[Path]:
    """Tous les fichiers Python de tests/, fixtures comprises.

    B-049 : `rglob("test_*.py")` laissait conftest.py hors du balayage, alors
    que c'est précisément là que vivent les fixtures de base.
    """
    return [
        fichier
        for fichier in sorted(RACINE.rglob("*.py"))
        if fichier.name != Path(__file__).name
    ]


def _ouvre_une_connexion(expr: ast.expr) -> bool:
    """`sqlite3.connect(...)` / `sqlcipher3.connect(...)` confié tel quel au `with`.

    Un `closing(...)` autour rend un appel à `closing`, pas à `connect` : la
    connexion est alors bien fermée, ce n'est pas une faute.
    """
    return (
        isinstance(expr, ast.Call)
        and isinstance(expr.func, ast.Attribute)
        and expr.func.attr == "connect"
        and isinstance(expr.func.value, ast.Name)
        and expr.func.value.id in {"sqlite3", "sqlcipher3"}
    )


def _connexions_non_fermees(source: str, nom: str) -> list[str]:
    """`with <sqlite>.connect(...)` non enveloppé dans `closing()`.

    B-049 : la règle tenait sur UNE ligne strippée commençant par `with `. Un
    `with (` étalé sur plusieurs lignes — la forme même que prend un `with`
    à deux gestionnaires — passait donc au travers. L'AST voit le `with`
    quelle que soit sa mise en page.
    """
    try:
        arbre = ast.parse(source)
    except SyntaxError:  # pragma: no cover - un fichier illisible se voit ailleurs
        return []
    fautes = []
    for noeud in ast.walk(arbre):
        if not isinstance(noeud, ast.With | ast.AsyncWith):
            continue
        for item in noeud.items:
            if _ouvre_une_connexion(item.context_expr):
                fautes.append(f"{nom}:{item.context_expr.lineno}")
    return sorted(fautes)


class TestAucuneConnexionSqliteNeFuit:
    def test_le_gate_balaie_aussi_les_fixtures(self):
        """conftest.py ouvre des bases : l'exclure, c'est ne pas les voir."""
        noms = {fichier.name for fichier in _fichiers_balayes()}
        assert "conftest.py" in noms, (
            "conftest.py est hors du balayage : les fixtures de base ne sont pas "
            f"surveillées ({len(noms)} fichiers vus)"
        )

    def test_le_gate_voit_un_with_multiligne(self):
        """Un `with (` étalé sur plusieurs lignes est le même piège.

        Le motif mono-ligne ne voyait que `with sqlite3.connect(...)` : dès que
        le `with` et l'appel étaient sur deux lignes, la fuite passait.
        """
        etale = (
            "import sqlite3\n"
            "def essai(db_path):\n"
            "    with (\n"
            "        pytest.raises(sqlite3.DatabaseError),\n"
            '        sqlite3.connect(f"file:{db_path}?mode=ro", uri=True) as raw,\n'
            "    ):\n"
            '        raw.execute("SELECT 1")\n'
        )
        assert _connexions_non_fermees(etale, "faux.py") != [], (
            "une connexion ouverte dans un `with (` multi-lignes échappe au gate"
        )

        enveloppe = etale.replace(
            '        sqlite3.connect(f"file:{db_path}?mode=ro", uri=True) as raw,\n',
            '        closing(sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)) as raw,\n',
        )
        assert _connexions_non_fermees(enveloppe, "faux.py") == [], (
            "`closing(...)` ferme bien la connexion : ce n'est pas une faute"
        )

    def test_aucun_with_connect_sans_closing(self):
        fautes = []
        for fichier in _fichiers_balayes():
            fautes += _connexions_non_fermees(
                fichier.read_text(encoding="utf-8"), fichier.name
            )
        assert fautes == [], (
            "`with sqlite3.connect(...)` ne ferme PAS la connexion (il gère la "
            "transaction). Le fichier reste ouvert, et sous Windows un "
            "os.replace par-dessus lève WinError 5. Utiliser "
            "`with closing(sqlite3.connect(...)) as conn:`. "
            f"Fautes : {fautes}"
        )

    def test_le_piege_est_reel(self):
        """Le gate ci-dessus ne vaut que si sa prémisse est vraie. On l'exécute."""
        import sqlite3
        import tempfile
        from contextlib import closing

        chemin = Path(tempfile.mkdtemp()) / "essai.db"

        with sqlite3.connect(str(chemin)) as fuite:
            fuite.execute("CREATE TABLE t (id INTEGER)")
        fuite.execute("SELECT 1")  # ne lève pas : la connexion vit encore

        with closing(sqlite3.connect(str(chemin))) as fermee:
            fermee.execute("SELECT 1")
        try:
            fermee.execute("SELECT 1")
            raise AssertionError("closing() aurait dû fermer la connexion")
        except sqlite3.ProgrammingError:
            pass

        fuite.close()
