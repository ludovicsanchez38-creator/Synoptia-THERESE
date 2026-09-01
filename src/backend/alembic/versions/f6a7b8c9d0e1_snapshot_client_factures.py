"""Fige le destinataire des factures et devis existants.

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
"""

import sqlalchemy as sa
from alembic import op

revision = "f6a7b8c9d0e1"
down_revision = "e5f6a7b8c9d0"
branch_labels = None
depends_on = None

SNAPSHOT_COLUMNS = (
    "client_name",
    "client_company",
    "client_email",
    "client_phone",
    "client_address",
)


def _columns() -> set[str]:
    return {
        column["name"]
        for column in sa.inspect(op.get_bind()).get_columns("invoices")
    }


def upgrade() -> None:
    bind = op.get_bind()
    orphan = bind.execute(
        sa.text(
            "SELECT i.id FROM invoices i LEFT JOIN contacts c ON c.id = i.contact_id "
            "WHERE c.id IS NULL LIMIT 1"
        )
    ).fetchone()
    if orphan is not None:
        raise RuntimeError(
            "Migration des factures impossible : le contact de la pièce "
            f"{orphan[0]} est introuvable"
        )

    existing = _columns()
    for column_name in SNAPSHOT_COLUMNS:
        if column_name not in existing:
            op.add_column("invoices", sa.Column(column_name, sa.Text(), nullable=True))

    # Le contact courant est la seule source encore disponible. Une valeur
    # inventée ou vide rendrait la migration irréversible et juridiquement fausse.
    bind.execute(
        sa.text(
            """
            UPDATE invoices
            SET client_name = (
                    SELECT CASE
                        WHEN TRIM(COALESCE(c.first_name, '') || ' ' || COALESCE(c.last_name, '')) != ''
                        THEN TRIM(COALESCE(c.first_name, '') || ' ' || COALESCE(c.last_name, ''))
                        WHEN COALESCE(c.company, '') != '' THEN c.company
                        ELSE NULL
                    END
                    FROM contacts c WHERE c.id = invoices.contact_id
                ),
                client_company = (SELECT c.company FROM contacts c WHERE c.id = invoices.contact_id),
                client_email = (SELECT c.email FROM contacts c WHERE c.id = invoices.contact_id),
                client_phone = (SELECT c.phone FROM contacts c WHERE c.id = invoices.contact_id),
                client_address = (SELECT c.address FROM contacts c WHERE c.id = invoices.contact_id)
            WHERE client_name IS NULL OR TRIM(client_name) = ''
            """
        )
    )
    missing = bind.execute(
        sa.text(
            "SELECT id FROM invoices WHERE client_name IS NULL "
            "OR TRIM(client_name) = '' LIMIT 1"
        )
    ).fetchone()
    if missing is not None:
        raise RuntimeError(
            "Migration des factures incomplète : snapshot absent pour la pièce "
            f"{missing[0]}"
        )


def downgrade() -> None:
    existing = _columns()
    with op.batch_alter_table("invoices") as batch_op:
        for column_name in reversed(SNAPSHOT_COLUMNS):
            if column_name in existing:
                batch_op.drop_column(column_name)
