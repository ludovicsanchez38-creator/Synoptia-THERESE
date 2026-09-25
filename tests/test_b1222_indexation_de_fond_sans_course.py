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


def _lecture_en_panne(monkeypatch, en_panne):
    """B-1258 : `_embed_contact` avale ses erreurs ; ce qui peut lever, c'est
    la lecture de la fiche en base. On fait donc tomber celle-ci."""
    import contextlib

    import app.models.database as base

    vraie = base.get_session_context

    @contextlib.asynccontextmanager
    async def lecture():
        async with vraie() as session:
            ordinaire = session.get

            async def get(modele, identifiant, *a, **kw):
                if identifiant in en_panne:
                    raise RuntimeError("base verrouillée")
                return await ordinaire(modele, identifiant, *a, **kw)

            session.get = get
            yield session

    monkeypatch.setattr(base, "get_session_context", lecture)


@pytest.mark.asyncio
async def test_une_fiche_en_erreur_n_arrete_pas_les_suivantes(db_session, monkeypatch):
    """B-1239 : une erreur sur une fiche (lecture en base) faisait mourir la
    tâche en silence ; les fiches suivantes n'étaient jamais indexées."""
    from app.models.entities import Contact
    from app.routers import memory as memoire

    premiere, seconde = Contact(first_name="Alice"), Contact(first_name="Bruno")
    db_session.add(premiere)
    db_session.add(seconde)
    await db_session.commit()
    vues: list[str] = []

    async def embed(fiche):
        vues.append(fiche.first_name)

    monkeypatch.setattr(memoire, "_embed_contact", embed)
    _lecture_en_panne(monkeypatch, {premiere.id})
    memoire.indexer_fiches_en_arriere_plan([premiere, seconde])
    await asyncio.gather(*list(memoire._INDEXATIONS_DE_FICHES), return_exceptions=True)
    assert vues == ["Bruno"], vues


@pytest.mark.asyncio
async def test_une_panne_persistante_ne_journalise_qu_une_trace(db_session, monkeypatch, caplog):
    """B-1258 : une base en panne produisait une trace complète par fiche
    restante ; une seule trace, puis un décompte."""
    import logging

    from app.models.entities import Contact
    from app.routers import memory as memoire

    fiches = [Contact(first_name=f"Fiche {i}") for i in range(3)]
    for fiche in fiches:
        db_session.add(fiche)
    await db_session.commit()

    async def embed(fiche):
        return None

    monkeypatch.setattr(memoire, "_embed_contact", embed)
    _lecture_en_panne(monkeypatch, {f.id for f in fiches})
    with caplog.at_level(logging.WARNING, logger=memoire.logger.name):
        memoire.indexer_fiches_en_arriere_plan(fiches)
        await asyncio.gather(*list(memoire._INDEXATIONS_DE_FICHES), return_exceptions=True)
    traces = [r for r in caplog.records if r.exc_info]
    assert len(traces) == 1, [r.getMessage() for r in caplog.records]
    assert any("3" in r.getMessage() for r in caplog.records if not r.exc_info), [r.getMessage() for r in caplog.records]


@pytest.mark.asyncio
async def test_une_interruption_pendant_l_attente_ne_laisse_pas_une_purge_a_moitie_faite(client, monkeypatch):
    """B-1249 : l'attente de la fiche en vol (B-1234, jusqu'à 19 s) venait
    APRÈS le commit des suppressions ; une interruption à ce moment laissait
    des tables vides mais l'index vectoriel et les fichiers en place. Elle
    vient désormais avant toute suppression."""
    from app.routers import memory as memoire

    cree = await client.post("/api/memory/contacts", json={"first_name": "Alice", "last_name": "Martin"})
    assert cree.status_code == 200, cree.text

    async def interrompu():
        raise OSError("interruption simulée pendant l'attente")

    monkeypatch.setattr(memoire, "arreter_les_indexations_de_fiches", interrompu)
    await client.delete("/api/data/all?confirm=true")

    restants = (await client.get("/api/memory/contacts")).json()
    assert len(restants) == 1, "la purge a supprimé les fiches avant l'attente interrompue"


@pytest.mark.asyncio
async def test_la_purge_n_attend_que_la_fiche_en_vol(client, monkeypatch):
    """B-1255 : rien ne prouvait l'arrêt ENTRE deux fiches (B-1234). Depuis
    B-1249, l'attente précède les suppressions : sans la demande d'arrêt, la
    purge attendait l'indexation du carnet entier, un vecteur par fiche."""
    import app.services.qdrant as mq

    def ecrire_dans_le_fil(entity_id):
        time.sleep(1.0)

    async def ajout(**kw):
        await asyncio.to_thread(ecrire_dans_le_fil, kw.get("entity_id"))
        return "p"

    async def suppr(entity_id):
        return 0

    monkeypatch.setattr(mq._qdrant_service, "async_add_memory", ajout)
    monkeypatch.setattr(mq._qdrant_service, "async_delete_by_entity", suppr)
    resp = await client.post("/api/memory/contacts/import", files={"file": ("c.vcf", _carnet(6), "text/vcard")})
    assert resp.status_code == 200, resp.text
    time.sleep(0.3)  # la première fiche est en vol dans son fil
    debut = time.monotonic()
    r = await client.delete("/api/data/all?confirm=true")
    duree = time.monotonic() - debut
    assert r.status_code == 200, r.text
    assert duree < 3.5, f"la purge a attendu {duree:.1f} s : le carnet entier, pas la seule fiche en vol"
