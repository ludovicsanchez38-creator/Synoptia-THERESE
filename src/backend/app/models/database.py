"""
THÉRÈSE v2 - Database Connection

SQLite database setup with SQLModel.
"""

import logging
import sqlite3
from pathlib import Path
from typing import AsyncGenerator

from app.config import settings
from sqlalchemy import event
from sqlalchemy import text as sqlalchemy_text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import Session, SQLModel, create_engine

logger = logging.getLogger(__name__)

# Sync engine for SQLModel compatibility
sync_engine = None

# Async engine for FastAPI
async_engine = None

# Session factory
AsyncSessionLocal = None


INVOICE_LEGACY_COLUMN_DEFINITIONS: dict[str, str] = {
    "currency": "TEXT DEFAULT 'EUR'",
    "payment_terms": "TEXT",
    "payment_method": "TEXT",
    "late_penalty_rate": "REAL",
    "legal_mentions": "TEXT",
    "converted_from_id": "TEXT",
    "validite_jours": "INTEGER",
    "payment_date": "TIMESTAMP",
}


def ensure_invoice_currency_column(db_path: Path | None) -> bool:
    """Ajoute la colonne invoices.currency si elle manque sur une DB legacy."""
    return "currency" in ensure_invoice_legacy_columns(db_path, columns=("currency",))


def ensure_invoice_legacy_columns(
    db_path: Path | None,
    columns: tuple[str, ...] | None = None,
) -> list[str]:
    """Ajoute les colonnes invoices manquantes sur une DB legacy."""
    if db_path is None or not db_path.exists():
        return []

    target_columns = columns or tuple(INVOICE_LEGACY_COLUMN_DEFINITIONS.keys())
    added_columns: list[str] = []

    with sqlite3.connect(str(db_path)) as conn:
        cursor = conn.execute("PRAGMA table_info(invoices)")
        existing_columns = {row[1] for row in cursor.fetchall()}
        if not existing_columns:
            return []

        for column_name in target_columns:
            if column_name in existing_columns:
                continue

            column_definition = INVOICE_LEGACY_COLUMN_DEFINITIONS[column_name]
            conn.execute(f"ALTER TABLE invoices ADD COLUMN {column_name} {column_definition}")
            added_columns.append(column_name)

        if added_columns:
            conn.commit()
            logger.info(
                "Migration auto : colonnes invoices ajoutées (%s)",
                ", ".join(added_columns),
            )

    return added_columns


# US-015 : tête Alembic épinglée. Une DB bootstrapée par create_all + les
# migrations ad-hoc d'init_db/main.py EST au schéma de cette révision : on
# l'estampille pour qu'Alembic devienne l'unique voie d'évolution du schéma.
# Le test tests/test_alembic_stamp.py vérifie que cette constante suit la
# vraie tête de src/backend/alembic/versions (épinglée en dur pour que
# l'app PACKAGÉE puisse estampiller sans embarquer le dossier alembic/).
ALEMBIC_HEAD_REVISION = "a1b2c3d4e5f7"


def ensure_alembic_stamp(db_path) -> None:
    """Estampille la DB à la tête Alembic si elle n'a pas d'alembic_version.

    Idempotent. Ne touche pas une DB déjà suivie par Alembic (révision plus
    ancienne incluse : `alembic upgrade head` la fera avancer normalement).
    Ne stamp JAMAIS une DB vide (sans tables métier) : elle doit être créée
    par les migrations ou par create_all d'abord.
    """
    import sqlite3
    from contextlib import closing
    from pathlib import Path as _Path

    if not db_path or not _Path(str(db_path)).exists():
        return
    try:
        with closing(sqlite3.connect(str(db_path))) as conn:
            has_tables = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='contacts'"
            ).fetchone()
            if not has_tables:
                return
            has_stamp = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='alembic_version'"
            ).fetchone()
            if has_stamp:
                return
            conn.execute(
                "CREATE TABLE alembic_version ("
                "version_num VARCHAR(32) NOT NULL, "
                "CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num))"
            )
            conn.execute(
                "INSERT INTO alembic_version (version_num) VALUES (?)",
                (ALEMBIC_HEAD_REVISION,),
            )
            conn.commit()
            logger.info(f"US-015 : DB estampillée Alembic {ALEMBIC_HEAD_REVISION}")
    except Exception as e:
        logger.warning(f"Estampillage Alembic échoué : {e}")


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
    from app.models import (
        entities,  # noqa: F401
        entities_agents,  # noqa: F401 - Agent system tables
    )
    from app.services import audit  # noqa: F401 - ActivityLog model

    SQLModel.metadata.create_all(sync_engine)

    # Auto-migration : ajouter les colonnes manquantes aux tables existantes
    ensure_invoice_legacy_columns(settings.db_path)

    with sync_engine.connect() as conn:
        alter_statements = [
            # BUG-068 : colonne mode ajoutée dans BoardDecisionDB mais absente des DB existantes
            "ALTER TABLE board_decisions ADD COLUMN mode VARCHAR DEFAULT 'cloud'",
        ]
        for stmt in alter_statements:
            try:
                conn.execute(sqlalchemy_text(stmt))
            except Exception as e:
                logger.debug("Migration colonne deja existante: %s", e)  # déjà existante
        conn.commit()

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
            "CREATE INDEX IF NOT EXISTS ix_invoices_converted_from_id ON invoices (converted_from_id)",
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

    # US-015 : estampiller la DB à la tête Alembic. Le bootstrap ci-dessus
    # (create_all + colonnes/index ad-hoc) amène la DB AU schéma courant ;
    # l'estampille fait d'Alembic l'unique voie d'évolution future
    # (`make db-migrate` fonctionne désormais aussi sur une DB legacy).
    ensure_alembic_stamp(settings.db_path)

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


def get_sync_connection():
    """Get a sync connection from the singleton engine (reuses WAL/cache PRAGMAs)."""
    if sync_engine is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    return sync_engine.connect()


from contextlib import asynccontextmanager  # noqa: E402


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
