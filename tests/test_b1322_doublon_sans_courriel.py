"""B-1322 : sans courriel, la recherche d'un contact existant comparait prénom
et nom avec les accents et champ par champ : « Helene » face à « Hélène », ou
« /contact Jean Pierre Martin » face à « Jean Pierre » « Martin », créait un
doublon. Jumeau de B-1311 et B-1316. Lecteur γ, passe 7."""

import json

import pytest
from app.services.memory_tools import execute_create_contact


@pytest.mark.asyncio
async def test_un_accent_manquant_ne_cree_pas_de_doublon(db_session):
    await execute_create_contact({"first_name": "Hélène", "last_name": "Exemple"}, db_session)
    resultat = json.loads(await execute_create_contact({"first_name": "Helene", "last_name": "Exemple"}, db_session))
    assert resultat.get("already_existed") is True, resultat


@pytest.mark.asyncio
async def test_un_prenom_compose_ne_cree_pas_de_doublon(db_session):
    from app.services.slash_commands import execute_slash_command

    await execute_create_contact({"first_name": "Jean Pierre", "last_name": "Martin"}, db_session)
    reponse = await execute_slash_command("contact", "Jean Pierre Martin", db_session)
    assert "déjà en mémoire" in reponse, reponse


@pytest.mark.asyncio
async def test_deux_personnes_differentes_restent_deux(db_session):
    await execute_create_contact({"first_name": "Jean", "last_name": "Martin"}, db_session)
    resultat = json.loads(await execute_create_contact({"first_name": "Jeanne", "last_name": "Martin"}, db_session))
    assert not resultat.get("already_existed"), resultat


@pytest.mark.asyncio
async def test_un_tiret_ne_cree_pas_de_doublon(db_session):
    """B-1331 : « Jean-Pierre » face à « Jean Pierre » créait un doublon (tiret
    non replié). Lecteurs ζ et ε, passe 8."""
    await execute_create_contact({"first_name": "Jean Pierre", "last_name": "Martin"}, db_session)
    resultat = json.loads(await execute_create_contact({"first_name": "Jean-Pierre", "last_name": "Martin"}, db_session))
    assert resultat.get("already_existed") is True, resultat
    assert "nom" not in resultat.get("champs_ignores", []), resultat


@pytest.mark.asyncio
async def test_le_nom_complet_dans_le_seul_prenom_n_est_pas_signale(db_session):
    """B-1337 : régression de B-1322. Nom complet saisi dans le seul prénom :
    fiche retrouvée puis annoncée « nom ignoré ». Lecteur ε, passe 8."""
    await execute_create_contact({"first_name": "Marie", "last_name": "Exemple"}, db_session)
    resultat = json.loads(await execute_create_contact({"first_name": "Marie Exemple"}, db_session))
    assert resultat.get("already_existed") is True, resultat
    assert "nom" not in resultat.get("champs_ignores", []), resultat
