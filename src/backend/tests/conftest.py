"""
THERESE v2 - Backend Test Configuration

Pytest fixtures and configuration for backend tests.
"""

import asyncio
import os
import sys
import tempfile
from collections.abc import AsyncGenerator, Generator
from pathlib import Path

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

# Set test environment before importing app
os.environ["THERESE_ENV"] = "test"
os.environ["THERESE_DB_PATH"] = ":memory:"

from app.main import app
from app.models.database import get_session

# Test database setup
#
# B-153 : la base de test etait `sqlite+aiosqlite:///:memory:`, propre au
# moteur ASYNC. Or plusieurs routes lisent par le moteur SYNCHRONE de
# l'application (`get_sync_session`, cf `_assembler_export_rgpd` du routeur
# RGPD) : elles ne voyaient donc RIEN de ce que les tests inserent, et
# `test_export_and_delete_cover_every_user_table` echouait sur des sections
# vides - un faux diagnostic qui accusait l'export lui-meme. Les deux moteurs
# pointent desormais sur le MEME fichier temporaire, et la fixture
# `db_session` branche le moteur synchrone de l'application dessus.
_TEST_DB_FILE = Path(tempfile.mkdtemp(prefix="therese-backend-tests-")) / "test.db"
TEST_DATABASE_URL = f"sqlite+aiosqlite:///{_TEST_DB_FILE}"
TEST_SYNC_DATABASE_URL = f"sqlite:///{_TEST_DB_FILE}"

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


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create a fresh database session for each test.

    B-153 : le moteur SYNCHRONE de l'application est branche sur la meme base
    que le moteur async, le temps du test, puis restaure. Sans cela, toute
    route qui passe par `get_sync_session()` lit une autre base (ou leve
    « Database not initialized ») et ne voit aucune donnee inseree ici.
    """
    import app.models.database as database_module

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    moteur_sync_test = create_engine(
        TEST_SYNC_DATABASE_URL,
        echo=False,
        connect_args={"check_same_thread": False},
    )
    moteur_sync_precedent = database_module.sync_engine
    database_module.sync_engine = moteur_sync_test

    try:
        async with async_session_maker() as session:
            yield session
            await session.rollback()
    finally:
        database_module.sync_engine = moteur_sync_precedent
        moteur_sync_test.dispose()

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def async_client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create async test client with database session override."""

    async def override_get_session():
        yield db_session

    app.dependency_overrides[get_session] = override_get_session

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


# Alias for compatibility
@pytest_asyncio.fixture(scope="function")
async def client(async_client: AsyncClient) -> AsyncGenerator[AsyncClient, None]:
    """Alias for async_client."""
    yield async_client


@pytest.fixture
def sync_client() -> Generator[TestClient, None, None]:
    """Create synchronous test client for simple tests."""
    with TestClient(app) as client:
        yield client


def pytest_runtest_logreport(report):
    """Imprime chaque échec/erreur DÈS qu'il survient.

    Filet de sécurité : la suite peut être tuée pendant le teardown (threads
    orphelins) avant que pytest n'imprime sa section FAILURES + le résumé final.
    On écrit donc les nodeids fautifs immédiatement sur stderr pour qu'ils
    restent visibles dans les logs CI même en cas de kill.
    """
    if report.when == "call" and report.outcome == "failed":
        print(f"\n[TEST-FAILED] {report.nodeid}", file=sys.stderr, flush=True)
    elif report.outcome == "failed":  # erreur de setup/teardown
        print(f"\n[TEST-ERROR:{report.when}] {report.nodeid}", file=sys.stderr, flush=True)


@pytest.hookimpl(trylast=True)
def pytest_sessionfinish(session, exitstatus):
    """Rend la main après le résumé malgré les threads de clients de test."""
    if any(arg.startswith("--cov") for arg in sys.argv):
        return
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(int(exitstatus))
