"""Date du premier envoi d'un devis ou d'une facture (P-139).

Revision ID: b8c9d0e1f2a3
Revises: a7b8c9d0e1f2
"""

import sqlalchemy as sa
from alembic import op

revision = "b8c9d0e1f2a3"
down_revision = "a7b8c9d0e1f2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    colonnes = {c["name"] for c in sa.inspect(op.get_bind()).get_columns("invoices")}
    # Les migrations ad-hoc du démarrage ont pu la poser avant Alembic.
    if "sent_at" not in colonnes:
        op.add_column("invoices", sa.Column("sent_at", sa.DateTime(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("invoices") as batch:
        batch.drop_column("sent_at")
