"""
THERESE v2 - Test Configuration

Pytest fixtures and configuration for all tests.
"""

import asyncio
import os
import sys
from pathlib import Path
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

# Ensure src/backend is on sys.path so 'app' module is importable
_backend_dir = str(Path(__file__).resolve().parent.parent / "src" / "backend")
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

# Set test environment before importing app
os.environ["THERESE_ENV"] = "test"
os.environ["THERESE_DB_PATH"] = ":memory:"

# Flag pour que le lifespan de l'app saute les services externes en mode test
os.environ["THERESE_SKIP_SERVICES"] = "1"

from contextlib import asynccontextmanager

from app.main import app
from app.models.database import get_session


# Remplacer le lifespan par un lifespan minimal pour les tests
# (init DB seulement, pas de Qdrant, embeddings, MCP, skills)
@asynccontextmanager
async def _test_lifespan(_app):
    from app.models.database import init_db, close_db
    await init_db()
    yield
    await close_db()

app.router.lifespan_context = _test_lifespan


# Mock Qdrant : injecter un mock directement dans le singleton du module
# pour que tous les imports (chat.py, memory.py, files.py etc.) le voient
from unittest.mock import MagicMock

import app.services.qdrant as _qdrant_module

_mock_qdrant = MagicMock()
_mock_qdrant.search.return_value = []
_mock_qdrant.add_memory.return_value = None
_mock_qdrant.add_memories.return_value = 0
_mock_qdrant.delete_by_entity.return_value = 0
_mock_qdrant.delete_by_scope.return_value = 0
_mock_qdrant._initialized = True
_mock_qdrant.is_initialized.return_value = True

# Remplacer le singleton directement dans le module
_qdrant_module._qdrant_service = _mock_qdrant

# Aussi overrider la fonction factory pour que les nouveaux appels retournent le mock
_original_get_qdrant = _qdrant_module.get_qdrant_service
_qdrant_module.get_qdrant_service = lambda: _mock_qdrant


# Test database setup
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False},
)

async_session_maker = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create a fresh database session for each test (async, pour les tests unitaires)."""
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    async with async_session_maker() as session:
        yield session
        await session.rollback()

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)


class _AwaitableResponse:
    """Wrapper pour que response = await client.get(...) fonctionne avec TestClient sync."""

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


@pytest.fixture(scope="function")
def client():
    """Create test client (sync, compatible await via _AsyncCompatClient).

    Le TestClient utilise la DB initialisée par le test lifespan.
    Les tests qui créent des données les verront via les endpoints.
    """
    with TestClient(app, raise_server_exceptions=False) as tc:
        yield _AsyncCompatClient(tc)


@pytest.fixture
def sync_client() -> TestClient:
    """Create synchronous test client for simple tests."""
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
    assert response.status_code == expected_status, f"Expected {expected_status}, got {response.status_code}: {response.text}"


def assert_contains_keys(data: dict, keys: list):
    """Assert dictionary contains expected keys."""
    for key in keys:
        assert key in data, f"Missing key: {key}"
