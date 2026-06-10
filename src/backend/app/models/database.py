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

    # US-014 : db_connect pose la clé SQLCipher si la base est chiffrée
    with db_connect(db_path) as conn:
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
    from contextlib import closing
    from pathlib import Path as _Path

    if not db_path or not _Path(str(db_path)).exists():
        return
    try:
        # US-014 : db_connect pose la clé SQLCipher si la base est chiffrée
        with closing(db_connect(db_path)) as conn:
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


# ============================================================
# US-014 : chiffrement de la base au repos (SQLCipher)
# ============================================================
# therese.db est chiffrée avec SQLCipher (AES-256), clé dérivée de la clé
# maîtresse du trousseau (HKDF, cf. encryption.get_db_key_hex). Une DB claire
# existante est migrée au démarrage (sqlcipher_export + vérification).
# Échappatoire : THERESE_DB_PLAINTEXT=1 (debug / trousseau indisponible).

_db_cipher_active = False  # positionné par init_db, lu par les listeners


def db_encryption_enabled() -> bool:
    """Chiffrement au repos actif ? (US-014)"""
    import os

    return os.environ.get("THERESE_DB_PLAINTEXT") != "1"


def db_is_encrypted(db_path) -> bool:
    """Une DB SQLite claire commence par l'en-tête 'SQLite format 3'."""
    from pathlib import Path as _Path

    p = _Path(str(db_path))
    if not p.exists() or p.stat().st_size == 0:
        return False
    with open(p, "rb") as f:
        return f.read(16) != b"SQLite format 3\x00"


def _db_key_pragma() -> str:
    from app.services.encryption import get_db_key_hex

    return f"PRAGMA key = \"x'{get_db_key_hex()}'\""


def db_connect(db_path):
    """Connexion directe à therese.db (remplace les sqlite3.connect épars).

    Adaptatif : DB chiffrée -> sqlcipher3 + clé ; DB claire (échappatoire ou
    pré-migration) -> sqlite3 standard. Tous les accès hors engine DOIVENT
    passer par ici (data.py, agents.py, swarm.py, main.py, env.py).
    """

    if db_is_encrypted(db_path):
        import sqlcipher3

        conn = sqlcipher3.connect(str(db_path))
        conn.execute(_db_key_pragma())
        return conn
    return sqlite3.connect(str(db_path))


def ensure_db_encrypted(db_path) -> None:
    """Migre une DB claire existante vers SQLCipher (idempotent).

    Étapes : checkpoint WAL -> sqlcipher_export vers un fichier temporaire ->
    vérification (mêmes tables + integrity_check) -> remplacement atomique.
    La copie claire n'est PAS conservée (la garder annulerait le chiffrement
    au repos) : la vérification précède toujours le remplacement.
    """
    import os
    from contextlib import closing
    from pathlib import Path as _Path

    p = _Path(str(db_path))
    if not p.exists() or p.stat().st_size == 0 or db_is_encrypted(p):
        return

    import sqlcipher3
    from app.services.encryption import get_db_key_hex

    key_hex = get_db_key_hex()
    tmp = _Path(str(p) + ".encrypting")
    tmp.unlink(missing_ok=True)

    # Rapatrier le WAL avant export (sinon transactions récentes perdues)
    with closing(sqlite3.connect(str(p))) as conn:
        conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        expected_tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }

    with closing(sqlcipher3.connect(str(p))) as conn:
        conn.execute(
            f"ATTACH DATABASE ? AS encrypted KEY \"x'{key_hex}'\"", (str(tmp),)
        )
        conn.execute("SELECT sqlcipher_export('encrypted')")
        conn.execute("DETACH DATABASE encrypted")

    # Vérifier le chiffré AVANT de remplacer la claire
    with closing(sqlcipher3.connect(str(tmp))) as conn:
        conn.execute(f"PRAGMA key = \"x'{key_hex}'\"")
        got_tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
        integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
    if got_tables != expected_tables or integrity != "ok":
        tmp.unlink(missing_ok=True)
        raise RuntimeError(
            "Migration SQLCipher : vérification échouée "
            f"(tables {len(got_tables)}/{len(expected_tables)}, integrity={integrity}). "
            "La base claire est intacte."
        )

    os.replace(tmp, p)
    for suffix in ("-wal", "-shm"):
        _Path(str(p) + suffix).unlink(missing_ok=True)
    logger.info("US-014 : base migrée vers SQLCipher (chiffrement au repos actif)")


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

    # US-014 : chiffrement au repos. Migrer une DB claire existante, puis
    # brancher les deux engines sur sqlcipher3 (clé posée en PREMIER pragma
    # de chaque connexion). Échec de clé/migration = fatal et explicite
    # (démarrer en clair en silence trahirait la promesse de souveraineté ;
    # échappatoire documentée : THERESE_DB_PLAINTEXT=1).
    global _db_cipher_active
    _db_cipher_active = False
    engine_kwargs: dict = {}
    if db_encryption_enabled():
        try:
            ensure_db_encrypted(settings.db_path)
            import aiosqlite.core as _aiosqlite_core
            import sqlcipher3

            # aiosqlite importe sqlite3 en dur : on substitue le module DBAPI
            # SQLCipher (même API) pour le moteur async.
            _aiosqlite_core.sqlite3 = sqlcipher3.dbapi2
            engine_kwargs["module"] = sqlcipher3.dbapi2
            _db_cipher_active = True
        except Exception:
            logger.error(
                "US-014 : chiffrement de la base indisponible. Démarrage REFUSÉ "
                "pour ne pas écrire en clair en silence. Débloquer le trousseau "
                "ou poser THERESE_DB_PLAINTEXT=1 (assumé, base en clair)."
            )
            raise

    # Create sync engine for table creation
    sync_engine = create_engine(
        get_database_url(async_mode=False),
        echo=settings.debug,
        connect_args={"check_same_thread": False},
        **engine_kwargs,
    )

    # PERF-005 + Phase 3: SQLite PRAGMAs optimises
    @event.listens_for(sync_engine, "connect")
    def _set_sqlite_pragmas(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        if _db_cipher_active:
            cursor.execute(_db_key_pragma())  # DOIT précéder tout autre accès
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
        if _db_cipher_active:
            cursor.execute(_db_key_pragma())  # DOIT précéder tout autre accès
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
