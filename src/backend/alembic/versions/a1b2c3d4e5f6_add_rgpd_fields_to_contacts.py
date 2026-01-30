"""add_rgpd_fields_to_contacts

Revision ID: a1b2c3d4e5f6
Revises: ea76e4e8871d
Create Date: 2026-01-28 16:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = 'ea76e4e8871d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add RGPD fields to contacts table
    op.add_column('contacts', sa.Column('rgpd_base_legale', sa.String(), nullable=True))
    op.add_column('contacts', sa.Column('rgpd_date_collecte', sa.DateTime(), nullable=True))
    op.add_column('contacts', sa.Column('rgpd_date_expiration', sa.DateTime(), nullable=True))
    op.add_column('contacts', sa.Column('rgpd_consentement', sa.Boolean(), nullable=False, server_default='0'))


def downgrade() -> None:
    op.drop_column('contacts', 'rgpd_consentement')
    op.drop_column('contacts', 'rgpd_date_expiration')
    op.drop_column('contacts', 'rgpd_date_collecte')
    op.drop_column('contacts', 'rgpd_base_legale')
