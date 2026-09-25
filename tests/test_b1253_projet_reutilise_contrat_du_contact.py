"""B-1253 : B-1238 avait donné au projet réutilisé un second contrat (clé
« ignore », success vrai) alors que le contact réutilisé rend « champs_ignores »
et success faux. Le Récap réel, qui ne lit que « champs_ignores », disait
« 1 déjà existant(s) » sans dire que rien n'avait été écrit. Revue du diff,
passe 4."""

import json

import pytest
from app.services.execution_truth import summarize_executions
from app.services.memory_tools import execute_create_project


@pytest.mark.asyncio
async def test_un_projet_reutilise_suit_le_contrat_du_contact(db_session):
    await execute_create_project({"name": "Site Web"}, db_session)
    brut = await execute_create_project(
        {"name": "Site Web", "status": "completed", "budget": 1200}, db_session,
    )
    resultat = json.loads(brut)
    assert resultat.get("already_existed") is True, resultat
    assert resultat.get("success") is False, resultat
    assert set(resultat.get("champs_ignores", [])) == {"statut", "budget"}, resultat
    assert "Ne dis pas" in resultat.get("message", ""), resultat

    recap = summarize_executions([("create_project", brut, False)])
    assert recap and "rien n'a été écrit" in recap, recap


@pytest.mark.asyncio
async def test_un_projet_redit_a_l_identique_reste_un_succes(db_session):
    await execute_create_project({"name": "Site Web"}, db_session)
    resultat = json.loads(await execute_create_project({"name": "Site Web"}, db_session))
    assert resultat.get("success") is True and not resultat.get("champs_ignores"), resultat
