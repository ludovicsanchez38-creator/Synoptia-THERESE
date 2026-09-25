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


@pytest.mark.asyncio
async def test_le_fil_du_vecteur_en_vol_n_ecrit_pas_apres_la_purge(client, monkeypatch):
    """B-1234 : le vecteur est calculé et écrit dans un FIL (asyncio.to_thread) ;
    annuler la tâche ne l'arrête pas, et il écrivait dans la collection
    recréée après la réponse 200 de la purge. Ici l'écriture se fait dans le
    fil, comme dans le moteur (qdrant.py add_memory)."""
    import app.services.qdrant as mq

    journal: list[tuple[str, float]] = []

    def ecrire_dans_le_fil(entity_id):
        time.sleep(0.8)
        journal.append((entity_id, time.monotonic()))

    async def ajout(**kw):
        await asyncio.to_thread(ecrire_dans_le_fil, kw.get("entity_id"))
        return "p"

    async def suppr(entity_id):
        return 0

    monkeypatch.setattr(mq._qdrant_service, "async_add_memory", ajout)
    monkeypatch.setattr(mq._qdrant_service, "async_delete_by_entity", suppr)
    resp = await client.post("/api/memory/contacts/import", files={"file": ("c.vcf", _carnet(3), "text/vcard")})
    assert resp.status_code == 200, resp.text
    time.sleep(0.3)  # un vecteur est en vol dans son fil
    r = await client.delete("/api/data/all?confirm=true")
    assert r.status_code == 200, r.text
    fin_de_la_purge = time.monotonic()
    time.sleep(2.5)
    apres = [e for e in journal if e[1] > fin_de_la_purge]
    assert not apres, f"{len(apres)} écriture(s) de fil après la réponse de la purge"


@pytest.mark.asyncio
async def test_une_fiche_en_erreur_n_arrete_pas_les_suivantes(db_session, monkeypatch):
    """B-1239 : une erreur sur une fiche (lecture en base, calcul du vecteur)
    faisait mourir la tâche en silence ; les fiches suivantes n'étaient
    jamais indexées."""
    from app.models.entities import Contact
    from app.routers import memory as memoire

    premiere, seconde = Contact(first_name="Alice"), Contact(first_name="Bruno")
    db_session.add(premiere)
    db_session.add(seconde)
    await db_session.commit()
    vues: list[str] = []

    async def embed(fiche):
        if fiche.first_name == "Alice":
            raise RuntimeError("panne du modèle d'embedding")
        vues.append(fiche.first_name)

    monkeypatch.setattr(memoire, "_embed_contact", embed)
    memoire.indexer_fiches_en_arriere_plan([premiere, seconde])
    await asyncio.gather(*list(memoire._INDEXATIONS_DE_FICHES), return_exceptions=True)
    assert vues == ["Bruno"], vues
