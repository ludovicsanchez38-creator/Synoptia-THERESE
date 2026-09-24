"""B-1188 : synchro tableur (route servie POST /api/crm/sync/import, mêmes
upsert que POST /api/crm/sync, crm.py:1413-1500 et :1524-1610) : une cellule
vide remplace le titre enregistré par « Sans nom » (projet) ou « Sans titre »
(tâche, livrable), et efface dates, description, budget et notes.

Attendu : arbitrage du 24/09 (docs/plans/2026-09-24-arbitrages-par-delegation.md:20-26)
« La synchronisation du tableur n'efface pas. Le tableur fait foi pour ce
qu'il dit, pas pour ce qu'il tait : une cellule vide ou une valeur inconnue ne
remplace pas la valeur enregistrée » ; B-1083 à l'import de fichier : « une
colonne absente, vide ou inconnue ne change rien à la fiche existante ».

NB : l'ancre du candidat (crm_sync.py:276-282) est dans CRMSyncService, que
rien n'appelle en production ; le code servi est crm_utils.py.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from sqlmodel import select

ECHEANCE = datetime(2026, 10, 15, 9, 0, tzinfo=UTC)
ACHEVEE = datetime(2026, 9, 20, 17, 0, tzinfo=UTC)


async def _poser():
    from app.models import database as db_module
    from app.models.entities import Deliverable, Project, Task

    async with db_module.AsyncSessionLocal() as s:
        s.add(Project(id="p-b1188", name="Chantier Martin", description="Rénovation cuisine",
                      budget=12000.0, notes="Acompte reçu", status="active"))
        s.add(Task(id="t-b1188", title="Relancer le plombier", description="Avant jeudi",
                   due_date=ECHEANCE, completed_at=ACHEVEE, status="done", priority="high"))
        await s.commit()
        s.add(Deliverable(id="d-b1188", title="Plan de la cuisine", description="Version 2",
                          project_id="p-b1188", status="en_cours"))
        await s.commit()


async def _lire():
    from app.models import database as db_module
    from app.models.entities import Deliverable, Project, Task

    async with db_module.AsyncSessionLocal() as s:
        p = (await s.execute(select(Project).where(Project.id == "p-b1188"))).scalar_one()
        t = (await s.execute(select(Task).where(Task.id == "t-b1188"))).scalar_one()
        d = (await s.execute(select(Deliverable).where(Deliverable.id == "d-b1188"))).scalar_one()
        return (
            {"name": p.name, "description": p.description, "budget": p.budget, "notes": p.notes},
            {"title": t.title, "description": t.description, "due_date": t.due_date,
             "completed_at": t.completed_at},
            {"title": d.title, "description": d.description, "project_id": d.project_id},
        )


async def _synchro_lignes_reduites_a_l_id(client):
    resp = await client.post("/api/crm/sync/import", json={
        "projects": [{"ID": "p-b1188"}],
        "tasks": [{"ID": "t-b1188"}],
        "deliverables": [{"ID": "d-b1188"}],
    })
    assert resp.status_code == 200, resp.text
    stats = resp.json()["stats"]
    assert (stats["projects_updated"], stats["tasks_updated"], stats["deliverables_updated"]) == (1, 1, 1), stats


@pytest.mark.asyncio
async def test_une_cellule_titre_vide_ne_remplace_pas_le_titre_par_une_valeur_inventee(client):
    await _poser()
    avant = await _lire()
    await _synchro_lignes_reduites_a_l_id(client)
    apres = await _lire()

    titres = (apres[0]["name"], apres[1]["title"], apres[2]["title"])
    assert titres == ("Chantier Martin", "Relancer le plombier", "Plan de la cuisine"), (
        f"titres avant={(avant[0]['name'], avant[1]['title'], avant[2]['title'])} ; après={titres}"
    )


@pytest.mark.asyncio
async def test_une_cellule_vide_n_efface_pas_dates_description_budget_notes(client):
    await _poser()
    avant = await _lire()
    await _synchro_lignes_reduites_a_l_id(client)
    apres = await _lire()

    efface = {
        f"{entite}.{champ}": (avant[i][champ], apres[i][champ])
        for i, entite in enumerate(("projet", "tache", "livrable"))
        for champ in avant[i]
        if avant[i][champ] is not None and apres[i][champ] is None
    }
    assert not efface, f"champs effacés par une cellule vide : {efface}"


@pytest.mark.asyncio
async def test_temoin_le_statut_et_le_projet_sont_bien_proteges(client):
    """Témoin B-1108/B-1125 : sur les mêmes lignes, statut, priorité et projet
    du livrable ne bougent pas (la règle existe, elle s'arrête là)."""
    from app.models import database as db_module
    from app.models.entities import Deliverable, Project, Task

    await _poser()
    await _synchro_lignes_reduites_a_l_id(client)
    async with db_module.AsyncSessionLocal() as s:
        p = await s.get(Project, "p-b1188")
        t = await s.get(Task, "t-b1188")
        d = await s.get(Deliverable, "d-b1188")
        assert (p.status, t.status, t.priority, d.status, d.project_id) == (
            "active", "done", "high", "en_cours", "p-b1188"
        )


@pytest.mark.asyncio
async def test_une_tache_rouverte_depuis_le_tableur_perd_sa_date_de_fin(client):
    """B-1212 : régression de B-1188. Une tâche repassée « à faire » dans le
    tableur, cellule CompletedAt vide, gardait sa date de fin ; la route des
    tâches l'efface dès que le statut n'est plus « done » (tasks.py)."""
    await _poser()
    resp = await client.post("/api/crm/sync/import", json={
        "tasks": [{"ID": "t-b1188", "Status": "todo"}],
    })
    assert resp.status_code == 200, resp.text
    _, tache, _ = await _lire()
    assert tache["completed_at"] is None, tache


@pytest.mark.asyncio
async def test_la_regle_de_date_de_fin_vaut_dans_les_deux_sens_et_a_la_creation(client):
    """B-1231 : B-1212 n'appliquait que la moitié de la règle de la route des
    tâches. Une tâche passée « done » par le tableur sans CompletedAt restait
    sans date de fin ; une tâche NEUVE non terminée gardait la sienne."""
    from app.models import database as db_module
    from app.models.entities import Task

    async with db_module.AsyncSessionLocal() as s:
        s.add(Task(id="t-b1231", title="Appeler", status="todo", priority="high"))
        await s.commit()
    resp = await client.post("/api/crm/sync/import", json={"tasks": [
        {"ID": "t-b1231", "Status": "done"},
        {"ID": "t-b1231-neuve", "Title": "Neuve", "Status": "todo", "CompletedAt": "2026-09-01T10:00:00"},
    ]})
    assert resp.status_code == 200, resp.text
    async with db_module.AsyncSessionLocal() as s:
        faite = (await s.execute(select(Task).where(Task.id == "t-b1231"))).scalar_one()
        neuve = (await s.execute(select(Task).where(Task.id == "t-b1231-neuve"))).scalar_one()
    assert (faite.completed_at is not None, neuve.completed_at) == (True, None), (faite.completed_at, neuve.completed_at)
