"""Journal local des accords de transfert cloud."""
import sqlalchemy as sa
from alembic import op

revision = 't4consent01'
down_revision = 'c22b02facture'
branch_labels = None
depends_on = None


def upgrade() -> None:
    if 'cloud_consents' not in sa.inspect(op.get_bind()).get_table_names():
        op.create_table('cloud_consents',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('event_id', sa.String(), unique=True),
            sa.Column('purpose', sa.String(), nullable=False),
            sa.Column('provider', sa.String(), nullable=False),
            sa.Column('granted', sa.Boolean(), nullable=False),
            sa.Column('text_version', sa.String(), nullable=False),
            sa.Column('occurred_at', sa.String(), nullable=False),
            sa.Column('recorded_at', sa.String(), nullable=False),
            sa.Column('data_categories', sa.String(), nullable=False),
            sa.Column('source', sa.String(), nullable=False))


def downgrade() -> None:
    op.drop_table('cloud_consents')
