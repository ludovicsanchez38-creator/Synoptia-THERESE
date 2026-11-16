"""Cycle 20 diff-2 : régressions signalées par la relecture, passe 1."""

import asyncio
import hashlib
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from app.config import settings
from app.models import database
from app.models.entities import Contact, FileMetadata, Notification, Project
from app.models.entities_sync import EtatPlan, ProjectSyncEntry, ProjectSyncRoot, SyncPlan
from app.routers import memory
from app.services import project_sync_service as sync
from app.services import rgpd_auto
from app.services.qdrant import QdrantService
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams
from sqlalchemy.ext.asyncio import AsyncSession


async def _garnir_dossier(racine: Path, project_id: str, contact_id: str) -> None:
    racine.mkdir()
    fichier = racine / "note.txt"
    fichier.write_text("Contenu fictif à conserver.", encoding="utf-8")
    stat = fichier.stat()
    async with database.AsyncSessionLocal() as session:
        session.add(Project(id=project_id, name="Dossier fictif", contact_id=contact_id))
        session.add(ProjectSyncRoot(
            id=f"racine-{project_id}", project_id=project_id, racine=str(racine),
            volume_id=stat.st_dev,
        ))
        session.add(FileMetadata(
            id=f"fichier-{project_id}", path=str(fichier), name=fichier.name,
            extension=".txt", size=stat.st_size, chunk_count=1,
            scope="project", scope_id=project_id,
        ))
        session.add(ProjectSyncEntry(
            id=f"entree-{project_id}", project_id=project_id, chemin=str(fichier),
            file_id=f"fichier-{project_id}", taille=stat.st_size, mtime_ns=stat.st_mtime_ns,
            sha256=hashlib.sha256(fichier.read_bytes()).hexdigest(), generation_racine=1,
        ))
        session.add(SyncPlan(id=f"plan-{project_id}", project_id=project_id, generation_racine=1))
        await session.commit()


@pytest.mark.asyncio
async def test_cascade_refusee_conserve_les_racines_et_les_plans(client, tmp_path):
    async with database.AsyncSessionLocal() as session:
        session.add(Contact(id="contact-r1", first_name="Fictif"))
        await session.commit()
    for project_id in ("premier", "second"):
        await _garnir_dossier(tmp_path / project_id, project_id, "contact-r1")

    with patch.object(memory, "get_qdrant_service") as obtenir_index:
        obtenir_index.return_value.async_copier_fragments_projet = AsyncMock(return_value=[])
        obtenir_index.return_value.async_delete_by_scope = AsyncMock(side_effect=RuntimeError("Index indisponible"))
        reponse = await client.delete("/api/memory/contacts/contact-r1?cascade=true")
    assert reponse.status_code == 500

    async with database.AsyncSessionLocal() as session:
        assert await session.get(Contact, "contact-r1") is not None
        for project_id in ("premier", "second"):
            assert await session.get(Project, project_id) is not None
            racine = await session.get(ProjectSyncRoot, f"racine-{project_id}")
            assert not racine.detachee, "la cascade refusée a détaché une racine"
            assert racine.generation == 1
            assert await session.get(ProjectSyncEntry, f"entree-{project_id}") is not None
            assert (await session.get(SyncPlan, f"plan-{project_id}")).etat == EtatPlan.PROPOSE


@pytest.mark.asyncio
@pytest.mark.parametrize("episode", ["courant", "ancien"])
async def test_purge_ne_detache_que_les_contacts_de_l_episode_a_traiter(client, tmp_path, episode):
    maintenant = datetime.now(UTC)
    async with database.AsyncSessionLocal() as session:
        session.add(Contact(
            id="contact-r1", first_name="Fictif",
            last_interaction=maintenant - timedelta(days=4 * 365),
            rgpd_date_expiration=maintenant - timedelta(days=60),
        ))
        session.add(Notification(
            title="Préavis", message="Données fictives", source="rgpd_purge",
            action_url="/crm/contacts/contact-r1", created_at=maintenant - timedelta(days=40),
        ))
        session.add(Notification(
            title="Purge effectuée", message="Données fictives", source="rgpd_purge_done",
            action_url="/crm/contacts/contact-r1",
            created_at=maintenant - timedelta(days=20 if episode == "courant" else 100),
        ))
        await session.commit()
    await _garnir_dossier(tmp_path / "dossier", "dossier", "contact-r1")

    resultat = await rgpd_auto.auto_purge_expired_contacts()

    async with database.AsyncSessionLocal() as session:
        contact = await session.get(Contact, "contact-r1")
        racine = await session.get(ProjectSyncRoot, "racine-dossier")
        if episode == "courant":
            assert resultat == {"notifications": 0, "anonymisations": 0}
            assert contact.first_name == "Fictif"
            assert await session.get(Project, "dossier") is not None
            assert not racine.detachee, "un contact ignoré a perdu sa racine"
            assert racine.generation == 1
            assert await session.get(ProjectSyncEntry, "entree-dossier") is not None
            assert (await session.get(SyncPlan, "plan-dossier")).etat == EtatPlan.PROPOSE
        else:
            assert resultat["anonymisations"] == 1, "une ancienne notification bloque le nouvel épisode"
            assert contact.first_name == "[ANONYMISÉ]"
            assert await session.get(Project, "dossier") is None
            assert racine.detachee


@pytest.mark.asyncio
@pytest.mark.parametrize("chemin", ["manuel", "automatique", "projet", "cascade", "fermeture", "effacement_partiel"])
async def test_un_rollback_restitue_les_fragments_et_un_plan_fidele(client, tmp_path, monkeypatch, chemin):
    maintenant = datetime.now(UTC)
    async with database.AsyncSessionLocal() as session:
        session.add(Contact(
            id="contact-r1", first_name="Fictif",
            last_interaction=maintenant - timedelta(days=4 * 365),
        ))
        session.add(Notification(
            title="Préavis", message="Données fictives", source="rgpd_purge",
            action_url="/crm/contacts/contact-r1", created_at=maintenant - timedelta(days=40),
        ))
        await session.commit()
    await _garnir_dossier(tmp_path / "dossier", "dossier", "contact-r1")

    # Vrai moteur Qdrant en mémoire, vecteurs fixes : aucun encodeur ni réseau.
    index = object.__new__(QdrantService)
    index._client = QdrantClient(location=":memory:")
    index.client.create_collection(settings.qdrant_collection, vectors_config=VectorParams(size=2, distance=Distance.COSINE))
    fragments = [
        PointStruct(id=1, vector=[1., 0.], payload={"entity_id": "fichier-dossier", "scope": "project", "scope_id": "dossier", "text": "Note fictive"}),
        PointStruct(id=2, vector=[0., 1.], payload={"entity_id": "orphelin", "scope": "project", "scope_id": "dossier", "text": "Fragment sans ligne SQL"}),
        PointStruct(id=3, vector=[1., 0.], payload={"entity_id": "dossier", "scope": "global", "text": "Projet fictif"}),
        PointStruct(id=4, vector=[0., 1.], payload={"entity_id": "voisin", "scope": "project", "scope_id": "autre", "text": "Voisin intact"}),
    ]
    index.client.upsert(settings.qdrant_collection, points=fragments)
    monkeypatch.setattr(memory, "get_qdrant_service", lambda: index)
    if chemin == "effacement_partiel":
        effacer = index.delete_by_scope

        def effacer_puis_echouer(scope: str, scope_id: str) -> int:
            effacer(scope, scope_id)
            raise RuntimeError("Panne après l'effacement des fragments")

        monkeypatch.setattr(index, "delete_by_scope", effacer_puis_echouer)
    commit_reel = AsyncSession.commit

    async def refuser_commit(session: AsyncSession) -> None:
        if session.info.get("retrait_racines_verrous"):
            raise RuntimeError("Échec simulé du commit métier")
        await commit_reel(session)

    try:
        with patch.object(AsyncSession, "commit", new=refuser_commit):
            if chemin == "manuel":
                reponse = await client.post("/api/rgpd/anonymize/contact-r1", json={"reason": "Test fictif"})
                assert reponse.status_code == 500
            elif chemin == "automatique":
                assert await rgpd_auto.auto_purge_expired_contacts() == {"notifications": 0, "anonymisations": 0}
            elif chemin == "fermeture":
                async with database.AsyncSessionLocal() as session:
                    projet = await session.get(Project, "dossier")
                    await memory._nettoyer_et_supprimer_projet(session, projet)
                    assert index.client.retrieve(settings.qdrant_collection, ids=[1, 2, 3]) == []
                    # close sans commit doit annuler SQL et l'effacement vectoriel.
            else:
                url = "/api/memory/projects/dossier" if chemin in ("projet", "effacement_partiel") else "/api/memory/contacts/contact-r1?cascade=true"
                reponse = await client.delete(url)
                assert reponse.status_code == 500

        async with database.AsyncSessionLocal() as session:
            assert (await session.get(Contact, "contact-r1")).first_name == "Fictif"
            assert await session.get(Project, "dossier") is not None
            assert (await session.get(FileMetadata, "fichier-dossier")).chunk_count == 1
            assert not (await session.get(ProjectSyncRoot, "racine-dossier")).detachee
            assert await session.get(ProjectSyncEntry, "entree-dossier") is not None
        relus = index.client.retrieve(settings.qdrant_collection, ids=[1, 2, 3, 4], with_vectors=True)
        assert len(relus) == 4, "le rollback SQL a perdu les fragments de recherche"
        assert [(p.id, p.payload, p.vector) for p in sorted(relus, key=lambda p: p.id)] == [
            (p.id, p.payload, p.vector) for p in fragments
        ]
        plan = await sync.preparer_plan("dossier")
        assert (plan.nb_indexer, plan.nb_reindexer, plan.nb_inchanges) == (0, 0, 1)
        assert not sync._verrou("dossier").locked()
    finally:
        index.close()


@pytest.mark.asyncio
@pytest.mark.parametrize("issue", ["commit", "rollback"])
async def test_restitution_complete_de_deux_dossiers_sous_verrous(client, tmp_path, monkeypatch, issue):
    async with database.AsyncSessionLocal() as session:
        session.add(Contact(id="contact-r1", first_name="Fictif"))
        await session.commit()
    for project_id in ("premier", "second"):
        await _garnir_dossier(tmp_path / project_id, project_id, "contact-r1")
    index = object.__new__(QdrantService)
    index._client = QdrantClient(location=":memory:")
    index.client.create_collection(settings.qdrant_collection, vectors_config=VectorParams(size=2, distance=Distance.COSINE))
    # Plus d'une page, un second dossier, un fragment de fichier mal classé
    # et un voisin : on restaure tout le périmètre supprimé, et lui seulement.
    fragments = [PointStruct(id=i, vector=[1., 0.], payload={
        "entity_id": "fichier-premier", "scope": "project", "scope_id": "premier",
    }) for i in range(1001)] + [
        PointStruct(id=1001, vector=[0., 1.], payload={"entity_id": "fichier-second", "scope": "project", "scope_id": "second"}),
        PointStruct(id=1002, vector=[0., 1.], payload={"entity_id": "fichier-premier", "scope": "global"}),
        PointStruct(id=1003, vector=[0., 1.], payload={"entity_id": "voisin", "scope": "global"}),
    ]
    index.client.upsert(settings.qdrant_collection, points=fragments)
    monkeypatch.setattr(memory, "get_qdrant_service", lambda: index)
    restitution_entree = asyncio.Event()
    reprendre = asyncio.Event()
    restituer = index.async_restituer_fragments
    restitutions = []

    async def restituer_sous_verrous(points):
        assert all(sync._verrou(p).locked() for p in ("premier", "second"))
        restitutions.append(len(points))
        restitution_entree.set()
        await reprendre.wait()
        await restituer(points)

    monkeypatch.setattr(index, "async_restituer_fragments", restituer_sous_verrous)
    try:
        async with database.AsyncSessionLocal() as session:
            for project_id in ("premier", "second"):
                await memory._nettoyer_et_supprimer_projet(session, await session.get(Project, project_id))
            assert index.client.count(settings.qdrant_collection).count == 1
            if issue == "commit":
                await session.commit()
                assert restitutions == []
            else:
                annulation = asyncio.create_task(session.rollback())
                try:
                    await asyncio.wait_for(restitution_entree.wait(), timeout=5)
                    for project_id in ("premier", "second"):
                        with pytest.raises(sync.OperationRefusee):
                            await sync.preparer_plan(project_id)
                finally:
                    reprendre.set()
                    await annulation
                assert restitutions == [1002, 1]
            assert all(not sync._verrou(p).locked() for p in ("premier", "second"))
        # La fermeture et une nouvelle transaction ne ressuscitent pas un
        # effacement validé ; un rollback a restitué les mêmes points exacts.
        relus = index.client.retrieve(settings.qdrant_collection, ids=[p.id for p in fragments], with_vectors=True)
        attendus = fragments if issue == "rollback" else [fragments[-1]]
        assert [(p.id, p.payload, p.vector) for p in sorted(relus, key=lambda p: p.id)] == [
            (p.id, p.payload, p.vector) for p in attendus
        ]
        async with database.AsyncSessionLocal() as session:
            for project_id in ("premier", "second"):
                assert (await session.get(Project, project_id) is not None) == (issue == "rollback")
    finally:
        reprendre.set()
        index.close()
