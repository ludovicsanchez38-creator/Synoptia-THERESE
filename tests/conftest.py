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
    """Create a fresh database session for each test."""
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    async with async_session_maker() as session:
        yield session
        await session.rollback()

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)


class _AsyncTestClientWrapper:
    """Wrapper qui rend TestClient compatible avec `await client.get(...)`."""

    def __init__(self, tc: TestClient):
        self._tc = tc

    async def get(self, *args, **kwargs):
        return self._tc.get(*args, **kwargs)

    async def post(self, *args, **kwargs):
        return self._tc.post(*args, **kwargs)

    async def put(self, *args, **kwargs):
        return self._tc.put(*args, **kwargs)

    async def patch(self, *args, **kwargs):
        return self._tc.patch(*args, **kwargs)

    async def delete(self, *args, **kwargs):
        return self._tc.delete(*args, **kwargs)


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator:
    """Create test client with database session override.

    Utilise TestClient synchrone wrappé en async pour éviter le deadlock
    entre pytest-asyncio et ASGITransport.
    """

    async def override_get_session():
        yield db_session

    app.dependency_overrides[get_session] = override_get_session

    with TestClient(app, raise_server_exceptions=False) as tc:
        yield _AsyncTestClientWrapper(tc)

    app.dependency_overrides.clear()


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
