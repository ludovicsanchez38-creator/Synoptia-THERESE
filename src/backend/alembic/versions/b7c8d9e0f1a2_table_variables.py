"""table variables (chantier 4 Variables V1, design V4 11/07/2026)

Revision ID: b7c8d9e0f1a2
Revises: a1b2c3d4e5f7
Create Date: 2026-07-11 10:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
import sqlmodel.sql.sqltypes
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'b7c8d9e0f1a2'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Idempotent : la table peut déjà exister via apply_adhoc_migrations
    # (chemin desktop) ou create_all (base neuve) - même filet que les
    # révisions précédentes.
    bind = op.get_bind()
    existing = bind.execute(
        sa.text(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='variables'"
        )
    ).fetchone()
    if existing:
        return
    op.create_table(
        'variables',
        sa.Column('id', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('name', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('kind', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('value', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('description', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    with op.batch_alter_table('variables', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_variables_name'), ['name'], unique=True)


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('variables', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_variables_name'))
    op.drop_table('variables')
