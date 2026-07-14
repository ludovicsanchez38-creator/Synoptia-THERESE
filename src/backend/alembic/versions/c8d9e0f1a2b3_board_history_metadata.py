"""Historique Board reconstructible : sources web et usage de synthèse.

Revision ID: c8d9e0f1a2b3
Revises: b7c8d9e0f1a2
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c8d9e0f1a2b3"
down_revision: str | Sequence[str] | None = "b7c8d9e0f1a2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "board_decisions",
        sa.Column("web_sources", sa.Text(), nullable=False, server_default="[]"),
    )
    op.add_column(
        "board_decisions",
        sa.Column("synthesis_usage", sa.Text(), nullable=False, server_default="{}"),
    )


def downgrade() -> None:
    op.drop_column("board_decisions", "synthesis_usage")
    op.drop_column("board_decisions", "web_sources")
