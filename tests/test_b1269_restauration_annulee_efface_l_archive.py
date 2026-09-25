"""B-1269 : une restauration annulée PENDANT begin() (une requête suivie est en
vol, begin() attend sa fin) rendait bien le verrou (B-1263), mais laissait sur
le disque l'archive déchiffrée en clair, qui contient la clé de chiffrement
(US-003). Le finally qui l'efface n'englobait pas begin(). Revue du diff,
passe 5 (cas A)."""

import asyncio
from pathlib import Path

import pytest

PASSE = "Passphrase-Test-123"


@pytest.mark.asyncio
async def test_annulation_pendant_begin(client):
    from app.config import settings
    from app.routers import data as data_router
    from app.services.maintenance import maintenance_mode

    data_dir = Path(settings.data_dir)
    (data_dir / "THERESE.md").write_text("consignes", encoding="utf-8")
    resp = await client.post("/api/data/backup", json={"password": PASSE})
    assert resp.status_code == 200, resp.text
    nom = resp.json()["backup_name"]

    maintenance_mode._active_requests += 1
    try:
        tache = asyncio.create_task(data_router.restore_backup(nom, confirm=True, password=PASSE))
        for _ in range(300):
            await asyncio.sleep(0.01)
            if maintenance_mode.active:
                break
        assert maintenance_mode.active, "begin() n'a pas été atteint : le test ne mesure rien"
        assert list(data_dir.rglob(f".{nom}.restore.tar.gz")), "archive déchiffrée absente pendant begin()"
        tache.cancel()
        with pytest.raises(asyncio.CancelledError):
            await tache
        assert maintenance_mode.active is False
        assert not list(data_dir.rglob(f".{nom}.restore.tar.gz")), "archive déchiffrée laissée en clair"
    finally:
        maintenance_mode._active_requests = max(0, maintenance_mode._active_requests - 1)
        maintenance_mode._active = False
