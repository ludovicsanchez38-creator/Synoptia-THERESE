"""La suppression du profil ne peut réussir en laissant son vecteur derrière."""

import asyncio
import threading
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from app.services import user_profile as profil
from httpx import ASGITransport, AsyncClient


async def _creer_profil(session):
    await profil.set_user_profile(session, profil.UserProfile(name="Profil fictif"), embed_in_qdrant=False)


@pytest.mark.asyncio
async def test_une_nouvelle_demande_repare_un_vecteur_orphelin(db_session, monkeypatch):
    vecteur = ["owner_profile"]

    def supprimer(identifiant):
        vecteur.remove(identifiant)
        return 1

    monkeypatch.setattr(profil, "get_qdrant_service", lambda: SimpleNamespace(delete_by_entity=supprimer))
    assert await profil.delete_user_profile(db_session) is False
    assert vecteur == []


@pytest.mark.asyncio
async def test_echec_qdrant_ne_signale_pas_une_suppression_reussie(db_session, monkeypatch):
    await _creer_profil(db_session)
    generation = profil._GENERATION_PROFIL

    def echec(_identifiant):
        raise RuntimeError("Index fictif indisponible")

    monkeypatch.setattr(profil, "get_qdrant_service", lambda: SimpleNamespace(delete_by_entity=echec))
    with pytest.raises(RuntimeError, match="Index fictif indisponible"):
        await profil.delete_user_profile(db_session)
    assert (await profil.get_user_profile(db_session)).name == "Profil fictif"
    assert generation == profil._GENERATION_PROFIL


@pytest.mark.asyncio
async def test_annulation_avant_le_verrou_ne_supprime_rien(db_session, monkeypatch):
    await _creer_profil(db_session)
    generation = profil._GENERATION_PROFIL

    class VerrouObserve:
        def __init__(self):
            self.verrou = asyncio.Lock()
            self.attente = asyncio.Event()

        async def __aenter__(self):
            self.attente.set()
            await self.verrou.acquire()

        async def __aexit__(self, *_args):
            self.verrou.release()

    verrou = VerrouObserve()
    await verrou.verrou.acquire()
    monkeypatch.setattr(profil, "_VERROU_INDEXATION", verrou)
    suppression = asyncio.create_task(profil.delete_user_profile(db_session))
    try:
        await asyncio.wait_for(verrou.attente.wait(), 3)
        generation_pendant_attente = profil._GENERATION_PROFIL
        suppression.cancel()
        with pytest.raises(asyncio.CancelledError):
            await suppression
    finally:
        verrou.verrou.release()
    assert generation_pendant_attente == generation
    assert (await profil.get_user_profile(db_session)).name == "Profil fictif"


@pytest.mark.asyncio
async def test_annulation_pendant_qdrant_attend_la_fin_du_fil(db_session, monkeypatch):
    await _creer_profil(db_session)
    profil.set_cached_profile(profil.UserProfile(name="Profil fictif"))
    vecteur = ["owner_profile"]
    demarre = threading.Event()
    terminer = threading.Event()

    def suppression_lente(identifiant):
        demarre.set()
        if not terminer.wait(3):
            raise TimeoutError("Le test n'a pas libéré la suppression")
        vecteur.remove(identifiant)
        return 1

    monkeypatch.setattr(profil, "get_qdrant_service", lambda: SimpleNamespace(delete_by_entity=suppression_lente))
    suppression = asyncio.create_task(profil.delete_user_profile(db_session))
    try:
        assert await asyncio.to_thread(demarre.wait, 3)
        suppression.cancel()
        await asyncio.sleep(0)
        verrou_reste_tenu = profil._VERROU_INDEXATION.locked()
    finally:
        terminer.set()
    with pytest.raises(asyncio.CancelledError):
        await suppression
    assert verrou_reste_tenu
    assert await profil.get_user_profile(db_session) is None
    assert vecteur == []
    assert profil.get_cached_profile() is None


@pytest.mark.asyncio
async def test_echec_commit_sql_ne_retire_pas_le_vecteur(db_session, monkeypatch):
    await _creer_profil(db_session)
    vecteur = ["owner_profile"]

    def supprimer(identifiant):
        vecteur.remove(identifiant)
        return 1

    monkeypatch.setattr(profil, "get_qdrant_service", lambda: SimpleNamespace(delete_by_entity=supprimer))
    monkeypatch.setattr(db_session, "commit", AsyncMock(side_effect=RuntimeError("Commit fictif refusé")))
    with pytest.raises(RuntimeError, match="Commit fictif refusé"):
        await profil.delete_user_profile(db_session)
    assert (await profil.get_user_profile(db_session)).name == "Profil fictif"
    assert vecteur == ["owner_profile"]


@pytest.mark.asyncio
async def test_annulation_pendant_commit_sql_termine_la_suppression(db_session, monkeypatch):
    await _creer_profil(db_session)
    vecteur = ["owner_profile"]
    demarre, terminer = asyncio.Event(), asyncio.Event()
    commit_reel = db_session.commit

    async def commit_lent():
        demarre.set()
        await terminer.wait()
        await commit_reel()

    def supprimer(identifiant):
        vecteur.remove(identifiant)
        return 1

    monkeypatch.setattr(db_session, "commit", commit_lent)
    monkeypatch.setattr(profil, "get_qdrant_service", lambda: SimpleNamespace(delete_by_entity=supprimer))
    suppression = asyncio.create_task(profil.delete_user_profile(db_session))
    try:
        await asyncio.wait_for(demarre.wait(), 3)
        vecteur_avant_commit = list(vecteur)
        suppression.cancel()
    finally:
        terminer.set()
    with pytest.raises(asyncio.CancelledError):
        await suppression
    assert vecteur_avant_commit == ["owner_profile"]
    assert await profil.get_user_profile(db_session) is None
    assert vecteur == []


@pytest.mark.asyncio
async def test_nouvelle_fiche_pendant_retrait_retrouve_son_vecteur(db_session, monkeypatch):
    from app.models import database

    await _creer_profil(db_session)
    vecteur = ["Profil fictif"]
    demarre, terminer = threading.Event(), threading.Event()

    def supprimer(_identifiant):
        demarre.set()
        if not terminer.wait(3):
            raise TimeoutError("Le test n'a pas libéré la suppression")
        vecteur.clear()
        return 1

    async def indexer(nouveau_profil):
        vecteur[:] = [nouveau_profil.name]

    monkeypatch.setattr(profil, "get_qdrant_service", lambda: SimpleNamespace(delete_by_entity=supprimer))
    monkeypatch.setattr(profil, "_embed_profile", indexer)
    suppression = asyncio.create_task(profil.delete_user_profile(db_session))
    try:
        assert await asyncio.to_thread(demarre.wait, 3)
        async with database.AsyncSessionLocal() as nouvelle_session:
            nouveau = profil.UserProfile(name="Nouveau profil fictif")
            await profil.set_user_profile(nouvelle_session, nouveau)
            profil.set_cached_profile(nouveau)
            indexations = list(profil._INDEXATIONS_EN_COURS)
    finally:
        terminer.set()
    assert await suppression is True
    await asyncio.wait_for(asyncio.gather(*indexations), 3)
    assert profil.get_cached_profile().name == "Nouveau profil fictif"
    assert (await profil.get_user_profile(db_session)).name == "Nouveau profil fictif"
    assert vecteur == ["Nouveau profil fictif"]


@pytest.mark.asyncio
async def test_route_suppression_preserve_le_cache_d_une_sauvegarde_concurrente(
    db_session, monkeypatch
):
    from app.main import app

    await _creer_profil(db_session)
    profil.set_cached_profile(profil.UserProfile(name="Profil fictif"))
    vecteur = ["Profil fictif"]
    demarre, terminer = threading.Event(), threading.Event()

    def supprimer(_identifiant):
        demarre.set()
        if not terminer.wait(5):
            raise TimeoutError("Le test n'a pas libéré la suppression")
        vecteur.clear()
        return 1

    async def indexer(nouveau_profil):
        vecteur[:] = [nouveau_profil.name]

    monkeypatch.setattr(profil, "get_qdrant_service", lambda: SimpleNamespace(delete_by_entity=supprimer))
    monkeypatch.setattr(profil, "_embed_profile", indexer)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as http:
        suppression = asyncio.create_task(http.delete("/api/config/profile"))
        try:
            assert await asyncio.to_thread(demarre.wait, 3)
            sauvegarde = await http.post("/api/config/profile", json={"name": "Nouveau profil fictif"})
            assert sauvegarde.status_code == 200
            indexations = list(profil._INDEXATIONS_EN_COURS)
        finally:
            terminer.set()
        reponse = await asyncio.wait_for(suppression, 5)
        assert reponse.status_code == 200
        assert reponse.json() == {"deleted": True}
        await asyncio.wait_for(asyncio.gather(*indexations), 5)
        assert profil.get_cached_profile() is not None
        assert profil.get_cached_profile().name == "Nouveau profil fictif"
        relu = await http.get("/api/config/profile")
    assert relu.json()["name"] == "Nouveau profil fictif"
    assert vecteur == ["Nouveau profil fictif"]


@pytest.mark.asyncio
async def test_route_suppression_sans_fiche_vide_un_cache_obsolete(db_session):
    from app.main import app

    profil.set_cached_profile(profil.UserProfile(name="Profil obsolète"))
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as http:
        reponse = await http.delete("/api/config/profile")
    assert reponse.status_code == 200
    assert reponse.json() == {"deleted": False}
    assert profil.get_cached_profile() is None
