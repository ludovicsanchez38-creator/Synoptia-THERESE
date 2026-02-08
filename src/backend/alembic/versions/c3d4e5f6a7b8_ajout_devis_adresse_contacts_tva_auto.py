"""Ajout devis, adresse contacts et TVA auto

Ajoute :
- address (str, nullable) sur la table contacts
- document_type (str, default "facture") sur la table invoices
- tva_applicable (bool, default True) sur la table invoices

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-02-08 10:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'c3d4e5f6a7b8'
down_revision: Union[str, None] = 'b2c3d4e5f6a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Ajout des champs devis/avoir, adresse contacts et TVA auto-entrepreneur."""

    # =============================================
    # CONTACTS - Champ adresse postale
    # =============================================

    with op.batch_alter_table("contacts") as batch_op:
        batch_op.add_column(sa.Column("address", sa.String(), nullable=True))

    # =============================================
    # INVOICES - Type de document et TVA applicable
    # =============================================

    with op.batch_alter_table("invoices") as batch_op:
        batch_op.add_column(sa.Column(
            "document_type", sa.String(),
            nullable=False, server_default="facture",
        ))
        batch_op.add_column(sa.Column(
            "tva_applicable", sa.Boolean(),
            nullable=False, server_default="1",
        ))
        batch_op.create_index("ix_invoices_document_type", ["document_type"])


def downgrade() -> None:
    """Suppression des champs devis/avoir, adresse contacts et TVA."""

    with op.batch_alter_table("invoices") as batch_op:
        batch_op.drop_index("ix_invoices_document_type")
        batch_op.drop_column("tva_applicable")
        batch_op.drop_column("document_type")

    with op.batch_alter_table("contacts") as batch_op:
        batch_op.drop_column("address")
