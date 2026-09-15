"""B-806 (cycle 9) : quand le client abandonne un flux (BaseHTTPMiddleware annule
la tâche), `session.close()` était interrompu par CancelledError et la connexion
aiosqlite n'était jamais rendue au pool (« non-checked-in connection » ramassée
par le GC). Le pool est borné (5 + 10) : des abandons répétés l'épuiseraient."""
from __future__ import annotations

import asyncio

import pytest
from app.models import database


class FausseSession:
    def __init__(self, termine: asyncio.Event, duree: float):
        self._termine = termine
        self._duree = duree
        self.rollbacks = 0

    async def commit(self):
        return None

    async def rollback(self):
        self.rollbacks += 1

    async def close(self):
        await asyncio.sleep(self._duree)
        self._termine.set()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        await self.close()


@pytest.mark.asyncio
async def test_la_fermeture_de_session_survit_a_l_annulation(monkeypatch) -> None:
    termine = asyncio.Event()
    monkeypatch.setattr(database, "AsyncSessionLocal", lambda: FausseSession(termine, 0.05))

    async def consommer():
        generateur = database.get_session()
        await generateur.__anext__()
        await generateur.aclose()

    tache = asyncio.create_task(consommer())
    await asyncio.sleep(0.01)
    tache.cancel()
    with pytest.raises(asyncio.CancelledError):
        await tache

    await asyncio.wait_for(termine.wait(), timeout=1)
