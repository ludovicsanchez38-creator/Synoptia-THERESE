"""Tables project.sync (0.45) - roots, entries, plans, operations.

IDEMPOTENTE : `create_all()` tourne à chaque démarrage packagé et peut avoir
créé ces tables AVANT un `alembic upgrade` (challenge du design V2.1,
correction 5). Chaque création est gardée par l'inspecteur.

Revision ID: e5f6a7b8c9d0
Revises: d9e0f1a2b3c4
"""
import sqlalchemy as sa
from alembic import op

revision = "e5f6a7b8c9d0"
down_revision = "d9e0f1a2b3c4"
branch_labels = None
depends_on = None


def _absente(nom: str) -> bool:
    return nom not in sa.inspect(op.get_bind()).get_table_names()


def _index_absent(nom: str) -> bool:
    lignes = op.get_bind().execute(sa.text(
        "SELECT name FROM sqlite_master WHERE type='index' AND name=:nom"
    ), {"nom": nom}).fetchall()
    return not lignes


def upgrade() -> None:
    if _absente("project_sync_roots"):
        op.create_table(
            "project_sync_roots",
            sa.Column("id", sa.String(), primary_key=True),
            sa.Column("project_id", sa.String(), nullable=False, unique=True),
            sa.Column("racine", sa.String(), nullable=False),
            sa.Column("volume_id", sa.Integer(), nullable=False),
            sa.Column("generation", sa.Integer(), nullable=False),
            sa.Column("detachee", sa.Boolean(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
        )
        op.create_index(
            "ix_project_sync_roots_project_id", "project_sync_roots",
            ["project_id"], unique=True,
        )

    if _absente("project_sync_entries"):
        op.create_table(
            "project_sync_entries",
            sa.Column("id", sa.String(), primary_key=True),
            sa.Column("project_id", sa.String(), nullable=False),
            sa.Column("chemin", sa.String(), nullable=False),
            sa.Column("file_id", sa.String(), nullable=False),
            sa.Column("taille", sa.Integer(), nullable=False),
            sa.Column("mtime_ns", sa.Integer(), nullable=False),
            sa.Column("sha256", sa.String(), nullable=False),
            sa.Column("generation_racine", sa.Integer(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.UniqueConstraint(
                "project_id", "chemin", name="uq_sync_entry_projet_chemin"
            ),
        )
        op.create_index(
            "ix_project_sync_entries_project_id", "project_sync_entries",
            ["project_id"],
        )
        op.create_index(
            "ix_project_sync_entries_chemin", "project_sync_entries", ["chemin"]
        )
    if _absente("sync_plans"):
        op.create_table(
            "sync_plans",
            sa.Column("id", sa.String(), primary_key=True),
            sa.Column("project_id", sa.String(), nullable=False),
            sa.Column("generation_racine", sa.Integer(), nullable=False),
            sa.Column("etat", sa.String(), nullable=False),
            sa.Column("nb_indexer", sa.Integer(), nullable=False),
            sa.Column("nb_reindexer", sa.Integer(), nullable=False),
            sa.Column("nb_retirer", sa.Integer(), nullable=False),
            sa.Column("nb_conflits", sa.Integer(), nullable=False),
            sa.Column("nb_inchanges", sa.Integer(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
        )
        op.create_index("ix_sync_plans_project_id", "sync_plans", ["project_id"])
        op.create_index("ix_sync_plans_etat", "sync_plans", ["etat"])
    if _absente("sync_operations"):
        op.create_table(
            "sync_operations",
            sa.Column("id", sa.String(), primary_key=True),
            sa.Column("plan_id", sa.String(), nullable=False),
            sa.Column("type", sa.String(), nullable=False),
            sa.Column("chemin", sa.String(), nullable=False),
            sa.Column("file_id_prevu", sa.String(), nullable=True),
            sa.Column("empreinte_prevue", sa.String(), nullable=True),
            sa.Column("empreinte_reelle", sa.String(), nullable=True),
            sa.Column("etat", sa.String(), nullable=False),
            sa.Column("erreur", sa.String(), nullable=True),
            sa.Column("attempt_count", sa.Integer(), nullable=False),
            sa.Column("last_attempt_at", sa.DateTime(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
        )
        op.create_index("ix_sync_operations_plan_id", "sync_operations", ["plan_id"])
        op.create_index("ix_sync_operations_etat", "sync_operations", ["etat"])
        op.create_index(
            "ix_sync_operations_plan_etat", "sync_operations", ["plan_id", "etat"]
        )

    # Passe 3 de revue : l'index partiel vivait dans le guard « table
    # absente » - une base déjà estampillée ne le recevait jamais. Garde
    # idempotente PROPRE : il se crée même sur des tables existantes.
    if not _absente("project_sync_roots") and _index_absent(
        "uq_sync_root_racine_active"
    ):
        op.create_index(
            "uq_sync_root_racine_active", "project_sync_roots",
            ["racine"], unique=True,
            sqlite_where=sa.text("detachee = 0"),
        )


def downgrade() -> None:
    for table in (
        "sync_operations", "sync_plans", "project_sync_entries", "project_sync_roots"
    ):
        if not _absente(table):
            op.drop_table(table)
