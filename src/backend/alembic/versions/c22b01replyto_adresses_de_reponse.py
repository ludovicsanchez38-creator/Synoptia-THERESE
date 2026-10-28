"""B-1296 : adresses de réponse, y compris après lecture hors ligne."""
import sqlalchemy as sa
from alembic import op

revision = 'c22b01replyto'
down_revision = 'f2a3b4c5d6e7'
branch_labels = None
depends_on = None


def upgrade() -> None:
    inspecteur = sa.inspect(op.get_bind())
    if 'email_messages' in inspecteur.get_table_names() and 'reply_to_emails' not in {
        c['name'] for c in inspecteur.get_columns('email_messages')
    }:
        op.add_column('email_messages', sa.Column('reply_to_emails', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('email_messages', 'reply_to_emails')
