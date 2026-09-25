"""B-1431 (recette P-146, lot 1, A-2) : la création d'un rendez-vous par la
conversation répondait « Evenement cree : … », sans accents, et l'agenda
local non branché disait « Aucun calendrier configure … cree ». Dette déjà
notée pour `/rdv` ; la recette l'a vue à l'écran."""

from datetime import datetime, timedelta

import pytest


@pytest.mark.asyncio
async def test_la_creation_d_un_rendez_vous_s_ecrit_avec_ses_accents(client):
    from app.models.database import get_session_context
    from app.services.workspace_tools import execute_workspace_tool

    debut = datetime.now() + timedelta(days=2)
    fin = debut + timedelta(hours=1)
    async with get_session_context() as session:
        retour = await execute_workspace_tool(
            "create_calendar_event",
            {"summary": "Calibration du devis", "start": debut.strftime("%Y-%m-%dT%H:%M:%S"),
             "end": fin.strftime("%Y-%m-%dT%H:%M:%S")},
            session,
        )
    assert retour.startswith("Événement créé : **Calibration du devis**"), retour
    assert "Evenement" not in retour and "cree" not in retour
