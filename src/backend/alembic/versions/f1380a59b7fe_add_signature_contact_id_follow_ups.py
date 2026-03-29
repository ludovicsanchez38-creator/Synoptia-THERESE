"""add signature, contact_id, follow_ups

Revision ID: f1380a59b7fe
Revises: d4e5f6a7b8c9
Create Date: 2026-03-29 19:00:08.842012

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes


# revision identifiers, used by Alembic.
revision: str = 'f1380a59b7fe'
down_revision: Union[str, Sequence[str], None] = 'd4e5f6a7b8c9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 1. Table email_follow_ups
    op.create_table('email_follow_ups',
        sa.Column('id', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('email_message_id', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('contact_id', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column('due_date', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('note', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column('status', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('created_at', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.ForeignKeyConstraint(['contact_id'], ['contacts.id']),
        sa.ForeignKeyConstraint(['email_message_id'], ['email_messages.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    with op.batch_alter_table('email_follow_ups', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_email_follow_ups_contact_id'), ['contact_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_email_follow_ups_email_message_id'), ['email_message_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_email_follow_ups_status'), ['status'], unique=False)

    # 2. Colonne signature_html sur email_accounts
    with op.batch_alter_table('email_accounts', schema=None) as batch_op:
        batch_op.add_column(sa.Column('signature_html', sqlmodel.sql.sqltypes.AutoString(), nullable=True))

    # 3. Colonne contact_id sur email_messages
    with op.batch_alter_table('email_messages', schema=None) as batch_op:
        batch_op.add_column(sa.Column('contact_id', sqlmodel.sql.sqltypes.AutoString(), nullable=True))
        batch_op.create_index(batch_op.f('ix_email_messages_contact_id'), ['contact_id'], unique=False)
        batch_op.create_foreign_key('fk_email_messages_contact_id', 'contacts', ['contact_id'], ['id'])


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('email_messages', schema=None) as batch_op:
        batch_op.drop_constraint('fk_email_messages_contact_id', type_='foreignkey')
        batch_op.drop_index(batch_op.f('ix_email_messages_contact_id'))
        batch_op.drop_column('contact_id')

    with op.batch_alter_table('email_accounts', schema=None) as batch_op:
        batch_op.drop_column('signature_html')

    with op.batch_alter_table('email_follow_ups', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_email_follow_ups_status'))
        batch_op.drop_index(batch_op.f('ix_email_follow_ups_email_message_id'))
        batch_op.drop_index(batch_op.f('ix_email_follow_ups_contact_id'))

    op.drop_table('email_follow_ups')
