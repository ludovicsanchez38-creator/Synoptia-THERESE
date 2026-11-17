"""Courses de publication et reprises avec SQL et Qdrant locaux jetables."""

import asyncio
import threading
from contextlib import asynccontextmanager

import pytest
from app.config import settings
from app.models import database
from app.models.entities import Contact, FileMetadata, Project
from app.models.schemas import ContactUpdate, ProjectUpdate, RGPDAnonymizeRequest
from app.routers import files, memory, rgpd
from app.services import project_sync_service as sync

from tests.test_c20_diff2_relecture_passe2 import index_local as _index_local
from tests.test_c20_diff2_relecture_passe2 import lire, point

index_local = _index_local


@pytest.fixture(autouse=True)
def verrous_isoles(monkeypatch):
    monkeypatch.setattr(sync, "_verrous_projet", {})
    monkeypatch.setattr(sync, "_verrous_restitutions", {})
    monkeypatch.setattr(sync, "_journaux_actifs", set())


async def _restitution_en_panne(session, index, monkeypatch, tmp_path):
    session.add(Project(id="dossier", name="Dossier"))
    for identifiant in ("fichier", "voisin"):
        session.add(FileMetadata(
            id=identifiant, path=str(tmp_path / f"{identifiant}.txt"), name=identifiant,
            extension=".txt", size=5, scope="project", scope_id="dossier",
        ))
    await session.commit()
    index.client.upsert(settings.qdrant_collection, points=[point(1, "fichier"), point(2, "voisin")])
    restaurer = index.async_restituer_fragments

    async def indisponible(_points):
        raise RuntimeError("Index temporairement indisponible")

    monkeypatch.setattr(index, "async_restituer_fragments", indisponible)
    await memory._nettoyer_et_supprimer_projet(session, await session.get(Project, "dossier"))
    await session.rollback()
    return restaurer


@pytest.mark.asyncio
async def test_restitution_visible_et_reessayable_sans_redemarrage(
    db_session, index_local, monkeypatch, tmp_path,
):
    from app.main import app
    from httpx import ASGITransport, AsyncClient

    restaurer = await _restitution_en_panne(db_session, index_local, monkeypatch, tmp_path)
    try:
        async with AsyncClient(transport=ASGITransport(app), base_url="http://test") as client:
            etat = await client.get("/api/projects/dossier/sync")
            assert etat.json().get("restitution_en_attente") is True, "la restitution en attente est invisible"
            tentative = await client.post("/api/projects/dossier/sync/reprendre-index")
            assert tentative.status_code == 200
            assert tentative.json()["restitution_en_attente"] is True
            assert sync._verrou("dossier").locked()
            monkeypatch.setattr(index_local, "async_restituer_fragments", restaurer)
            reprise = await client.post("/api/projects/dossier/sync/reprendre-index")
            assert reprise.status_code == 200
            assert reprise.json()["restitution_en_attente"] is False
            assert [p.id for p in lire(index_local)] == [1, 2]
            assert not sync._verrou("dossier").locked()
    finally:
        monkeypatch.setattr(index_local, "async_restituer_fragments", restaurer)
        await sync.reprendre_restitutions_index(index_local)


@pytest.mark.asyncio
async def test_retrait_fichier_coordonne_avec_restitution(db_session, index_local, monkeypatch, tmp_path):
    from fastapi import HTTPException

    restaurer = await _restitution_en_panne(db_session, index_local, monkeypatch, tmp_path)
    try:
        async with database.AsyncSessionLocal() as session:
            with pytest.raises(HTTPException) as erreur:
                await files.delete_file("fichier", session)
        assert erreur.value.status_code == 409
        assert "restitution" in erreur.value.detail.lower()
    finally:
        monkeypatch.setattr(index_local, "async_restituer_fragments", restaurer)
        await sync.reprendre_restitutions_index(index_local)


@pytest.mark.asyncio
@pytest.mark.parametrize("changement", ["suppression", "perimetre", "version"])
async def test_reprise_revalide_chaque_entite_du_journal(
    db_session, index_local, monkeypatch, tmp_path, changement,
):
    from datetime import timedelta

    restaurer = await _restitution_en_panne(db_session, index_local, monkeypatch, tmp_path)
    # Simule un autre démarrage : ni copie ni verrou de l'ancienne session.
    db_session.info.clear()
    await db_session.close()
    monkeypatch.setattr(sync, "_verrous_projet", {})
    monkeypatch.setattr(sync, "_verrous_restitutions", {})
    async with database.AsyncSessionLocal() as session:
        fichier = await session.get(FileMetadata, "fichier")
        if changement == "suppression":
            await session.delete(fichier)
        elif changement == "perimetre":
            fichier.scope, fichier.scope_id = "global", None
        else:
            fichier.updated_at += timedelta(seconds=1)
        await session.commit()
    monkeypatch.setattr(index_local, "async_restituer_fragments", restaurer)
    await sync.reprendre_restitutions_index(index_local)
    assert [p.payload["entity_id"] for p in lire(index_local)] == ["voisin"], (
        "la reprise restitue une entité supprimée, reclassée ou remplacée"
    )
    assert not sync._verrou("dossier").locked()


@pytest.mark.asyncio
async def test_annuler_publication_attend_le_fil_avant_de_liberer_la_fiche(
    db_session, index_local, monkeypatch,
):
    db_session.add(Contact(id="fiche", first_name="Fictif"))
    await db_session.commit()
    entree = asyncio.Event()
    continuer, termine = threading.Event(), threading.Event()
    boucle = asyncio.get_running_loop()
    ajout = index_local.add_memory

    def ajout_retarde(*args, **kwargs):
        boucle.call_soon_threadsafe(entree.set)
        assert continuer.wait(5)
        try:
            return ajout(*args, **kwargs)
        finally:
            termine.set()

    monkeypatch.setattr(index_local, "add_memory", ajout_retarde)
    publication = asyncio.create_task(sync._publier_fiches_detachees({("contact", "fiche")}))
    suppression = None
    try:
        await asyncio.wait_for(entree.wait(), 5)
        publication.cancel()

        async def supprimer():
            async with database.AsyncSessionLocal() as session:
                await memory.delete_contact("fiche", False, session)

        suppression = asyncio.create_task(supprimer())
        await asyncio.wait({suppression}, timeout=0.1)
    finally:
        continuer.set()
        with pytest.raises(asyncio.CancelledError):
            await publication
        if suppression is not None:
            await suppression
        assert await asyncio.to_thread(termine.wait, 5)
    assert not lire(index_local), "le fil de publication annulé ressuscite la fiche supprimée"


@pytest.mark.asyncio
@pytest.mark.parametrize("modele", [Contact, Project], ids=["contact", "projet"])
@pytest.mark.parametrize("operation", ["reclasser", "supprimer", "supprimer_sql"])
async def test_republication_ne_depasse_pas_la_modification_de_la_fiche(
    db_session, index_local, monkeypatch, modele, operation,
):
    fiche = modele(id="fiche", **({"first_name": "Fictif"} if modele is Contact else {"name": "Fictif"}))
    db_session.add(fiche)
    db_session.add(Project(id="destination", name="Destination"))
    await db_session.commit()
    entree, continuer = asyncio.Event(), asyncio.Event()
    ajout = index_local.async_add_memory
    premier = True

    async def publication_retardee(**kwargs):
        nonlocal premier
        if premier:
            premier = False
            entree.set()
            await continuer.wait()
        return await ajout(**kwargs)

    monkeypatch.setattr(index_local, "async_add_memory", publication_retardee)
    type_fiche = "contact" if modele is Contact else "project"
    publication = asyncio.create_task(sync._publier_fiches_detachees({(type_fiche, "fiche")}))

    async def modifier():
        async with database.AsyncSessionLocal() as session:
            if operation == "supprimer_sql":
                from sqlalchemy import delete

                await session.execute(delete(modele).where(modele.id == "fiche"))
                await session.commit()
                await index_local.async_delete_by_entity("fiche")
            elif operation == "supprimer":
                supprimer = memory.delete_contact if modele is Contact else memory.delete_project
                await supprimer("fiche", False, session)
            elif modele is Contact:
                await memory.update_contact("fiche", ContactUpdate(scope="project", scope_id="destination"), session)
            else:
                await memory.update_project("fiche", ProjectUpdate(scope="project", scope_id="destination"), session)

    modification = None
    try:
        await asyncio.wait_for(entree.wait(), 5)
        modification = asyncio.create_task(modifier())
        await asyncio.wait({modification}, timeout=0.1)
    finally:
        continuer.set()
        await publication
        if modification is not None:
            await modification
    points = [p for p in lire(index_local) if p.payload["entity_id"] == "fiche"]
    if operation.startswith("supprimer"):
        assert not points, "la republication ressuscite une fiche supprimée"
    else:
        assert len(points) == 1
        assert points[0].payload["scope"] == "project", "la republication périmée rétablit le périmètre global"
        assert points[0].payload["scope_id"] == "destination"


@pytest.mark.asyncio
@pytest.mark.parametrize("modele", [Contact, Project], ids=["contact", "projet"])
async def test_indexation_refuse_une_version_de_fiche_perimee(db_session, index_local, modele):
    fiche = modele(id="fiche", **({"first_name": "Fictif"} if modele is Contact else {"name": "Fictif"}))
    db_session.add(fiche)
    await db_session.commit()
    ancienne = fiche.model_copy()
    fiche.scope, fiche.scope_id = "project", "destination"
    await db_session.commit()
    indexer = memory._embed_contact if modele is Contact else memory._embed_project
    await indexer(fiche)
    await indexer(ancienne)
    points = lire(index_local)
    assert len(points) == 1
    assert points[0].payload["scope"] == "project", "une version périmée remplace le vecteur courant"


@pytest.mark.asyncio
@pytest.mark.parametrize("panne", ["sql", "vecteur"])
async def test_republication_en_panne_ne_fait_pas_echouer_un_commit_durable(
    db_session, index_local, monkeypatch, tmp_path, panne,
):
    db_session.add(Contact(id="personne", first_name="Fictif"))
    db_session.add(Project(id="dossier", name="Dossier", contact_id="personne"))
    db_session.add(Contact(id="fiche", first_name="Voisin", scope="project", scope_id="dossier"))
    await db_session.commit()
    depot = tmp_path / "depots" / "dossier"
    depot.mkdir(parents=True)
    (depot / "temoin.txt").write_text("Donnée fictive")
    monkeypatch.setattr(memory, "racine_des_depots", lambda: depot.parent)
    index_local.client.upsert(settings.qdrant_collection, points=[
        point(1, "personne", "global", None), point(2, "fiche"),
    ])
    lecture = sync.get_session_context
    ajout = index_local.async_add_memory

    @asynccontextmanager
    async def lecture_en_panne():
        raise RuntimeError("Lecture SQL indisponible après commit")
        yield

    async def ajout_en_panne(**_kwargs):
        raise RuntimeError("Index indisponible après commit")

    monkeypatch.setattr(sync, "get_session_context", lecture_en_panne if panne == "sql" else lecture)
    monkeypatch.setattr(index_local, "async_add_memory", ajout_en_panne if panne == "vecteur" else ajout)
    erreur = None
    try:
        await rgpd.anonymize_contact("personne", RGPDAnonymizeRequest(reason="Demande fictive"), db_session)
    except Exception as exc:
        erreur = exc
    assert erreur is None, "la republication fait échouer un commit déjà durable"
    assert not depot.exists(), "la panne de republication empêche la purge du dépôt"
    assert not any(p.payload["entity_id"] == "personne" for p in lire(index_local))

    from app.models.entities_sync import IndexPublication
    from sqlmodel import select

    # Une nouvelle session atteste la durabilité, indépendamment de session.info.
    async with database.AsyncSessionLocal() as verification:
        assert await verification.get(Project, "dossier") is None
        travaux = (await verification.execute(select(IndexPublication))).scalars().all()
        assert len(travaux) == 1, "la republication en échec n’est pas conservée durablement"
    db_session.info.clear()
    monkeypatch.setattr(sync, "get_session_context", lecture)
    monkeypatch.setattr(index_local, "async_add_memory", ajout)
    await sync.reprendre_publications_index()
    assert [p.payload["entity_id"] for p in lire(index_local)] == ["fiche"]
    async with database.AsyncSessionLocal() as verification:
        assert not (await verification.execute(select(IndexPublication))).scalars().all()
