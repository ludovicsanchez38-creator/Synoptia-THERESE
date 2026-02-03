"""
THÉRÈSE v2 - Database Connection

SQLite database setup with SQLModel.
"""

import logging
from pathlib import Path
from typing import AsyncGenerator

from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy import event, text as sqlalchemy_text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.config import settings

logger = logging.getLogger(__name__)

# Sync engine for SQLModel compatibility
sync_engine = None

# Async engine for FastAPI
async_engine = None

# Session factory
AsyncSessionLocal = None


def get_database_url(async_mode: bool = True) -> str:
    """Get database URL for SQLite."""
    db_path = settings.db_path
    if async_mode:
        return f"sqlite+aiosqlite:///{db_path}"
    return f"sqlite:///{db_path}"


async def init_db() -> None:
    """Initialize database connection and create tables."""
    global sync_engine, async_engine, AsyncSessionLocal

    logger.info(f"Initializing database at {settings.db_path}")

    # Ensure parent directory exists
    settings.db_path.parent.mkdir(parents=True, exist_ok=True)

    # Create sync engine for table creation
    sync_engine = create_engine(
        get_database_url(async_mode=False),
        echo=settings.debug,
        connect_args={"check_same_thread": False},
    )

    # PERF-005 + Phase 3: SQLite PRAGMAs optimises
    @event.listens_for(sync_engine, "connect")
    def _set_sqlite_pragmas(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA busy_timeout=5000")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA cache_size=-10000")  # 10 MB
        cursor.execute("PRAGMA temp_store=MEMORY")
        cursor.execute("PRAGMA mmap_size=268435456")  # 256 MB
        cursor.close()

    # Create async engine for operations (Phase 3: pool configuration)
    async_engine = create_async_engine(
        get_database_url(async_mode=True),
        echo=settings.debug,
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True,
        pool_recycle=1800,
    )

    # Appliquer les memes PRAGMAs sur le moteur async
    @event.listens_for(async_engine.sync_engine, "connect")
    def _set_async_sqlite_pragmas(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA busy_timeout=5000")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA cache_size=-10000")
        cursor.execute("PRAGMA temp_store=MEMORY")
        cursor.execute("PRAGMA mmap_size=268435456")
        cursor.close()

    # Create session factory
    AsyncSessionLocal = sessionmaker(
        async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    # Create tables using sync engine
    # Import models to register them with SQLModel
    from app.models import entities  # noqa: F401
    from app.services import audit  # noqa: F401 - ActivityLog model

    SQLModel.metadata.create_all(sync_engine)

    # Phase 3 + PERF audit: Creer les index manquants pour les DB existantes
    with sync_engine.connect() as conn:
        index_statements = [
            "CREATE INDEX IF NOT EXISTS ix_contacts_email ON contacts (email)",
            "CREATE INDEX IF NOT EXISTS ix_contacts_last_interaction ON contacts (last_interaction)",
            "CREATE INDEX IF NOT EXISTS ix_conversations_created_at ON conversations (created_at)",
            "CREATE INDEX IF NOT EXISTS ix_board_decisions_created_at ON board_decisions (created_at)",
            # PERF audit - index sur les FK frequemment filtrees
            "CREATE INDEX IF NOT EXISTS ix_tasks_project_id ON tasks (project_id)",
            "CREATE INDEX IF NOT EXISTS ix_invoice_lines_invoice_id ON invoice_lines (invoice_id)",
            "CREATE INDEX IF NOT EXISTS ix_activities_contact_id ON activities (contact_id)",
            "CREATE INDEX IF NOT EXISTS ix_deliverables_project_id ON deliverables (project_id)",
            "CREATE INDEX IF NOT EXISTS ix_calendar_events_calendar_id ON calendar_events (calendar_id)",
        ]
        for stmt in index_statements:
            try:
                conn.execute(sqlalchemy_text(stmt))
            except Exception as e:
                logger.debug(f"Index creation skipped: {e}")
        conn.commit()

    logger.info("Database initialized successfully")


async def close_db() -> None:
    """Close database connections."""
    global async_engine, sync_engine

    if async_engine:
        await async_engine.dispose()
        async_engine = None

    if sync_engine:
        sync_engine.dispose()
        sync_engine = None

    logger.info("Database connections closed")


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Get async database session for dependency injection."""
    if AsyncSessionLocal is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")

    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


def get_sync_session() -> Session:
    """Get sync database session for migrations and setup."""
    if sync_engine is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")

    return Session(sync_engine)


from contextlib import asynccontextmanager


@asynccontextmanager
async def get_session_context():
    """
    Get async database session as context manager.

    Use this for non-dependency injection scenarios (e.g., startup code).

    Usage:
        async with get_session_context() as session:
            # use session
    """
    if AsyncSessionLocal is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")

    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
