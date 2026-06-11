"""
Alembic migrations environment for THÉRÈSE v2.

Configured for SQLModel with sync SQLite.
"""

import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import pool
from sqlmodel import SQLModel

# Add app to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import all models to ensure they're registered with SQLModel.metadata
from app.config import settings  # noqa: E402
from app.models import entities, entities_agents  # noqa: F401, E402
from app.services import audit  # noqa: F401, E402 - ActivityLog

# Alembic Config object
config = context.config

# Override sqlalchemy.url with our settings
config.set_main_option("sqlalchemy.url", f"sqlite:///{settings.db_path}")

# Configure Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# SQLModel metadata for autogenerate support
target_metadata = SQLModel.metadata


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well. By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=True,  # SQLite batch mode for ALTER TABLE
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.
    """
    # US-014 : engine conscient du chiffrement (engine_from_config ne sait
    # pas poser la clé SQLCipher)
    connectable = _make_engine(poolclass=pool.NullPool)

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=True,  # SQLite batch mode for ALTER TABLE
        )

        with context.begin_transaction():
            context.run_migrations()


# US-015 : pré-vol avant toute migration.
# 1. DB NEUVE (aucune table métier) : la chaîne de migrations historique n'est
#    pas déroulable depuis zéro (les DB ont toujours été créées par create_all).
#    On bootstrap donc comme l'app : create_all depuis les modèles, source de
#    vérité unique du schéma.
# 2. DB legacy (tables présentes, pas d'alembic_version) : déjà au schéma
#    courant -> estampille, sinon upgrade head recréerait des tables existantes.
from app.models.database import ensure_alembic_stamp  # noqa: E402


def _make_engine(**kwargs):
    """US-014 : engine adapté à l'état de la base (claire ou SQLCipher).

    Revue adversariale : une DB NEUVE naît chiffrée si le chiffrement est
    actif (avant, make db-migrate sur dossier vierge créait un therese.db en
    CLAIR, contredisant la promesse « jamais en clair en silence »).
    """
    from pathlib import Path as _Path

    from app.models.database import (
        _db_key_pragma,
        db_encryption_enabled,
        db_is_encrypted,
    )
    from sqlalchemy import create_engine, event

    db_exists = _Path(str(settings.db_path)).exists()
    use_cipher = db_is_encrypted(settings.db_path) or (
        not db_exists and db_encryption_enabled()
    )
    if use_cipher:
        import sqlcipher3

        kwargs["module"] = sqlcipher3.dbapi2
    engine = create_engine(f"sqlite:///{settings.db_path}", **kwargs)
    if use_cipher:
        @event.listens_for(engine, "connect")
        def _set_key(dbapi_conn, _record):
            cursor = dbapi_conn.cursor()
            cursor.execute(_db_key_pragma())
            cursor.close()
    return engine


def _bootstrap_if_new() -> None:
    from sqlalchemy import inspect

    engine = _make_engine()
    try:
        if "contacts" not in inspect(engine).get_table_names():
            SQLModel.metadata.create_all(engine)
    finally:
        engine.dispose()


# Pas d'effet de bord en mode offline (génération SQL) : ni création de
# fichier DB, ni estampille.
if not context.is_offline_mode():
    _bootstrap_if_new()
    # Revue adversariale US-015 : les migrations ad-hoc AVANT l'estampille,
    # sinon une DB legacy serait marquée head sans le schéma de head.
    from app.models.database import apply_adhoc_migrations  # noqa: E402

    apply_adhoc_migrations(settings.db_path)
    ensure_alembic_stamp(settings.db_path)

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
