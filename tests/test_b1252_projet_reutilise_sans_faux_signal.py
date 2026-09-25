"""B-1252 : régression de B-1238. `/projet Nom` tapé une seconde fois répondait
« Non appliqué : status. » alors qu'aucune option n'avait été donnée : la
commande injectait le statut par défaut, et l'outil comptait comme demandée
toute valeur non vide, même égale à celle du projet. Revue du diff, passe 4."""

import json

import pytest
from app.services.memory_tools import execute_create_project


@pytest.mark.asyncio
async def test_projet_tape_deux_fois_sans_option(db_session):
    from app.services.slash_commands import execute_slash_command

    premiere = await execute_slash_command("projet", "Site Web", db_session)
    assert "créé" in premiere, premiere
    seconde = await execute_slash_command("projet", "Site Web", db_session)
    assert "déjà en mémoire" in seconde, seconde
    assert "Non appliqué" not in seconde, seconde


@pytest.mark.asyncio
async def test_une_valeur_egale_a_celle_du_projet_n_est_pas_ignoree(db_session):
    await execute_create_project({"name": "Site Web", "status": "active", "budget": 1200}, db_session)
    resultat = json.loads(await execute_create_project(
        {"name": "Site Web", "status": "active", "budget": 1200}, db_session,
    ))
    assert resultat.get("already_existed") is True, resultat
    assert not resultat.get("ignore") and not resultat.get("champs_ignores"), resultat


@pytest.mark.asyncio
async def test_une_valeur_differente_reste_signalee(db_session):
    from app.services.slash_commands import execute_slash_command

    await execute_slash_command("projet", "Site Web", db_session)
    seconde = await execute_slash_command("projet", "Site Web statut=completed", db_session)
    assert "Non appliqué" in seconde and "statut" in seconde, seconde


@pytest.mark.asyncio
async def test_projet_termine_retape_sans_option(db_session):
    """La commande ne doit pas injecter « active » : sur un projet terminé, ce
    défaut devenait une demande « non appliquée » que personne n'avait faite."""
    from app.services.slash_commands import execute_slash_command

    await execute_create_project({"name": "Site Web", "status": "completed"}, db_session)
    reponse = await execute_slash_command("projet", "Site Web", db_session)
    assert "Non appliqué" not in reponse, reponse
