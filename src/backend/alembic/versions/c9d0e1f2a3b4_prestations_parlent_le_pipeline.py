"""Les prestations parlent la langue du pipeline (P-132).

Révision de données : aucune colonne. Les phases d'une prestation deviennent
des étapes du pipeline, par une correspondance injective, donc réversible :
piste -> discovery, gagne -> signature, perdue -> lost, en_cours -> delivery,
terminee -> archive ; proposition ne bouge pas.

Le démarrage de l'application fait la même réécriture
(`migrer_les_phases_de_prestation`, app/models/database.py), puisque
l'application empaquetée ne lance jamais `alembic upgrade head`. La
correspondance est recopiée ici à dessein : une révision ne dépend pas du
code applicatif, qui change après elle.

Revision ID: c9d0e1f2a3b4
Revises: b8c9d0e1f2a3
"""

import sqlalchemy as sa
from alembic import op

revision = "c9d0e1f2a3b4"
down_revision = "b8c9d0e1f2a3"
branch_labels = None
depends_on = None

VERS_LE_PIPELINE = {
    "piste": "discovery",
    "gagne": "signature",
    "perdue": "lost",
    "en_cours": "delivery",
    "terminee": "archive",
}


def _table_presente(table: str) -> bool:
    return table in sa.inspect(op.get_bind()).get_table_names()


def _reecrire_les_phases(correspondance: dict[str, str]) -> None:
    # Aucune révision ne crée la table : elle naît de create_all ou du
    # démarrage. Une base sans prestation n'a rien à migrer.
    if not _table_presente("prestations"):
        return
    anciennes = list(correspondance)
    cas = " ".join(f"WHEN :a{i} THEN :n{i}" for i in range(len(anciennes)))
    dans = ", ".join(f":a{i}" for i in range(len(anciennes)))
    parametres: dict[str, str] = {}
    for i, ancienne in enumerate(anciennes):
        parametres[f"a{i}"] = ancienne
        parametres[f"n{i}"] = correspondance[ancienne]
    # Un seul UPDATE : aucune valeur réécrite n'est relue par une autre
    # branche. La clause WHERE rend la révision idempotente et laisse
    # `updated_at` intact.
    op.get_bind().execute(
        sa.text(f"UPDATE prestations SET phase = CASE phase {cas} END WHERE phase IN ({dans})"),
        parametres,
    )


def upgrade() -> None:
    _reecrire_les_phases(VERS_LE_PIPELINE)


def downgrade() -> None:
    _reecrire_les_phases({etape: ancienne for ancienne, etape in VERS_LE_PIPELINE.items()})
    # « Perdu » n'existait pas avant cette révision : une fiche perdue retrouve
    # l'étape qui voulait dire « perdu ou terminé ».
    if _table_presente("contacts"):
        op.get_bind().execute(sa.text("UPDATE contacts SET stage = 'archive' WHERE stage = 'lost'"))
