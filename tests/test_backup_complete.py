"""US-011 : le backup doit inclure tout (DB + Qdrant + images + mcp_servers.json),
pas seulement therese.db. Sinon un restore perd la mémoire vectorielle.
Test round-trip : backup -> effacement -> restore -> données revenues."""
import shutil
import tarfile
from pathlib import Path

import pytest
from app.config import settings
from app.routers import data as data_router


@pytest.mark.asyncio
async def test_backup_restore_round_trip_complet(client):
    data_dir = Path(settings.data_dir)

    # Données annexes (au-delà de therese.db)
    (data_dir / "qdrant").mkdir(parents=True, exist_ok=True)
    (data_dir / "qdrant" / "collection.bin").write_bytes(b"vecteurs-importants")
    (data_dir / "images").mkdir(parents=True, exist_ok=True)
    (data_dir / "images" / "img.png").write_bytes(b"image")
    (data_dir / "mcp_servers.json").write_text('{"servers": []}', encoding="utf-8")

    # Backup
    resp = await client.post("/api/data/backup", json={"password": "Passphrase-Test-123"})
    assert resp.status_code == 200
    name = resp.json()["backup_name"]

    # Simuler une perte des données annexes
    shutil.rmtree(data_dir / "qdrant")
    shutil.rmtree(data_dir / "images")
    (data_dir / "mcp_servers.json").unlink()

    # Restore
    resp = await client.post(
        f"/api/data/restore/{name}?confirm=true", json={"password": "Passphrase-Test-123"}
    )
    assert resp.status_code == 200

    # Les données annexes sont revenues à l'identique
    assert (data_dir / "qdrant" / "collection.bin").read_bytes() == b"vecteurs-importants"
    assert (data_dir / "images" / "img.png").exists()
    assert (data_dir / "mcp_servers.json").exists()


@pytest.mark.asyncio
async def test_backup_liste_les_elements_inclus(client):
    data_dir = Path(settings.data_dir)
    (data_dir / "mcp_servers.json").write_text("{}", encoding="utf-8")

    resp = await client.post("/api/data/backup", json={"password": "Passphrase-Test-123"})
    assert resp.status_code == 200
    body = resp.json()
    assert "therese.db" in body.get("included", [])
    assert "mcp_servers.json" in body.get("included", [])


@pytest.mark.asyncio
async def test_restore_supprime_les_orphelins(client):
    """Restore PROPRE : un fichier créé dans qdrant/ APRÈS le backup doit
    disparaître après restauration (sinon on mélange deux états de la mémoire
    vectorielle, ce qui corrompt l'index)."""
    data_dir = Path(settings.data_dir)
    (data_dir / "qdrant").mkdir(parents=True, exist_ok=True)
    (data_dir / "qdrant" / "ancien.bin").write_bytes(b"etat-1")

    resp = await client.post("/api/data/backup", json={"password": "Passphrase-Test-123"})
    assert resp.status_code == 200
    name = resp.json()["backup_name"]

    # Pollution APRÈS le backup : un orphelin qui n'est PAS dans l'archive
    (data_dir / "qdrant" / "orphelin.bin").write_bytes(b"cree-apres-backup")

    resp = await client.post(
        f"/api/data/restore/{name}?confirm=true", json={"password": "Passphrase-Test-123"}
    )
    assert resp.status_code == 200

    # L'état du backup est revenu, l'orphelin a disparu
    assert (data_dir / "qdrant" / "ancien.bin").read_bytes() == b"etat-1"
    assert not (data_dir / "qdrant" / "orphelin.bin").exists()


class _CheckpointConnection:
    def __init__(self, rows):
        self.rows = list(rows)
        self.calls = 0

    def execute(self, _statement):
        self.calls += 1
        return self

    def fetchone(self):
        return self.rows.pop(0)

    def close(self):
        return None


def test_checkpoint_reessaie_quand_sqlite_est_occupe(tmp_path, monkeypatch):
    db_path = tmp_path / "therese.db"
    db_path.write_bytes(b"SQLite format 3\x00")
    connection = _CheckpointConnection([(1, 4, 2), (1, 4, 4), (0, 0, 0)])

    monkeypatch.setattr(settings, "db_path", db_path)
    monkeypatch.setattr("app.models.database.db_connect", lambda _path: connection)
    monkeypatch.setattr("time.sleep", lambda _delay: None)

    assert data_router._checkpoint_db() is True
    assert connection.calls == 3


def test_archive_inclut_wal_et_shm_apres_checkpoint_occupe(tmp_path, monkeypatch):
    db_path = tmp_path / "therese.db"
    db_path.write_bytes(b"base")
    Path(f"{db_path}-wal").write_bytes(b"wal")
    Path(f"{db_path}-shm").write_bytes(b"shm")
    archive_path = tmp_path / "backup.tar.gz"

    monkeypatch.setattr(settings, "data_dir", tmp_path)
    monkeypatch.setattr(settings, "db_path", db_path)
    monkeypatch.setattr(settings, "qdrant_path", tmp_path / "qdrant")
    monkeypatch.setattr(data_router, "_checkpoint_db", lambda: False)

    included = data_router._create_archive(archive_path)

    assert {"therese.db", "therese.db-wal", "therese.db-shm"} <= set(included)
    with tarfile.open(archive_path, "r:gz") as archive:
        assert {"therese.db", "therese.db-wal", "therese.db-shm"} <= set(
            archive.getnames()
        )


def test_archive_echoue_si_le_fallback_wal_est_incomplet(tmp_path, monkeypatch):
    db_path = tmp_path / "therese.db"
    db_path.write_bytes(b"base")
    Path(f"{db_path}-wal").write_bytes(b"wal")
    archive_path = tmp_path / "backup.tar.gz"

    monkeypatch.setattr(settings, "data_dir", tmp_path)
    monkeypatch.setattr(settings, "db_path", db_path)
    monkeypatch.setattr(settings, "qdrant_path", tmp_path / "qdrant")
    monkeypatch.setattr(data_router, "_checkpoint_db", lambda: False)

    with pytest.raises(RuntimeError, match="sidecars impossible"):
        data_router._create_archive(archive_path)

    assert not archive_path.exists()


@pytest.mark.asyncio
async def test_restore_ferme_les_engines_avant_extraction(tmp_path, monkeypatch):
    backup_dir = tmp_path / "backups"
    backup_dir.mkdir()
    db_path = tmp_path / "therese.db"
    db_path.write_bytes(b"etat-courant")
    archive_path = backup_dir / "test_restore.tar.gz"
    restored_db = tmp_path / "restored.db"
    restored_db.write_bytes(b"etat-restaure")
    with tarfile.open(archive_path, "w:gz") as archive:
        archive.add(restored_db, arcname="therese.db")

    events = []
    original_extract = data_router._safe_extractall

    async def close_db_before_restore():
        events.append("close_db")

    def checked_extract(archive, destination):
        assert events == ["close_db"]
        events.append("extract")
        original_extract(archive, destination)

    monkeypatch.setattr(settings, "data_dir", tmp_path)
    monkeypatch.setattr(settings, "db_path", db_path)
    monkeypatch.setattr(settings, "qdrant_path", tmp_path / "qdrant")
    monkeypatch.setattr(data_router, "_backups_dir", lambda: backup_dir)
    monkeypatch.setattr(data_router, "close_db", close_db_before_restore)
    monkeypatch.setattr(data_router, "_checkpoint_db", lambda: True)
    monkeypatch.setattr(data_router, "_safe_extractall", checked_extract)
    monkeypatch.setattr(data_router, "_verify_restored_db", lambda: None)

    result = await data_router.restore_backup("test_restore", confirm=True)

    assert result["success"] is True
    assert events[:2] == ["close_db", "extract"]
    assert db_path.read_bytes() == b"etat-restaure"
