"""B-1108, B-1125 : la synchronisation du tableur n'efface pas.

Règle arbitrée le 24/09 (docs/plans/2026-09-24-arbitrages-par-delegation.md) :
le tableur fait foi pour ce qu'il dit, pas pour ce qu'il tait. Une cellule
vide ou une valeur inconnue ne remplace pas le client d'un projet, ni le
statut (ou la priorité) d'un projet, d'une tâche ou d'un livrable. Les
statuts accentués ou en anglais sont reconnus. Un livrable sans projet est
écarté avec un message, sans faire tomber la synchronisation (500 : la
colonne project_id est NOT NULL et l'échec éclatait au commit final).
"""

from __future__ import annotations

import pytest
from app.models.entities import Contact, Deliverable, Project, Task
from app.services.crm_utils import upsert_deliverable_from_import, upsert_project, upsert_task
from httpx import AsyncClient
from sqlmodel import select


async def _client_et_projet(session, statut: str = "completed") -> None:
    session.add(Contact(id="client-b1108", first_name="Alice", last_name="Martin"))
    session.add(Project(id="projet-b1108", name="Chantier", contact_id="client-b1108", status=statut))
    await session.commit()


# --- Projets (B-1108) -------------------------------------------------------


@pytest.mark.asyncio
async def test_une_cellule_client_vide_ne_delie_pas_le_projet(db_session):
    await _client_et_projet(db_session)
    projet, cree = await upsert_project(
        db_session, {"ID": "projet-b1108", "ClientID": "", "Name": "Chantier", "Status": "completed"}, safe_get=True
    )
    assert not cree
    assert projet.contact_id == "client-b1108"


@pytest.mark.asyncio
@pytest.mark.parametrize("saisi", ["", "Gelé"])
async def test_un_statut_de_projet_vide_ou_inconnu_ne_remplace_rien(db_session, saisi: str):
    await _client_et_projet(db_session, statut="completed")
    projet, _ = await upsert_project(
        db_session, {"ID": "projet-b1108", "ClientID": "client-b1108", "Name": "Chantier", "Status": saisi}, safe_get=True
    )
    assert projet.status == "completed"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("saisi", "attendu"),
    [("Terminé", "completed"), ("En cours", "active"), ("En pause", "on_hold"), ("Annulé", "cancelled"),
     ("Livré", "completed"), ("done", "completed"), ("On hold", "on_hold"), ("canceled", "cancelled")],
)
async def test_un_statut_de_projet_accentue_ou_anglais_est_reconnu(db_session, saisi: str, attendu: str):
    await _client_et_projet(db_session, statut="active" if attendu != "active" else "on_hold")
    projet, _ = await upsert_project(
        db_session, {"ID": "projet-b1108", "ClientID": "client-b1108", "Name": "Chantier", "Status": saisi}, safe_get=True
    )
    assert projet.status == attendu


@pytest.mark.asyncio
async def test_un_nouveau_projet_au_statut_inconnu_est_actif(db_session):
    projet, cree = await upsert_project(db_session, {"ID": "projet-neuf", "Name": "Neuf", "Status": "Gelé"}, safe_get=True)
    assert cree
    assert projet.status == "active"


# --- Tâches (B-1125) --------------------------------------------------------


async def _tache(session, statut: str = "done", priorite: str = "high") -> None:
    session.add(Task(id="tache-b1125", title="Relancer", status=statut, priority=priorite))
    await session.commit()


@pytest.mark.asyncio
@pytest.mark.parametrize("saisi", ["", "Gelée"])
async def test_un_statut_de_tache_vide_ou_inconnu_ne_remplace_rien(db_session, saisi: str):
    await _tache(db_session, statut="done")
    tache, cree = await upsert_task(db_session, {"ID": "tache-b1125", "Title": "Relancer", "Status": saisi}, safe_get=True)
    assert not cree
    assert tache.status == "done"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("saisi", "attendu"),
    [("Terminée", "done"), ("Fait", "done"), ("En cours", "in_progress"), ("À faire", "todo"),
     ("Annulée", "cancelled"), ("completed", "done"), ("In progress", "in_progress")],
)
async def test_un_statut_de_tache_accentue_ou_anglais_est_reconnu(db_session, saisi: str, attendu: str):
    await _tache(db_session, statut="cancelled" if attendu != "cancelled" else "todo")
    tache, _ = await upsert_task(db_session, {"ID": "tache-b1125", "Title": "Relancer", "Status": saisi}, safe_get=True)
    assert tache.status == attendu


@pytest.mark.asyncio
@pytest.mark.parametrize("saisi", ["", "Très vite"])
async def test_une_priorite_vide_ou_inconnue_ne_remplace_rien(db_session, saisi: str):
    await _tache(db_session, priorite="high")
    tache, _ = await upsert_task(db_session, {"ID": "tache-b1125", "Title": "Relancer", "Priority": saisi}, safe_get=True)
    assert tache.priority == "high"


@pytest.mark.asyncio
async def test_une_nouvelle_tache_au_statut_inconnu_est_a_faire(db_session):
    tache, cree = await upsert_task(db_session, {"ID": "tache-neuve", "Title": "Neuve", "Status": "Gelée"}, safe_get=True)
    assert cree
    assert tache.status == "todo"


# --- Livrables sans projet (B-1125) -----------------------------------------


@pytest.mark.asyncio
async def test_une_cellule_projet_vide_ne_detache_pas_un_livrable(db_session):
    await _client_et_projet(db_session)
    db_session.add(Deliverable(id="livrable-b1125", project_id="projet-b1108", title="Plan", status="valide"))
    await db_session.commit()
    livrable, _ = await upsert_deliverable_from_import(
        db_session, {"ID": "livrable-b1125", "ProjectID": "", "Title": "Plan v2"}, safe_get=True
    )
    assert livrable.project_id == "projet-b1108"
    assert livrable.title == "Plan v2"


@pytest.mark.asyncio
async def test_un_livrable_sans_projet_est_ecarte_sans_faire_tomber_la_synchro(client: AsyncClient, db_session):
    await _client_et_projet(db_session)
    reponse = await client.post(
        "/api/crm/sync/import",
        json={
            "deliverables": [
                {"ID": "livrable-orphelin", "Title": "Sans projet"},
                {"ID": "livrable-sain", "ProjectID": "projet-b1108", "Title": "Avec projet"},
            ],
            "tasks": [{"ID": "tache-saine", "Title": "Après les livrables"}],
        },
    )
    assert reponse.status_code == 200, reponse.text
    corps = reponse.json()
    assert any("livrable-orphelin" in erreur for erreur in corps["stats"]["errors"]), corps
    ids = set((await db_session.execute(select(Deliverable.id))).scalars())
    assert ids == {"livrable-sain"}
    assert await db_session.get(Task, "tache-saine") is not None


@pytest.mark.asyncio
async def test_un_client_inconnu_ne_delie_pas_le_projet(db_session):
    await _client_et_projet(db_session)
    projet, _ = await upsert_project(
        db_session, {"ID": "projet-b1108", "ClientID": "client-absent", "Name": "Chantier"}, safe_get=True
    )
    assert projet.contact_id == "client-b1108"


@pytest.mark.asyncio
async def test_un_projet_inconnu_ne_detache_pas_un_livrable(db_session):
    await _client_et_projet(db_session)
    db_session.add(Deliverable(id="livrable-b1125", project_id="projet-b1108", title="Plan", status="valide"))
    await db_session.commit()
    livrable, _ = await upsert_deliverable_from_import(
        db_session, {"ID": "livrable-b1125", "ProjectID": "projet-absent", "Title": "Plan"}, safe_get=True
    )
    assert livrable.project_id == "projet-b1108"


# --- Synchronisation Google (crm_sync), même règle pour les livrables ----------


@pytest.mark.asyncio
@pytest.mark.parametrize(("saisi", "attendu"), [("Validé", "valide"), ("En révision", "en_revision"), ("", "en_revision"), ("Gelé", "en_revision")])
async def test_la_synchro_google_des_livrables_suit_la_meme_regle(db_session, saisi: str, attendu: str):
    from unittest.mock import MagicMock

    from app.services.crm_sync import CRMSyncService, SyncStats

    await _client_et_projet(db_session)
    db_session.add(Deliverable(id="livrable-g", project_id="projet-b1108", title="Plan", status="en_revision"))
    await db_session.commit()
    await CRMSyncService(db_session, MagicMock())._sync_deliverables(
        [{"ID": "livrable-g", "ProjectID": "projet-b1108", "Title": "Plan", "Status": saisi}], SyncStats()
    )
    await db_session.commit()
    db_session.expire_all()
    assert (await db_session.get(Deliverable, "livrable-g")).status == attendu


@pytest.mark.asyncio
async def test_un_client_cree_dans_la_meme_synchro_est_bien_lie(db_session):
    """Régression à éviter : la synchro crée les clients puis les projets avant
    un seul commit ; le contrôle d'existence doit voir le client en attente."""
    db_session.add(Contact(id="client-neuf", first_name="Nina", last_name="Roux"))
    projet, cree = await upsert_project(
        db_session, {"ID": "projet-neuf", "ClientID": "client-neuf", "Name": "Neuf"}, safe_get=True
    )
    assert cree
    assert projet.contact_id == "client-neuf"
