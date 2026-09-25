"""B-1257 : `/projet X budget=beaucoup` jetait le budget illisible avant
l'outil ; la réponse disait « Projet créé » sans signaler le budget perdu.
Revue du diff (passe 4) et lecteur U (« budget=15000€ »)."""

import pytest
from app.models.entities import Project
from sqlmodel import select


@pytest.mark.asyncio
async def test_un_budget_illisible_est_signale(db_session):
    from app.services.slash_commands import execute_slash_command

    reponse = await execute_slash_command("projet", "Chantier budget=beaucoup", db_session)
    assert "créé" in reponse and "budget" in reponse.lower() and "beaucoup" in reponse, reponse


@pytest.mark.asyncio
async def test_un_budget_en_euros_est_lu(db_session):
    from app.services.slash_commands import execute_slash_command

    reponse = await execute_slash_command("projet", "Chantier budget=15000€", db_session)
    assert "créé" in reponse, reponse
    projet = (await db_session.execute(select(Project).where(Project.name == "Chantier"))).scalar_one()
    assert projet.budget == 15000, projet.budget
