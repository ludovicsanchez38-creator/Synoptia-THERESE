"""Une indexation de profil ne garde pas de connexion après le client de test."""
import asyncio
import sys
from pathlib import Path
from unittest.mock import AsyncMock

import pytest
from app.models import database
from app.services import user_profile
from sqlalchemy import text
from sqlalchemy.util.concurrency import greenlet_spawn


@pytest.mark.parametrize('racine', ['tests', 'src/backend/tests'])
async def test_le_lifespan_attend_la_lecture_du_profil(racine, monkeypatch):
    chemin = (Path(racine) / 'conftest.py').resolve()
    harnais = next(m for m in list(sys.modules.values())
                   if getattr(m, '__file__', None) and Path(m.__file__).resolve() == chemin)
    commencee = asyncio.Event()

    async def relecture():
        async with database.get_session_context() as session:
            await session.execute(text('SELECT 1'))
            commencee.set()
            await asyncio.sleep(0.05)
        return True

    monkeypatch.setattr(user_profile, '_VERROU_INDEXATION', asyncio.Lock())
    monkeypatch.setattr(user_profile, '_embed_profile', AsyncMock())
    monkeypatch.setattr(user_profile, '_profil_encore_enregistre', relecture)
    tache = None
    pool = None
    try:
        async with harnais._test_lifespan(harnais.app):
            pool = database.async_engine.pool
            tache = asyncio.create_task(user_profile._indexer_en_arriere_plan(
                user_profile.UserProfile(name='Profil fictif'), user_profile._GENERATION_PROFIL,
            ))
            user_profile._INDEXATIONS_EN_COURS.add(tache)
            tache.add_done_callback(user_profile._INDEXATIONS_EN_COURS.discard)
            await asyncio.wait_for(commencee.wait(), timeout=5)
        assert tache.done(), "Le client ferme la base pendant la lecture du profil"
        assert pool.checkedout() == 0
        assert pool.checkedin() == 0
    finally:
        if tache is not None:
            await tache
        if pool is not None:
            await greenlet_spawn(pool.dispose)
        await database.close_db()
