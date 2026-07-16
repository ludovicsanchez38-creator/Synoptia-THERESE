"""US-014 : chiffrement de la base au repos (SQLCipher).

Critère du plan : « DB hors app sans clé -> illisible ».
La clé est dérivée de la clé maîtresse du trousseau (HKDF) ; en test, elle
est fixée par THERESE_DB_KEY (conftest) pour rester indépendante du Keychain.
"""
import sqlite3

import pytest
from app.config import settings
from app.models.database import (
    db_connect,
    db_is_encrypted,
    ensure_db_encrypted,
)


def _make_plain_db(path, rows: int = 3) -> None:
    with sqlite3.connect(str(path)) as conn:
        conn.execute("CREATE TABLE contacts (id INTEGER PRIMARY KEY, name TEXT)")
        for i in range(rows):
            conn.execute("INSERT INTO contacts (name) VALUES (?)", (f"Contact {i}",))
        conn.commit()


class TestDetection:
    def test_db_claire_detectee(self, tmp_path):
        db = tmp_path / "plain.db"
        _make_plain_db(db)
        assert db_is_encrypted(db) is False

    def test_db_absente_non_chiffree(self, tmp_path):
        assert db_is_encrypted(tmp_path / "absent.db") is False


class TestMigration:
    def test_migration_claire_vers_chiffree_sans_perte(self, tmp_path):
        db = tmp_path / "therese.db"
        _make_plain_db(db, rows=5)

        ensure_db_encrypted(db)

        # 1. Le fichier n'a plus l'en-tête SQLite : illisible hors app
        assert db_is_encrypted(db) is True
        with pytest.raises(sqlite3.DatabaseError), sqlite3.connect(str(db)) as raw:
            raw.execute("SELECT * FROM sqlite_master").fetchall()

        # 2. Les données sont intactes via db_connect (clé posée)
        with db_connect(db) as conn:
            count = conn.execute("SELECT COUNT(*) FROM contacts").fetchone()[0]
        assert count == 5

    def test_migration_idempotente(self, tmp_path):
        db = tmp_path / "therese.db"
        _make_plain_db(db)
        ensure_db_encrypted(db)
        ensure_db_encrypted(db)  # deuxième passage : no-op
        with db_connect(db) as conn:
            assert conn.execute("SELECT COUNT(*) FROM contacts").fetchone()[0] == 3

    def test_migration_couvre_le_wal_non_checkpointe(self, tmp_path):
        """Revue adversariale : des transactions encore dans le -wal (pas
        checkpointées) doivent survivre à la migration vers le chiffré."""
        db = tmp_path / "therese.db"
        conn = sqlite3.connect(str(db))
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("CREATE TABLE contacts (id INTEGER PRIMARY KEY, name TEXT)")
        conn.commit()
        conn.execute("INSERT INTO contacts (name) VALUES ('Dans le WAL')")
        conn.commit()  # commit WAL : la donnée vit dans therese.db-wal
        assert (tmp_path / "therese.db-wal").exists(), "précondition : WAL présent"

        ensure_db_encrypted(db)
        conn.close()

        assert db_is_encrypted(db) is True
        with db_connect(db) as enc:
            rows = enc.execute("SELECT name FROM contacts").fetchall()
        assert rows == [("Dans le WAL",)]
        # plus de WAL clair résiduel
        assert not (tmp_path / "therese.db-wal").exists()

    def test_pas_de_copie_claire_residuelle(self, tmp_path):
        """Garder une copie claire annulerait le chiffrement au repos."""
        db = tmp_path / "therese.db"
        _make_plain_db(db)
        ensure_db_encrypted(db)
        residuals = [
            p for p in tmp_path.iterdir()
            if p.name != "therese.db" and p.suffix != ""
        ]
        assert residuals == [], f"fichiers résiduels : {residuals}"


class TestRuntime:
    @pytest.mark.asyncio
    async def test_la_db_de_l_app_est_chiffree(self, client):
        """La DB créée/utilisée par l'app (fixtures init_db) est chiffrée :
        le critère d'audit « DB hors app sans clé -> illisible » tient."""
        resp = await client.get("/health")
        assert resp.status_code == 200

        db_path = settings.db_path
        assert db_is_encrypted(db_path) is True, (
            "therese.db doit être chiffrée au repos (US-014)"
        )
        # mode=ro : ne pas polluer la base VIVANTE avec un journal parasite
        with (
            pytest.raises(sqlite3.DatabaseError),
            sqlite3.connect(f"file:{db_path}?mode=ro", uri=True) as raw,
        ):
            raw.execute("SELECT * FROM sqlite_master").fetchall()

    @pytest.mark.asyncio
    async def test_backup_contient_la_db_chiffree(self, client):
        """US-011 x US-014 x US-003 : l'archive de backup est chiffrée par
        passphrase ET embarque la DB déjà chiffrée + la clé (restaurable sur une
        autre machine AVEC la passphrase, totalement illisible sans)."""
        import tarfile
        from pathlib import Path

        from app.services.encryption import (
            decrypt_backup_archive,
            get_encryption_service,
        )

        pwd = "Passphrase-Test-123"
        get_encryption_service().encrypt("probe")  # force la création de la clé

        resp = await client.post("/api/data/backup", json={"password": pwd})
        assert resp.status_code == 200
        enc_path = resp.json()["path"]
        assert enc_path.endswith(".tar.gz.enc"), enc_path
        assert resp.json()["encrypted"] is True

        # L'archive est un blob chiffré : illisible tel quel comme tar.
        with pytest.raises(tarfile.ReadError):
            tarfile.open(enc_path, "r:gz")  # noqa: SIM115 (on vérifie qu'il lève)

        # Déchiffrée avec la passphrase : DB déjà chiffrée + clé autosuffisante.
        plain = Path(enc_path + ".dec")
        decrypt_backup_archive(enc_path, plain, pwd)
        try:
            with tarfile.open(plain, "r:gz") as tar:
                header = tar.extractfile("therese.db").read(16)
                names = tar.getnames()
            assert header != b"SQLite format 3\x00", "DB en CLAIR dans le backup"
            assert ".encryption_key" in names, names
        finally:
            plain.unlink(missing_ok=True)
