"""add_email_priority_fields

Revision ID: 20682614d0d1
Revises: 977c5c3cff46
Create Date: 2026-01-28 13:47:06.409977

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20682614d0d1'
down_revision: Union[str, Sequence[str], None] = '977c5c3cff46'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - Add priority fields to email_messages."""
    # Add priority fields
    op.add_column('email_messages', sa.Column('priority', sa.String(), nullable=True))
    op.add_column('email_messages', sa.Column('priority_score', sa.Integer(), nullable=True))
    op.add_column('email_messages', sa.Column('priority_reason', sa.String(), nullable=True))

    # Add index on priority for fast filtering
    op.create_index(op.f('ix_email_messages_priority'), 'email_messages', ['priority'], unique=False)


def downgrade() -> None:
    """Downgrade schema - Remove priority fields from email_messages."""
    # Drop index
    op.drop_index(op.f('ix_email_messages_priority'), table_name='email_messages')

    # Drop columns
    op.drop_column('email_messages', 'priority_reason')
    op.drop_column('email_messages', 'priority_score')
    op.drop_column('email_messages', 'priority')
