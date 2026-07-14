"""Historique Atelier reconstructible après redémarrage.

Revision ID: d9e0f1a2b3c4
Revises: c8d9e0f1a2b3
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "d9e0f1a2b3c4"
down_revision: str | Sequence[str] | None = "c8d9e0f1a2b3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    for column_name in (
        "run_phase",
        "plan",
        "test_results",
        "explanation",
        "events",
        "agent_outputs",
        "base_branch",
        "commit_hash",
    ):
        op.add_column("agent_tasks", sa.Column(column_name, sa.Text(), nullable=True))


def downgrade() -> None:
    for column_name in (
        "commit_hash",
        "base_branch",
        "agent_outputs",
        "events",
        "explanation",
        "test_results",
        "plan",
        "run_phase",
    ):
        op.drop_column("agent_tasks", column_name)
