"""Passe 2 : vraies écritures Qdrant, sans encodeur ni service distant."""

import asyncio
import threading
from pathlib import Path
from unittest.mock import AsyncMock

import pytest
from app.config import settings
from app.models.entities import Contact, FileMetadata, Project
from app.routers import memory
from app.services import project_sync_service as sync
from app.services import qdrant as qdrant_module
from app.services.qdrant import QdrantService
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams
from sqlmodel import select


@pytest.fixture
def index_local(monkeypatch, tmp_path):
    index = object.__new__(QdrantService)
    index._client = QdrantClient(path=str(tmp_path / "qdrant"))
    index.client.create_collection(settings.qdrant_collection, vectors_config=VectorParams(size=2, distance=Distance.COSINE))
    monkeypatch.setattr(memory, "get_qdrant_service", lambda: index)
    monkeypatch.setattr(qdrant_module, "get_qdrant_service", lambda: index)
    monkeypatch.setattr(qdrant_module, "embed_text", lambda _texte: [1., 0.])
    monkeypatch.setattr(sync, "_dossier_restitutions", lambda: tmp_path / "restitutions", raising=False)
    yield index
    index.close()


def point(identifiant, entite, scope="project", scope_id="dossier"):
    return PointStruct(id=identifiant, vector=[1., 0.], payload={
        "entity_id": entite, "scope": scope, "scope_id": scope_id, "text": "Texte fictif",
    })


def lire(index):
    return index.client.scroll(settings.qdrant_collection, limit=100, with_vectors=True)[0]


@pytest.mark.asyncio
@pytest.mark.parametrize("type_fiche", [Contact, Project], ids=["contact", "sous_projet"])
@pytest.mark.parametrize("issue", ["rollback", "commit"])
async def test_reclassement_global_attend_le_commit(db_session, index_local, monkeypatch, type_fiche, issue):
    session = db_session
    session.add(Project(id="dossier", name="Dossier fictif"))
    fiche = type_fiche(id="fiche", scope="project", scope_id="dossier", **(
        {"first_name": "Fictif"} if type_fiche is Contact else {"name": "Sous-dossier fictif"}
    ))
    session.add(fiche)
    await session.commit()
    original = point(1, "fiche")
    index_local.client.upsert(settings.qdrant_collection, points=[original])

    await memory._nettoyer_et_supprimer_projet(session, await session.get(Project, "dossier"))
    avant_commit = lire(index_local)
    if issue == "rollback":
        monkeypatch.setattr(session, "commit", AsyncMock(side_effect=RuntimeError("Commit refusé")))
        with pytest.raises(RuntimeError, match="Commit refusé"):
            await session.commit()
        await session.rollback()
        relus = lire(index_local)
        assert [(p.id, p.payload, p.vector) for p in relus] == [
            (original.id, original.payload, original.vector),
        ], "le rollback laisse un vecteur global pour une fiche privée"
        assert (await session.get(type_fiche, "fiche")).scope == "project"
    else:
        await session.commit()
        assert len(lire(index_local)) == 1
        assert lire(index_local)[0].payload["scope"] == "global"
        assert (await session.get(type_fiche, "fiche")).scope == "global"
    assert not any(p.payload["scope"] == "global" for p in avant_commit), "publication globale avant commit"


@pytest.mark.asyncio
@pytest.mark.parametrize("effacement", ["scope", "entity"])
@pytest.mark.parametrize("annulations", [1, 2])
async def test_annulation_attend_le_fil_avant_restitution(db_session, index_local, monkeypatch, effacement, annulations):
    session = db_session
    session.add(Project(id="dossier", name="Dossier fictif"))
    await session.commit()
    original = point(1, "dossier", "global", None) if effacement == "entity" else point(1, "fragment")
    index_local.client.upsert(settings.qdrant_collection, points=[original])
    entree, fin = asyncio.Event(), asyncio.Event()
    continuer = threading.Event()
    boucle = asyncio.get_running_loop()
    methode = f"delete_by_{effacement}"
    effacer = getattr(index_local, methode)

    def fil_non_annulable(*args):
        boucle.call_soon_threadsafe(entree.set)
        assert continuer.wait(timeout=5), "le test n’a pas libéré le fil"
        try:
            return effacer(*args)
        finally:
            boucle.call_soon_threadsafe(fin.set)

    monkeypatch.setattr(index_local, methode, fil_non_annulable)
    restituer = AsyncMock(wraps=index_local.async_restituer_fragments)
    monkeypatch.setattr(index_local, "async_restituer_fragments", restituer)

    async def supprimer():
        try:
            await memory._nettoyer_et_supprimer_projet(session, await session.get(Project, "dossier"))
        finally:
            await session.rollback()

    tache = asyncio.create_task(supprimer())
    try:
        await asyncio.wait_for(entree.wait(), timeout=5)
        for _ in range(annulations):
            tache.cancel()
            await asyncio.wait([tache], timeout=0.05)
        restitution_precoce = restituer.called
        verrou_conserve = sync._verrou("dossier").locked()
    finally:
        continuer.set()
        await asyncio.wait_for(fin.wait(), timeout=5)
        with pytest.raises(asyncio.CancelledError):
            await tache

    assert [(p.id, p.payload, p.vector) for p in lire(index_local)] == [
        (original.id, original.payload, original.vector),
    ], "le fil d’effacement a supprimé les fragments après leur restitution"
    assert not restitution_precoce, "restitution avant la fin effective de l’effacement"
    assert verrou_conserve
    assert not sync._verrou("dossier").locked()
    assert await session.get(Project, "dossier") is not None


@pytest.mark.asyncio
@pytest.mark.parametrize("reprise", ["redemarrage", "session_reutilisee"])
async def test_restitution_en_echec_preserve_les_suivantes_et_survit_a_la_session(db_session, index_local, monkeypatch, tmp_path, reprise):
    session = db_session
    for identifiant in ("premier", "second"):
        session.add(Project(id=identifiant, name="Dossier fictif"))
    await session.commit()
    originaux = [point(1, "fragment-1", scope_id="premier"), point(2, "fragment-2", scope_id="second")]
    index_local.client.upsert(settings.qdrant_collection, points=originaux)
    tentatives = []
    restituer = index_local.async_restituer_fragments

    async def echouer_sur_premier(fragments):
        identifiant = fragments[0].payload["scope_id"]
        tentatives.append(identifiant)
        if identifiant == "premier":
            raise RuntimeError("Restitution indisponible")
        await restituer(fragments)

    monkeypatch.setattr(index_local, "async_restituer_fragments", echouer_sur_premier)
    for identifiant in ("premier", "second"):
        await memory._nettoyer_et_supprimer_projet(session, await session.get(Project, identifiant))
    try:
        try:
            await session.rollback()
        except RuntimeError:
            pass
        assert tentatives == ["premier", "second"], "une restitution en échec empêche celle du dossier suivant"
        assert len(session.info.get("retrait_racines_index", [])) == 1, "la copie non restituée a été perdue"
        assert [p.id for p in lire(index_local)] == [2]
        assert sync._verrou("premier").locked()
        assert not sync._verrou("second").locked()

        journaux = list((tmp_path / "restitutions").glob("*.json.enc"))
        assert len(journaux) == 1
        assert b"Texte fictif" not in journaux[0].read_bytes()
        anciens_verrous = dict(sync._verrous_projet)
        if reprise == "redemarrage":
            # Aucune copie mémoire, aucun client ni verrou de l'ancien
            # processus : seuls SQL, Qdrant et le journal sur disque restent.
            session.info.clear()
            await session.close()
            monkeypatch.setattr(sync, "_verrous_projet", {})
            monkeypatch.setattr(sync, "_verrous_restitutions", {})
            index_local.close()
            index_local._client = QdrantClient(path=str(tmp_path / "qdrant"))
        monkeypatch.setattr(index_local, "async_restituer_fragments", restituer)
        await qdrant_module.init_qdrant()
        assert [(p.id, p.payload, p.vector) for p in lire(index_local)] == [
            (p.id, p.payload, p.vector) for p in originaux
        ]
        assert not sync._verrou("premier").locked()
        assert list((tmp_path / "restitutions").glob("*.json.enc")) == []
        if reprise == "session_reutilisee":
            await session.execute(select(Project))
            # Un nouveau détenteur prend le verrou rendu par la reprise.
            nouveau_verrou = sync._verrou("premier")
            await nouveau_verrou.acquire()
            await session.rollback()
            assert nouveau_verrou.locked(), "l’ancienne session libère le verrou de son successeur"
            nouveau_verrou.release()
        else:
            for verrou in anciens_verrous.values():
                if verrou.locked():
                    verrou.release()
        await qdrant_module.init_qdrant()
        assert len(lire(index_local)) == 2
    finally:
        for identifiant in ("premier", "second"):
            verrou = sync._verrou(identifiant)
            if verrou.locked():
                verrou.release()


@pytest.mark.asyncio
@pytest.mark.parametrize("avec_projet", [True, False])
async def test_cascade_commit_refuse_restitue_les_fichiers_du_contact(db_session, index_local, monkeypatch, avec_projet):
    session = db_session
    session.add(Contact(id="personne", first_name="Fictif"))
    if avec_projet:
        session.add(Project(id="dossier", name="Dossier fictif", contact_id="personne"))
    session.add(FileMetadata(id="fichier-contact", name="Note fictive", path="/fictif/note.txt", extension=".txt", size=12, scope="contact", scope_id="personne"))
    await session.commit()
    originaux = [point(1, "fichier-contact", "contact", "personne"), point(2, "voisin", "global", None)]
    if avec_projet:
        originaux.append(point(3, "fragment-projet"))
    index_local.client.upsert(settings.qdrant_collection, points=originaux)
    monkeypatch.setattr(session, "commit", AsyncMock(side_effect=RuntimeError("Commit refusé")))

    with pytest.raises(RuntimeError, match="Commit refusé"):
        await memory.delete_contact("personne", cascade=True, session=session)
    await session.rollback()

    assert [(p.id, p.payload, p.vector) for p in lire(index_local)] == [
        (p.id, p.payload, p.vector) for p in originaux
    ], "le rollback de la cascade a perdu le fichier rattaché au contact"
    assert await session.get(Contact, "personne") is not None
    assert await session.get(FileMetadata, "fichier-contact") is not None
    if avec_projet:
        assert await session.get(Project, "dossier") is not None


@pytest.mark.asyncio
async def test_journal_residuel_ne_ressuscite_pas_un_retrait_commite(db_session, index_local, monkeypatch, tmp_path):
    session = db_session
    session.add(Project(id="dossier", name="Dossier fictif"))
    await session.commit()
    index_local.client.upsert(settings.qdrant_collection, points=[point(1, "fragment")])
    await memory._nettoyer_et_supprimer_projet(session, await session.get(Project, "dossier"))
    journal, = (tmp_path / "restitutions").glob("*.json.enc")
    effacer = Path.unlink

    def nettoyage_indisponible(chemin, *args, **kwargs):
        if chemin == journal:
            raise PermissionError("Nettoyage du journal indisponible")
        return effacer(chemin, *args, **kwargs)

    with monkeypatch.context() as contexte:
        contexte.setattr(Path, "unlink", nettoyage_indisponible)
        await session.commit()
    assert journal.exists()
    restituer = AsyncMock(wraps=index_local.async_restituer_fragments)
    monkeypatch.setattr(index_local, "async_restituer_fragments", restituer)

    await qdrant_module.init_qdrant()

    restituer.assert_not_awaited()
    assert lire(index_local) == []
    assert not journal.exists()
    assert await session.get(Project, "dossier") is None
    assert not sync._verrou("dossier").locked()
