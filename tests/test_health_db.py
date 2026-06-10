"""US-008 (RES2) : /health et /health/services doivent tester réellement la DB.

Bug : `await session.execute("SELECT 1")` en chaîne brute lève sous SQLAlchemy
2.x (exige text()), l'except l'avale → database:false PERMANENT même DB saine.
Et /health ne testait pas la DB (lecture d'un singleton stale)."""
from unittest.mock import patch

import pytest


@pytest.mark.asyncio
async def test_health_services_database_true_quand_db_saine(client):
    resp = await client.get("/health/services")
    assert resp.status_code == 200
    assert resp.json()["services"]["database"]["available"] is True


@pytest.mark.asyncio
async def test_health_global_reflete_db_saine(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["services"].get("database") is True


@pytest.mark.asyncio
async def test_health_services_database_false_quand_db_down(client):
    class _BadSession:
        async def execute(self, *a, **k):
            raise RuntimeError("DB indisponible")

    class _BadCtx:
        async def __aenter__(self):
            return _BadSession()

        async def __aexit__(self, *a):
            return False

    with patch("app.models.database.get_session_context", return_value=_BadCtx()):
        resp = await client.get("/health/services")
        assert resp.status_code == 200
        assert resp.json()["services"]["database"]["available"] is False
