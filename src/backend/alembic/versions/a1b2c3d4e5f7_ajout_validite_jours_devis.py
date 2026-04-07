"""ajout validite_jours devis

Ajoute le champ validite_jours (int, nullable) sur la table invoices
pour la duree de validite des devis.

Revision ID: a1b2c3d4e5f7
Revises: f1380a59b7fe
Create Date: 2026-04-07 10:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f7'
down_revision: Union[str, Sequence[str], None] = 'f1380a59b7fe'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Ajout du champ validite_jours sur invoices."""
    with op.batch_alter_table("invoices") as batch_op:
        batch_op.add_column(sa.Column(
            "validite_jours", sa.Integer(),
            nullable=True,
        ))


def downgrade() -> None:
    """Suppression du champ validite_jours."""
    with op.batch_alter_table("invoices") as batch_op:
        batch_op.drop_column("validite_jours")
