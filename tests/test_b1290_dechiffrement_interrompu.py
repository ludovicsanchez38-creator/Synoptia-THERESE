"""B-1290 : `decrypt_backup_archive` écrit le clair par write_bytes ; seule une
ValueError (mauvaise passphrase) était rattrapée. Une OSError en pleine
écriture (disque plein) laissait un clair partiel sur le disque, contre
US-003. Revue du diff, passe 6 (constat 8)."""

import errno
from pathlib import Path

import pytest

PASSE = "Passphrase-Test-123"


@pytest.mark.asyncio
async def test_un_dechiffrement_interrompu_ne_laisse_pas_de_clair(client, monkeypatch):
    from app.config import settings
    from app.routers import data as data_router

    data_dir = Path(settings.data_dir)
    (data_dir / "THERESE.md").write_text("consignes", encoding="utf-8")
    resp = await client.post("/api/data/backup", json={"password": PASSE})
    assert resp.status_code == 200, resp.text
    nom = resp.json()["backup_name"]

    def disque_plein(source, destination, passe):
        Path(destination).write_bytes(b"clair partiel")
        raise OSError(errno.ENOSPC, "No space left on device")

    monkeypatch.setattr(data_router, "decrypt_backup_archive", disque_plein)
    try:
        await client.post(f"/api/data/restore/{nom}?confirm=true", json={"password": PASSE})
    except OSError:
        pass
    assert not list(data_dir.rglob(f".{nom}.restore.tar.gz")), "clair partiel laissé sur le disque"
