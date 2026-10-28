"""Adresse de facturation, date de prestation et bon de commande."""

import sqlalchemy as sa
from alembic import op

revision = "c22b02facture"
down_revision = "c22b01replyto"
branch_labels = None
depends_on = None


def upgrade() -> None:
    inspecteur = sa.inspect(op.get_bind())
    if "invoices" not in inspecteur.get_table_names():
        return
    existantes = {c["name"] for c in inspecteur.get_columns("invoices")}
    for nom, type_ in [
        ("client_billing_address", sa.Text()),
        ("service_date", sa.DateTime()),
        ("purchase_order", sa.Text()),
    ]:
        if nom not in existantes:
            op.add_column("invoices", sa.Column(nom, type_, nullable=True))


def downgrade() -> None:
    for nom in ("client_billing_address", "service_date", "purchase_order"):
        op.drop_column("invoices", nom)
