"""R5 : contact facultatif et provenance des activités.

Revision ID: e1f2a3b4c5d6
Revises: d0e1f2a3b4c5
"""
import sqlalchemy as sa
from alembic import op

revision = 'e1f2a3b4c5d6'
down_revision = 'd0e1f2a3b4c5'
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    if 'activities' not in sa.inspect(bind).get_table_names():
        return
    colonnes = {c['name']: c for c in sa.inspect(bind).get_columns('activities')}
    if colonnes['contact_id']['nullable'] and {'project_id', 'conversation_id', 'execution_id'} <= colonnes.keys():
        return
    with op.batch_alter_table('activities') as batch:
        batch.alter_column('contact_id', existing_type=sa.String(), nullable=True)
        for nom, cible in [('project_id', 'projects.id'), ('conversation_id', 'conversations.id')]:
            if nom not in colonnes:
                batch.add_column(sa.Column(nom, sa.String(), nullable=True))
                batch.create_foreign_key(f'fk_activities_{nom}', cible.split('.')[0], [nom], ['id'],
                    ondelete='SET NULL' if nom == 'conversation_id' else None)
                batch.create_index(f'ix_activities_{nom}', [nom])
        if 'execution_id' not in colonnes:
            batch.add_column(sa.Column('execution_id', sa.String(), nullable=True))
            batch.create_index('ix_activities_execution_id', ['execution_id'], unique=True)


def downgrade() -> None:
    # Une activité sans contact ne peut pas être rétrogradée sans perte.
    if op.get_bind().execute(sa.text('SELECT count(*) FROM activities WHERE contact_id IS NULL')).scalar():
        raise ValueError('Des traces sans contact empêchent une rétrogradation sans perte.')
    with op.batch_alter_table('activities') as batch:
        for nom in ('execution_id', 'conversation_id', 'project_id'):
            batch.drop_column(nom)
        batch.alter_column('contact_id', existing_type=sa.String(), nullable=False)
