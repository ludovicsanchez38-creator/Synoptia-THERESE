"""B-1222 : régression de B-1204. L'indexation de fond travaillait sur l'instantané
des fiches importées et rien ne l'arrêtait : une fiche supprimée, ou une purge
« Effacer toutes mes données », voyait ses vecteurs (nom, courriel, société)
réécrits dans Qdrant APRÈS la réponse 200. Test de la revue adverse du diff."""
import asyncio
import time

import pytest


def _carnet(n: int) -> bytes:
    return b"".join(
        f"BEGIN:VCARD\r\nVERSION:3.0\r\nFN:Fiche {i}\r\nEMAIL:fiche{i}@example.fr\r\nEND:VCARD\r\n".encode()
        for i in range(n)
    )


def _espions(monkeypatch):
    import app.services.qdrant as mq

    journal: list[tuple[str, str, float]] = []

    async def lent(**kw):
        await asyncio.sleep(0.8)
        journal.append(("add", kw.get("entity_id"), time.monotonic()))
        return "p"

    async def suppr(entity_id):
        journal.append(("del", entity_id, time.monotonic()))
        return 0

    monkeypatch.setattr(mq._qdrant_service, "async_add_memory", lent)
    monkeypatch.setattr(mq._qdrant_service, "async_delete_by_entity", suppr)
    return journal


@pytest.mark.asyncio
async def test_fiche_supprimee_pendant_l_indexation(client, monkeypatch):
    journal = _espions(monkeypatch)
    resp = await client.post("/api/memory/contacts/import", files={"file": ("c.vcf", _carnet(3), "text/vcard")})
    assert resp.status_code == 200, resp.text
    liste = (await client.get("/api/memory/contacts")).json()
    cible = next(c["id"] for c in liste if c.get("email") == "fiche2@example.fr")
    r = await client.delete(f"/api/memory/contacts/{cible}")
    assert r.status_code == 200, r.text
    t_suppression = time.monotonic()
    time.sleep(3.5)
    apres = [e for e in journal if e[0] == "add" and e[1] == cible and e[2] > t_suppression]
    assert not apres, f"vecteur réécrit après la suppression de la fiche : {apres}"


@pytest.mark.asyncio
async def test_purge_totale_pendant_l_indexation(client, monkeypatch):
    journal = _espions(monkeypatch)
    resp = await client.post("/api/memory/contacts/import", files={"file": ("c.vcf", _carnet(3), "text/vcard")})
    assert resp.status_code == 200, resp.text
    r = await client.delete("/api/data/all?confirm=true")
    assert r.status_code == 200, r.text
    t_purge = time.monotonic()
    time.sleep(3.5)
    apres = [e for e in journal if e[0] == "add" and e[2] > t_purge]

    assert not apres, f"{len(apres)} vecteur(s) de fiches effacées écrits après la purge"
