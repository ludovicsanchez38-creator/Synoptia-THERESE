"""P-039 : la révision Alembic crée et retire réellement le socle planning."""

import importlib.util
from pathlib import Path

from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, inspect

ROOT = Path(__file__).resolve().parent.parent
MIGRATION = (
    ROOT
    / "src/backend/alembic/versions/a7b8c9d0e1f2_planning_pert_gantt.py"
)
PLANNING_TABLES = {
    "task_schedules",
    "task_dependencies",
    "planning_resources",
    "task_allocations",
    "planning_snapshots",
}


def _load_migration():
    spec = importlib.util.spec_from_file_location("planning_migration", MIGRATION)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_upgrade_et_downgrade_reels(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'planning.db'}")
    migration = _load_migration()
    with engine.begin() as connection:
        connection.exec_driver_sql(
            "CREATE TABLE projects (id VARCHAR NOT NULL PRIMARY KEY)"
        )
        connection.exec_driver_sql(
            "CREATE TABLE tasks (id VARCHAR NOT NULL PRIMARY KEY, "
            "project_id VARCHAR REFERENCES projects(id))"
        )
        migration.op = Operations(MigrationContext.configure(connection))
        migration.upgrade()

        inspector = inspect(connection)
        assert set(inspector.get_table_names()) >= PLANNING_TABLES
        assert {
            "duration_optimistic_minutes",
            "duration_likely_minutes",
            "duration_pessimistic_minutes",
            "constraint_type",
            "constraint_at",
            "progress_percent",
            "is_milestone",
            "billing_milestone",
        } <= {
            column["name"]
            for column in inspector.get_columns("task_schedules")
        }
        assert "uq_task_dependency_edge" in {
            constraint["name"]
            for constraint in inspector.get_unique_constraints(
                "task_dependencies"
            )
        }

        migration.downgrade()
        assert not (
            PLANNING_TABLES & set(inspect(connection).get_table_names())
        )
    engine.dispose()
