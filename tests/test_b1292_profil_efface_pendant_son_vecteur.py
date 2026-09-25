"""B-1292 : un profil enregistré juste après l'arrêt de la purge recevait une
génération neuve ; son vecteur (nom, courriel, entreprise) arrivait dans
l'index APRÈS la purge et son 200, alors que la ligne était effacée, et rien
ne le retirait. Même relecture que les fiches (B-1222) : si le profil a
disparu pendant le calcul, le vecteur est retiré. Revue ciblée, passe 7."""

import asyncio
import time

import pytest


@pytest.mark.asyncio
async def test_un_profil_efface_pendant_son_vecteur_est_retire_de_l_index(db_session, monkeypatch):
    import app.services.qdrant as mq
    from app.models.database import get_session_context
    from app.models.entities import Preference
    from app.services import user_profile as up
    from sqlmodel import delete

    retraits: list[str] = []
    monkeypatch.setattr(mq._qdrant_service, "delete_by_entity", lambda entite: retraits.append(entite) or 0)
    monkeypatch.setattr(up, "_VERROU_INDEXATION", asyncio.Lock())

    async def embed(profil):
        await asyncio.to_thread(time.sleep, 0.3)

    monkeypatch.setattr(up, "_embed_profile", embed)
    await up.set_user_profile(db_session, up.UserProfile(name="Profil Tardif"), embed_in_qdrant=False)

    indexation = asyncio.create_task(
        up._indexer_en_arriere_plan(up.UserProfile(name="Profil Tardif"), up._GENERATION_PROFIL)
    )
    await asyncio.sleep(0.1)  # le vecteur est en cours de calcul : la purge efface la ligne
    async with get_session_context() as session:
        await session.execute(delete(Preference))
        await session.commit()
    await indexation
    assert "owner_profile" in retraits, retraits


@pytest.mark.asyncio
async def test_un_profil_toujours_la_garde_son_vecteur(db_session, monkeypatch):
    import app.services.qdrant as mq
    from app.services import user_profile as up

    retraits: list[str] = []
    monkeypatch.setattr(mq._qdrant_service, "delete_by_entity", lambda entite: retraits.append(entite) or 0)
    monkeypatch.setattr(up, "_VERROU_INDEXATION", asyncio.Lock())

    async def embed(profil):
        return None

    monkeypatch.setattr(up, "_embed_profile", embed)
    await up.set_user_profile(db_session, up.UserProfile(name="Profil"), embed_in_qdrant=False)
    await up._indexer_en_arriere_plan(up.UserProfile(name="Profil"), up._GENERATION_PROFIL)
    assert retraits == [], retraits
