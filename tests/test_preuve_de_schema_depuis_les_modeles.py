"""B-398 (cycle 4) : la preuve de schéma qui autorise le re-estampillage Alembic
énumérait neuf noms de tables en dur. Les noms viennent des modèles : une table
renommée ou ajoutée au sous-système ne peut plus rendre la preuve muette."""

from __future__ import annotations

from sqlmodel import SQLModel


def test_les_tables_prouvees_sont_celles_des_modeles():
    from app.models import entities, entities_sync
    from app.models.database import tables_de_planning, tables_de_synchronisation

    assert set(tables_de_synchronisation()) == {
        m.__tablename__
        for m in (entities_sync.ProjectSyncRoot, entities_sync.ProjectSyncEntry, entities_sync.SyncPlan, entities_sync.SyncOperation)
    }
    assert set(tables_de_planning()) == {
        m.__tablename__
        for m in (entities.TaskSchedule, entities.TaskDependency, entities.PlanningResource, entities.TaskAllocation, entities.PlanningSnapshot)
    }


def test_chaque_table_prouvee_existe_dans_les_metadonnees():
    from app.models.database import tables_de_planning, tables_de_synchronisation

    for table in tables_de_synchronisation() + tables_de_planning():
        assert table in SQLModel.metadata.tables, table
