"""
Alembic migrations environment for THÉRÈSE v2.

Configured for SQLModel with sync SQLite.
"""

import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool
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
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

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


def _bootstrap_if_new() -> None:
    from sqlalchemy import create_engine, inspect

    engine = create_engine(f"sqlite:///{settings.db_path}")
    try:
        if "contacts" not in inspect(engine).get_table_names():
            SQLModel.metadata.create_all(engine)
    finally:
        engine.dispose()


_bootstrap_if_new()
ensure_alembic_stamp(settings.db_path)

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
