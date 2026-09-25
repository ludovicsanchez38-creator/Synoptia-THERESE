"""B-1277 : l'écran n'a plus de délai pour la purge (B-1250) et le serveur
n'en avait aucun sur ses attentes de fond (créations du chat, fiche en vol,
profil). Un vecteur n'est pas borné (modèle chargé, voire téléchargé, au
premier appel) : l'écran pouvait tourner sans fin. Au-delà du plafond, la
route répond 503 sans rien supprimer. Revue du diff, passe 5."""

import asyncio
from pathlib import Path

import pytest

PASSE = "Passphrase-Test-123"


def _travaux_interminables(monkeypatch):
    from app.routers import data as data_router
    from app.routers import memory as memoire

    async def interminable():
        await asyncio.sleep(5)

    monkeypatch.setattr(data_router, "DELAI_MAX_TRAVAUX_DE_FOND_S", 0.3)
    monkeypatch.setattr(memoire, "arreter_les_indexations_de_fiches", interminable)


@pytest.mark.asyncio
async def test_la_purge_repond_503_sans_rien_supprimer(client, monkeypatch):
    cree = await client.post("/api/memory/contacts", json={"first_name": "Alice", "last_name": "Martin"})
    assert cree.status_code == 200, cree.text
    _travaux_interminables(monkeypatch)
    r = await client.delete("/api/data/all?confirm=true")
    assert r.status_code == 503, r.text
    assert "rien n'a été modifié" in r.text, r.text
    assert len((await client.get("/api/memory/contacts")).json()) == 1


@pytest.mark.asyncio
async def test_la_restauration_repond_503_et_rend_la_main(client, monkeypatch):
    from app.config import settings
    from app.services.maintenance import maintenance_mode

    data_dir = Path(settings.data_dir)
    (data_dir / "THERESE.md").write_text("consignes", encoding="utf-8")
    resp = await client.post("/api/data/backup", json={"password": PASSE})
    assert resp.status_code == 200, resp.text
    nom = resp.json()["backup_name"]
    _travaux_interminables(monkeypatch)
    r = await client.post(f"/api/data/restore/{nom}?confirm=true", json={"password": PASSE})
    assert r.status_code == 503, r.text
    assert maintenance_mode.active is False
    assert not list(data_dir.rglob(f".{nom}.restore.tar.gz"))
