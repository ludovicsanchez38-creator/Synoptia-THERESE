"""Ajoute le socle de planning PERT/Gantt.

Revision ID: a7b8c9d0e1f2
Revises: f6a7b8c9d0e1
"""

import sqlalchemy as sa
from alembic import op

revision = "a7b8c9d0e1f2"
down_revision = "f6a7b8c9d0e1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "task_schedules",
        sa.Column("task_id", sa.String(), nullable=False),
        sa.Column("duration_optimistic_minutes", sa.Integer(), nullable=True),
        sa.Column("duration_likely_minutes", sa.Integer(), nullable=True),
        sa.Column("duration_pessimistic_minutes", sa.Integer(), nullable=True),
        sa.Column("constraint_type", sa.String(), nullable=True),
        sa.Column("constraint_at", sa.DateTime(), nullable=True),
        sa.Column("progress_percent", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_milestone", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("billing_milestone", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint(
            "duration_optimistic_minutes IS NULL OR duration_optimistic_minutes > 0",
            name="ck_task_schedule_duration_optimistic_positive",
        ),
        sa.CheckConstraint(
            "duration_likely_minutes IS NULL OR duration_likely_minutes > 0",
            name="ck_task_schedule_duration_likely_positive",
        ),
        sa.CheckConstraint(
            "duration_pessimistic_minutes IS NULL OR duration_pessimistic_minutes > 0",
            name="ck_task_schedule_duration_pessimistic_positive",
        ),
        sa.CheckConstraint(
            "duration_optimistic_minutes IS NULL OR duration_likely_minutes IS NULL "
            "OR duration_optimistic_minutes <= duration_likely_minutes",
            name="ck_task_schedule_duration_optimistic_likely_order",
        ),
        sa.CheckConstraint(
            "duration_likely_minutes IS NULL OR duration_pessimistic_minutes IS NULL "
            "OR duration_likely_minutes <= duration_pessimistic_minutes",
            name="ck_task_schedule_duration_likely_pessimistic_order",
        ),
        sa.CheckConstraint(
            "constraint_type IS NULL OR constraint_type IN "
            "('start_no_earlier', 'finish_no_later', 'fixed_start', 'fixed_finish')",
            name="ck_task_schedule_constraint_type",
        ),
        sa.CheckConstraint(
            "(constraint_type IS NULL AND constraint_at IS NULL) OR "
            "(constraint_type IS NOT NULL AND constraint_at IS NOT NULL)",
            name="ck_task_schedule_constraint_pair",
        ),
        sa.CheckConstraint(
            "progress_percent BETWEEN 0 AND 100",
            name="ck_task_schedule_progress",
        ),
        sa.ForeignKeyConstraint(["task_id"], ["tasks.id"]),
        sa.PrimaryKeyConstraint("task_id"),
    )

    op.create_table(
        "task_dependencies",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("predecessor_task_id", sa.String(), nullable=False),
        sa.Column("successor_task_id", sa.String(), nullable=False),
        sa.Column(
            "kind", sa.String(), nullable=False, server_default="finish_start"
        ),
        sa.Column("lag_minutes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint(
            "predecessor_task_id <> successor_task_id",
            name="ck_task_dependency_distinct_tasks",
        ),
        sa.CheckConstraint(
            "kind IN ('finish_start', 'start_start', 'finish_finish', 'start_finish')",
            name="ck_task_dependency_kind",
        ),
        sa.CheckConstraint(
            "lag_minutes BETWEEN -525600 AND 525600",
            name="ck_task_dependency_lag",
        ),
        sa.ForeignKeyConstraint(["predecessor_task_id"], ["tasks.id"]),
        sa.ForeignKeyConstraint(["successor_task_id"], ["tasks.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "predecessor_task_id",
            "successor_task_id",
            "kind",
            name="uq_task_dependency_edge",
        ),
    )
    op.create_index(
        "ix_task_dependencies_predecessor_task_id",
        "task_dependencies",
        ["predecessor_task_id"],
    )
    op.create_index(
        "ix_task_dependencies_successor_task_id",
        "task_dependencies",
        ["successor_task_id"],
    )

    op.create_table(
        "planning_resources",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("project_id", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("kind", sa.String(), nullable=False, server_default="person"),
        sa.Column("capacity_percent", sa.Integer(), nullable=False, server_default="100"),
        sa.Column("timezone", sa.String(), nullable=False, server_default="Europe/Paris"),
        sa.Column("working_hours_json", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint(
            "capacity_percent BETWEEN 1 AND 100",
            name="ck_planning_resource_capacity",
        ),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "project_id", "name", name="uq_planning_resource_name"
        ),
    )
    op.create_index(
        "ix_planning_resources_project_id", "planning_resources", ["project_id"]
    )

    op.create_table(
        "task_allocations",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("task_id", sa.String(), nullable=False),
        sa.Column("resource_id", sa.String(), nullable=False),
        sa.Column("allocation_percent", sa.Integer(), nullable=False, server_default="100"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint(
            "allocation_percent BETWEEN 1 AND 100",
            name="ck_task_allocation_percent",
        ),
        sa.ForeignKeyConstraint(["resource_id"], ["planning_resources.id"]),
        sa.ForeignKeyConstraint(["task_id"], ["tasks.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("task_id", "resource_id", name="uq_task_allocation"),
    )
    op.create_index("ix_task_allocations_task_id", "task_allocations", ["task_id"])
    op.create_index(
        "ix_task_allocations_resource_id", "task_allocations", ["resource_id"]
    )

    op.create_table(
        "planning_snapshots",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("project_id", sa.String(), nullable=False),
        sa.Column("engine_version", sa.String(), nullable=False),
        sa.Column("input_hash", sa.String(), nullable=False),
        sa.Column("calculated_at", sa.DateTime(), nullable=False),
        sa.Column("state", sa.String(), nullable=False),
        sa.Column("warnings_json", sa.String(), nullable=False, server_default="[]"),
        sa.Column("missing_fields_json", sa.String(), nullable=False, server_default="[]"),
        sa.Column("result_json", sa.String(), nullable=False),
        sa.CheckConstraint(
            "state IN ('complete', 'incomplete', 'invalid')",
            name="ck_planning_snapshot_state",
        ),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "project_id",
            "engine_version",
            "input_hash",
            name="uq_planning_snapshot_input",
        ),
    )
    op.create_index(
        "ix_planning_snapshots_project_id", "planning_snapshots", ["project_id"]
    )
    op.create_index(
        "ix_planning_snapshots_input_hash", "planning_snapshots", ["input_hash"]
    )
    op.create_index(
        "ix_planning_snapshots_calculated_at",
        "planning_snapshots",
        ["calculated_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_planning_snapshots_calculated_at", table_name="planning_snapshots")
    op.drop_index("ix_planning_snapshots_input_hash", table_name="planning_snapshots")
    op.drop_index("ix_planning_snapshots_project_id", table_name="planning_snapshots")
    op.drop_table("planning_snapshots")
    op.drop_index("ix_task_allocations_resource_id", table_name="task_allocations")
    op.drop_index("ix_task_allocations_task_id", table_name="task_allocations")
    op.drop_table("task_allocations")
    op.drop_index("ix_planning_resources_project_id", table_name="planning_resources")
    op.drop_table("planning_resources")
    op.drop_index(
        "ix_task_dependencies_successor_task_id", table_name="task_dependencies"
    )
    op.drop_index(
        "ix_task_dependencies_predecessor_task_id", table_name="task_dependencies"
    )
    op.drop_table("task_dependencies")
    op.drop_table("task_schedules")
