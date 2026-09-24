"""B-1219 : l'outil create_project du chat (et la commande /projet) contrôle le
statut et le budget.

Le statut était écrit tel quel : une valeur hors des quatre statuts rendait le
projet invisible du tableau, et un statut null tombait sur la colonne NOT NULL
(texte SQL brut rendu au modèle). Un budget infini faisait tomber la liste des
projets en erreur 500.
"""

import json
import math

import pytest
from app.models.entities import Project
from app.services.memory_tools import execute_create_project
from sqlmodel import select


@pytest.mark.asyncio
@pytest.mark.parametrize("statut", ["gelé", None, 42])
async def test_un_statut_hors_domaine_prend_le_defaut(db_session, statut):
    resultat = json.loads(await execute_create_project({"name": f"Chantier {statut}", "status": statut}, db_session))
    assert resultat.get("success") is True, resultat
    projet = (await db_session.execute(select(Project).where(Project.id == resultat["project_id"]))).scalar_one()
    assert projet.status == "active", projet.status


@pytest.mark.asyncio
@pytest.mark.parametrize("budget", [float("inf"), "1e999", "beaucoup", -5])
async def test_un_budget_illisible_ou_infini_n_est_pas_enregistre(db_session, budget):
    resultat = json.loads(await execute_create_project({"name": f"Budget {budget}", "budget": budget}, db_session))
    assert resultat.get("success") is True, resultat
    projet = (await db_session.execute(select(Project).where(Project.id == resultat["project_id"]))).scalar_one()
    assert projet.budget is None or (math.isfinite(projet.budget) and projet.budget >= 0), projet.budget


@pytest.mark.asyncio
async def test_la_route_refuse_un_budget_infini(client):
    resp = await client.post("/api/memory/projects", json={"name": "Chantier infini", "budget": "inf"})
    assert resp.status_code == 422, resp.text


@pytest.mark.asyncio
async def test_le_tableur_n_enregistre_pas_un_budget_infini(client):
    resp = await client.post("/api/crm/sync/import", json={"projects": [{"ID": "p-b1219", "Name": "Chantier", "Budget": "1e999"}]})
    assert resp.status_code == 200, resp.text
    liste = await client.get("/api/memory/projects")
    assert liste.status_code == 200, liste.text
    projet = next(p for p in liste.json() if p["id"] == "p-b1219")
    assert projet["budget"] is None, projet["budget"]
