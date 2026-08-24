"""Les quatre tables de project.sync (0.45, phase 3 du séquencement).

Contrats issus du design V2.1 :
- quatre tables NOUVELLES, zéro colonne ajoutée (create_all n'ajoute pas de
  colonnes aux tables existantes sur une base packagée) ;
- alembic/env.py doit importer les modèles, sinon un bootstrap NEUF par
  Alembic créerait un schéma sans elles (finding 7 : `processing` manquait
  déjà) ;
- l'autorité est formalisée : project_sync_entries porte le dernier snapshot
  APPLIQUÉ (une entrée naît d'une opération réussie, jamais du rattachement),
  files porte l'identité et le périmètre réellement indexés.
"""

from pathlib import Path

import pytest
from sqlalchemy import inspect

RACINE = Path(__file__).resolve().parent.parent


TABLES_SYNC = {
    "project_sync_roots",
    "project_sync_entries",
    "sync_plans",
    "sync_operations",
}


class TestLesTablesExistent:
    def test_les_modeles_declarent_les_quatre_tables(self):
        import app.models.entities_sync  # noqa: F401
        from sqlmodel import SQLModel

        declarees = set(SQLModel.metadata.tables.keys())
        assert declarees >= TABLES_SYNC, TABLES_SYNC - declarees

    @pytest.mark.asyncio
    async def test_create_all_les_cree_sur_une_base_existante(self, client):
        """Le chemin réel d'une base packagée 0.44 : create_all au démarrage
        crée les tables manquantes."""
        from app.models.database import get_sync_connection

        with get_sync_connection() as conn:
            presentes = set(inspect(conn).get_table_names())

        assert presentes >= TABLES_SYNC, TABLES_SYNC - presentes

    def test_env_alembic_importe_tous_les_modeles(self):
        """Un bootstrap neuf par Alembic doit voir TOUTES les tables - env.py
        n'importait ni processing ni les modèles sync."""
        source = (RACINE / "src/backend/alembic/env.py").read_text(encoding="utf-8")

        assert "entities_sync" in source
        assert "processing" in source

    def test_database_importe_les_modeles_avant_create_all(self):
        """create_all ne crée que ce que la métadonnée connaît : les modules
        doivent être importés par database.py, pas par hasard d'un routeur."""
        source = (RACINE / "src/backend/app/models/database.py").read_text(encoding="utf-8")

        assert "entities_sync" in source
        assert "processing" in source


class TestLeContratDesColonnes:
    def test_l_etat_de_reference_porte_l_identite_et_l_empreinte(self):
        from app.models.entities_sync import ProjectSyncEntry

        colonnes = set(ProjectSyncEntry.model_fields.keys())
        assert {
            "project_id", "chemin", "file_id", "taille", "mtime_ns",
            "sha256", "generation_racine",
        } <= colonnes

    def test_le_plan_porte_sa_generation_de_racine(self):
        from app.models.entities_sync import SyncPlan

        assert "generation_racine" in SyncPlan.model_fields

    def test_l_operation_porte_reprise_et_identite_prevue(self):
        from app.models.entities_sync import SyncOperation

        colonnes = set(SyncOperation.model_fields.keys())
        assert {
            "plan_id", "type", "chemin", "file_id_prevu", "empreinte_prevue",
            "empreinte_reelle", "etat", "erreur", "attempt_count",
            "last_attempt_at",
        } <= colonnes

    def test_la_racine_est_unique_et_porte_son_volume(self):
        from app.models.entities_sync import ProjectSyncRoot

        colonnes = set(ProjectSyncRoot.model_fields.keys())
        assert {"project_id", "racine", "volume_id", "generation"} <= colonnes
