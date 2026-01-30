"""add_email_category_field

Revision ID: ea76e4e8871d
Revises: 20682614d0d1
Create Date: 2026-01-28 15:02:53.065832

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ea76e4e8871d'
down_revision: Union[str, Sequence[str], None] = '20682614d0d1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - Add category field to email_messages."""
    op.add_column('email_messages', sa.Column('category', sa.String(), nullable=True))


def downgrade() -> None:
    """Downgrade schema - Remove category field from email_messages."""
    op.drop_column('email_messages', 'category')
