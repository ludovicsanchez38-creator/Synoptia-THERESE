"""Provenance des images, brouillons et sections rédigées par l'IA."""
import sqlalchemy as sa
from alembic import op

revision = 't4marque02'
down_revision = 't4consent01'
branch_labels = None
depends_on = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    tables = inspector.get_table_names()
    if 'ai_generations' not in tables:
        op.create_table('ai_generations',
            sa.Column('id', sa.String(), primary_key=True),
            sa.Column('kind', sa.String(), nullable=False),
            sa.Column('owner_id', sa.String(), nullable=False),
            sa.Column('provider', sa.String(), nullable=False),
            sa.Column('model', sa.String(), nullable=False),
            sa.Column('created_at', sa.String(), nullable=False),
            sa.Column('provenance', sa.String(), nullable=False))
    if 'email_messages' in tables and 'ai_generation_id' not in {c['name'] for c in inspector.get_columns('email_messages')}:
        op.add_column('email_messages', sa.Column('ai_generation_id', sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column('email_messages', 'ai_generation_id')
    op.drop_table('ai_generations')
