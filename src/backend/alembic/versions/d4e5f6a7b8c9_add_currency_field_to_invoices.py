"""Ajout du champ currency sur les factures

Ajoute :
- currency (str, default "EUR") sur la table invoices

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-03-15 10:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'd4e5f6a7b8c9'
down_revision: Union[str, None] = 'c3d4e5f6a7b8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Ajout du champ currency sur la table invoices."""
    with op.batch_alter_table("invoices") as batch_op:
        batch_op.add_column(sa.Column(
            "currency", sa.String(),
            nullable=False, server_default="EUR",
        ))


def downgrade() -> None:
    """Suppression du champ currency."""
    with op.batch_alter_table("invoices") as batch_op:
        batch_op.drop_column("currency")
