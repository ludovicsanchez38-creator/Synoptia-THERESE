"""
THERESE v2 - Test Configuration

Pytest fixtures and configuration for all tests.
"""

import os
import sys
import tempfile
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator
from unittest.mock import MagicMock

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import SQLModel

# Ensure src/backend is on sys.path so 'app' module is importable
_backend_dir = str(Path(__file__).resolve().parent.parent / "src" / "backend")
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

# Set test environment before importing app
os.environ["THERESE_ENV"] = "test"
os.environ["THERESE_SKIP_SERVICES"] = "1"
# Isolation des données : ne JAMAIS toucher la base réelle de l'utilisateur.
# Les fixtures client/db_session font drop_all/create_all ; sans data dir dédié,
# lancer la suite détruirait ~/.therese. setdefault respecte un override (CI/dev).
os.environ.setdefault("THERESE_DATA_DIR", tempfile.mkdtemp(prefix="therese-test-"))
# US-014 : clé SQLCipher fixe pour la suite - déterministe et sans dépendre
# du trousseau de la machine (Keychain absent en CI, prompts possibles en dev).
# Le chemin chiffré reste ENTIÈREMENT exercé (engines + migration + backup).
os.environ.setdefault("THERESE_DB_KEY", "ad" * 32)

from app.main import app  # noqa: E402  (doit être importé APRÈS le setup os.environ ci-dessus)


# Remplacer le lifespan par un lifespan minimal pour les tests
# (init DB seulement, pas de Qdrant, embeddings, MCP, skills)
@asynccontextmanager
async def _test_lifespan(_app):
    from app.models.database import close_db, init_db
    await init_db()
    yield
    await close_db()

app.router.lifespan_context = _test_lifespan


# Mock Qdrant : injecter un mock directement dans le singleton du module
# pour que tous les imports (chat.py, memory.py, files.py etc.) le voient
import app.services.qdrant as _qdrant_module  # noqa: E402  (après setup env, cf ci-dessus)

_mock_qdrant = MagicMock()
_mock_qdrant.search.return_value = []
_mock_qdrant.add_memory.return_value = None
_mock_qdrant.add_memories.return_value = 0
_mock_qdrant.delete_by_entity.return_value = 0
_mock_qdrant.delete_by_scope.return_value = 0
_mock_qdrant._initialized = True
_mock_qdrant.is_initialized.return_value = True
_qdrant_module._qdrant_service = _mock_qdrant
_qdrant_module.get_qdrant_service = lambda: _mock_qdrant


# ============================================================
# Awaitable wrappers pour TestClient sync
# ============================================================

class _AwaitableResponse:
    """Wrapper pour que `response = await client.get(...)` fonctionne."""

    def __init__(self, response):
        self._response = response

    def __getattr__(self, name):
        return getattr(self._response, name)

    def __await__(self):
        yield
        return self._response


class _AsyncCompatClient:
    """TestClient dont les méthodes HTTP retournent des awaitables.

    Permet aux tests async existants (await client.get(...)) de fonctionner
    sans modifier chaque fichier de test.
    """

    def __init__(self, tc: TestClient):
        self._tc = tc

    def get(self, *args, **kwargs):
        return _AwaitableResponse(self._tc.get(*args, **kwargs))

    def post(self, *args, **kwargs):
        return _AwaitableResponse(self._tc.post(*args, **kwargs))

    def put(self, *args, **kwargs):
        return _AwaitableResponse(self._tc.put(*args, **kwargs))

    def patch(self, *args, **kwargs):
        return _AwaitableResponse(self._tc.patch(*args, **kwargs))

    def delete(self, *args, **kwargs):
        return _AwaitableResponse(self._tc.delete(*args, **kwargs))


# ============================================================
# Fixtures
# ============================================================

@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Session DB async pour les tests unitaires (services, etc.).

    Utilise le AsyncSessionLocal de l'app (initialisé par le test lifespan)
    pour que les données soient partagées avec les endpoints.
    """
    from app.models import database as db_module

    # S'assurer que la DB est initialisée. NB : close_db() (shutdown du lifespan
    # d'un test HTTP anterieur) remet async_engine a None SANS reinitialiser
    # AsyncSessionLocal -> on teste les deux pour eviter un async_engine None ici.
    if db_module.async_engine is None or db_module.AsyncSessionLocal is None:
        await db_module.init_db()

    # Créer les tables
    async with db_module.async_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    async with db_module.AsyncSessionLocal() as session:
        yield session
        await session.rollback()

    # Nettoyer les tables après chaque test
    async with db_module.async_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
        await conn.run_sync(SQLModel.metadata.create_all)


@pytest.fixture(scope="function")
def client():
    """Test client HTTP sync, compatible await.

    Le TestClient lance le lifespan (init_db), donc la DB est prête.
    Les tables sont recréées à chaque test pour l'isolation.
    """
    with TestClient(app, raise_server_exceptions=False) as tc:
        # Isolation : drop + recreate toutes les tables avant chaque test
        from app.models import database as db_module
        if db_module.sync_engine is not None:
            SQLModel.metadata.drop_all(db_module.sync_engine)
            SQLModel.metadata.create_all(db_module.sync_engine)
        yield _AsyncCompatClient(tc)


@pytest.fixture
def sync_client() -> TestClient:
    """Test client synchrone classique."""
    return TestClient(app)


# ============================================================
# Mock data fixtures
# ============================================================

@pytest.fixture
def sample_contact_data():
    """Sample contact data for tests."""
    return {
        "first_name": "Jean",
        "last_name": "Dupont",
        "company": "Synoptia",
        "email": "jean@synoptia.fr",
        "phone": "+33612345678",
        "notes": "Contact test",
        "tags": ["client", "vip"],
    }


@pytest.fixture
def sample_project_data():
    """Sample project data for tests."""
    return {
        "name": "Projet Test",
        "description": "Description du projet test",
        "status": "active",
        "budget": 10000.0,
        "tags": ["dev", "ia"],
    }


@pytest.fixture
def sample_chat_message():
    """Sample chat message for tests."""
    return {
        "message": "Bonjour, comment vas-tu ?",
        "conversation_id": None,
        "include_memory": False,
        "stream": False,
    }


@pytest.fixture
def sample_roi_request():
    """Sample ROI calculation request."""
    return {
        "investment": 10000,
        "gain": 15000,
    }


@pytest.fixture
def sample_ice_request():
    """Sample ICE score request."""
    return {
        "impact": 8,
        "confidence": 7,
        "ease": 6,
    }


@pytest.fixture
def sample_rice_request():
    """Sample RICE score request."""
    return {
        "reach": 1000,
        "impact": 2,
        "confidence": 80,
        "effort": 2,
    }


@pytest.fixture
def sample_npv_request():
    """Sample NPV calculation request."""
    return {
        "initial_investment": 100000,
        "cash_flows": [30000, 40000, 50000, 60000],
        "discount_rate": 0.10,
    }


@pytest.fixture
def sample_breakeven_request():
    """Sample break-even calculation request."""
    return {
        "fixed_costs": 50000,
        "variable_cost_per_unit": 20,
        "price_per_unit": 50,
    }


@pytest.fixture
def sample_board_request():
    """Sample board deliberation request."""
    return {
        "question": "Dois-je investir dans l'IA pour mon entreprise ?",
        "context": "PME de 15 salaries, secteur services",
    }


@pytest.fixture
def sample_mcp_server():
    """Sample MCP server configuration."""
    return {
        "name": "test-server",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-filesystem"],
        "env": {},
        "enabled": True,
    }


# ============================================================
# Helper functions
# ============================================================

def assert_response_ok(response, expected_status=200):
    """Assert response is successful."""
    assert response.status_code == expected_status, (
        f"Expected {expected_status}, got {response.status_code}: {response.text}"
    )


def assert_contains_keys(data: dict, keys: list):
    """Assert dictionary contains expected keys."""
    for key in keys:
        assert key in data, f"Missing key: {key}"


# ============================================================
# Sortie propre : éviter le hang post-suite (threads orphelins)
# ============================================================
# Certains tests async (TestClient + appels réseau) laissent des threads
# non-daemon ouverts : pytest affiche bien "N passed" mais le process ne rend
# pas la main, et la CI le tue après 5 min (exit 124) -> job rouge à tort
# (cf. warning "threads orphelins" du workflow CI). On force la sortie juste
# après la fin de session en préservant le code de sortie pytest. On ne
# court-circuite pas pytest-cov (qui écrit ses rapports en sessionfinish).
@pytest.hookimpl(trylast=True)
def pytest_sessionfinish(session, exitstatus):
    import sys

    if any(arg.startswith("--cov") for arg in sys.argv):
        return
    import os

    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(int(exitstatus))
