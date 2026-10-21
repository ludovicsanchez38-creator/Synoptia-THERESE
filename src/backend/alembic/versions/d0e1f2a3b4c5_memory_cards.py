"""R2 : fiches et marqueurs de rejeu dans SQLCipher.

Revision ID: d0e1f2a3b4c5
Revises: c9d0e1f2a3b4
"""
import sqlalchemy as sa
from alembic import op

revision = 'd0e1f2a3b4c5'
down_revision = 'c9d0e1f2a3b4'
branch_labels = None
depends_on = None


def upgrade() -> None:
    if 'memory_cards' not in sa.inspect(op.get_bind()).get_table_names():
        op.create_table('memory_cards',
            sa.Column('id', sa.String(), primary_key=True),
            sa.Column('kind', sa.String(), nullable=False),
            sa.Column('subject', sa.String(), nullable=False),
            sa.Column('dedup_key', sa.String(), nullable=False, unique=True),
            sa.Column('title', sa.String(), nullable=False),
            sa.Column('content', sa.String(), nullable=False),
            sa.Column('reason', sa.String(), nullable=False),
            sa.Column('search_text', sa.String(), nullable=False),
            sa.Column('scope', sa.String(), nullable=False),
            sa.Column('scope_id', sa.String(), sa.ForeignKey('projects.id')),
            sa.Column('contact_id', sa.String(), sa.ForeignKey('contacts.id')),
            sa.Column('project_id', sa.String(), sa.ForeignKey('projects.id')),
            sa.Column('conversation_id', sa.String(), sa.ForeignKey('conversations.id', ondelete='SET NULL')),
            sa.Column('message_id', sa.String(), sa.ForeignKey('messages.id', ondelete='SET NULL')),
            sa.Column('author', sa.String(), nullable=False),
            sa.Column('last_author', sa.String(), nullable=False),
            sa.Column('protected', sa.Boolean(), nullable=False),
            sa.Column('state', sa.String(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.CheckConstraint("kind IN ('preference','fait','decision','correction')"),
            sa.CheckConstraint("state IN ('active','archivee')"),
            sa.CheckConstraint("scope IN ('global','project')"),
            sa.CheckConstraint("(scope = 'global' AND scope_id IS NULL) OR (scope = 'project' AND scope_id IS NOT NULL)"),
            sa.CheckConstraint("length(title) BETWEEN 1 AND 120 AND length(content) BETWEEN 1 AND 1200"),
            sa.CheckConstraint("length(reason) <= 600 AND (kind != 'decision' OR length(reason) > 0)"),
            sa.CheckConstraint('version >= 1'))
    if 'memory_card_uses' not in sa.inspect(op.get_bind()).get_table_names():
        op.create_table('memory_card_uses',
            sa.Column('id', sa.String(), primary_key=True),
            sa.Column('message_id', sa.String(), sa.ForeignKey('messages.id', ondelete='SET NULL')),
            sa.Column('card_id', sa.String(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=False),
            sa.Column('operation', sa.String(), nullable=False),
            sa.Column('blocked', sa.Boolean(), nullable=False))
    for table, columns in [('memory_cards', ('kind', 'state', 'scope', 'scope_id', 'contact_id', 'project_id')),
                           ('memory_card_uses', ('message_id', 'card_id'))]:
        for column in columns:
            op.execute(sa.text(f'CREATE INDEX IF NOT EXISTS ix_{table}_{column} ON {table} ({column})'))


def downgrade() -> None:
    op.drop_table('memory_card_uses')
    op.drop_table('memory_cards')
