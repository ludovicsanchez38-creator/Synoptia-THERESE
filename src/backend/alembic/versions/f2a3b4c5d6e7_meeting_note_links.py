"""R5 : portée héritée des anciennes notes, sans les recopier.

Revision ID: f2a3b4c5d6e7
Revises: e1f2a3b4c5d6
"""
import sqlalchemy as sa
from alembic import op

revision = 'f2a3b4c5d6e7'
down_revision = 'e1f2a3b4c5d6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # La même requête idempotente que le bootstrap desktop, sans données hors SQL.
    from app.models.meeting_note_migration import LIER_NOTES
    tables = set(sa.inspect(op.get_bind()).get_table_names())
    if {'activities', 'calendar_events'} <= tables:
        op.execute(sa.text(LIER_NOTES))


def downgrade() -> None:
    # Garder une portée correcte ne perd aucune donnée et évite une fuite.
    pass
