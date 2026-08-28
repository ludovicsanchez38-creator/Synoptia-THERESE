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

from pathlib import Path

RACINE = Path(__file__).parent


class TestAucuneConnexionSqliteNeFuit:
    def test_aucun_with_connect_sans_closing(self):
        fautes = []
        for fichier in sorted(RACINE.rglob("test_*.py")):
            if fichier.name == Path(__file__).name:
                continue
            for numero, ligne in enumerate(
                fichier.read_text(encoding="utf-8").splitlines(), 1
            ):
                nu = ligne.strip()
                if nu.startswith("#"):
                    continue
                ouvre = "sqlite3.connect(" in nu or "sqlcipher3.connect(" in nu
                if ouvre and nu.startswith("with ") and "closing(" not in nu:
                    fautes.append(f"{fichier.name}:{numero}")
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
