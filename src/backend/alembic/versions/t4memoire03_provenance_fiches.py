"""Conserver l'origine documentaire des fiches, sans présumer celle des anciennes."""
import sqlalchemy as sa
from alembic import op

revision = 't4memoire03'
down_revision = 't4marque02'
branch_labels = None
depends_on = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if 'memory_cards' in inspector.get_table_names() and 'provenance_documents' not in {
        c['name'] for c in inspector.get_columns('memory_cards')
    }:
        op.add_column('memory_cards', sa.Column('provenance_documents', sa.String(),
                                              nullable=False, server_default='inconnue'))


def downgrade() -> None:
    op.drop_column('memory_cards', 'provenance_documents')
