"""US-011 : le backup doit inclure tout (DB + Qdrant + images + mcp_servers.json),
pas seulement therese.db. Sinon un restore perd la mémoire vectorielle.
Test round-trip : backup -> effacement -> restore -> données revenues."""
import shutil
from pathlib import Path

import pytest
from app.config import settings


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
    resp = await client.post("/api/data/backup")
    assert resp.status_code == 200
    name = resp.json()["backup_name"]

    # Simuler une perte des données annexes
    shutil.rmtree(data_dir / "qdrant")
    shutil.rmtree(data_dir / "images")
    (data_dir / "mcp_servers.json").unlink()

    # Restore
    resp = await client.post(f"/api/data/restore/{name}?confirm=true")
    assert resp.status_code == 200

    # Les données annexes sont revenues à l'identique
    assert (data_dir / "qdrant" / "collection.bin").read_bytes() == b"vecteurs-importants"
    assert (data_dir / "images" / "img.png").exists()
    assert (data_dir / "mcp_servers.json").exists()


@pytest.mark.asyncio
async def test_backup_liste_les_elements_inclus(client):
    data_dir = Path(settings.data_dir)
    (data_dir / "mcp_servers.json").write_text("{}", encoding="utf-8")

    resp = await client.post("/api/data/backup")
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

    resp = await client.post("/api/data/backup")
    assert resp.status_code == 200
    name = resp.json()["backup_name"]

    # Pollution APRÈS le backup : un orphelin qui n'est PAS dans l'archive
    (data_dir / "qdrant" / "orphelin.bin").write_bytes(b"cree-apres-backup")

    resp = await client.post(f"/api/data/restore/{name}?confirm=true")
    assert resp.status_code == 200

    # L'état du backup est revenu, l'orphelin a disparu
    assert (data_dir / "qdrant" / "ancien.bin").read_bytes() == b"etat-1"
    assert not (data_dir / "qdrant" / "orphelin.bin").exists()
