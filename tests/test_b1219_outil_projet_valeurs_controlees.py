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


@pytest.mark.asyncio
@pytest.mark.parametrize("statut, attendu", [("terminé", "completed"), ("En pause", "on_hold"), ("annulé", "cancelled")])
async def test_un_statut_francais_est_traduit_comme_au_tableur(db_session, statut, attendu):
    """B-1232 : B-1219 remplaçait en silence tout statut inconnu par « active »,
    y compris « terminé », que la table du tableur sait traduire."""
    resultat = json.loads(await execute_create_project({"name": f"Chantier {statut}", "status": statut}, db_session))
    projet = (await db_session.execute(select(Project).where(Project.id == resultat["project_id"]))).scalar_one()
    assert projet.status == attendu, projet.status


@pytest.mark.asyncio
async def test_une_valeur_ecartee_est_dite_au_modele(db_session):
    """B-1232 : un statut ou un budget écarté l'est sans le dire ; le résultat
    de l'outil le signale pour que le modèle ne l'annonce pas comme retenu."""
    resultat = json.loads(await execute_create_project(
        {"name": "Chantier flou", "status": "gelé", "budget": "beaucoup"}, db_session,
    ))
    assert "ecarte" in resultat or "écarté" in json.dumps(resultat, ensure_ascii=False), resultat


@pytest.mark.asyncio
async def test_un_projet_homonyme_dit_ce_qu_il_n_applique_pas(db_session):
    """B-1238 : sur un projet existant, l'outil rendait already_existed en
    ignorant sans le dire le statut, le budget et la description demandés."""
    await execute_create_project({"name": "Site Web"}, db_session)
    resultat = json.loads(await execute_create_project(
        {"name": "Site Web", "status": "completed", "budget": 1200, "description": "Refonte"}, db_session,
    ))
    assert resultat.get("already_existed") is True, resultat
    assert set(resultat.get("ignore", [])) == {"statut", "budget", "description"}, resultat


@pytest.mark.asyncio
async def test_la_commande_projet_dit_ce_qu_elle_ecarte(db_session):
    """B-1238 : /projet ignorait la clé « ecarte » de l'outil (B-1232)."""
    from app.services.slash_commands import execute_slash_command

    reponse = await execute_slash_command("projet", "Chantier flou statut=gelé", db_session)
    assert "gelé" in reponse and "active" in reponse, reponse


def test_l_import_de_fichier_n_accepte_pas_un_budget_infini():
    """B-1238 : quatrième porte du budget infini (B-1219) ; et « inf » en entier
    levait OverflowError."""
    from app.services.crm_import import _parse_value

    assert _parse_value("1e999", "float") is None
    assert _parse_value("inf", "int") is None
