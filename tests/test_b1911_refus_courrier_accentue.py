"""Le refus directement affichable du courrier reste en français correct."""

import pytest
from app.services.workspace_tools import execute_workspace_tool, poser_ecran


@pytest.mark.asyncio
async def test_sans_compte_le_message_est_accentue_et_tutoie(db_session):
    poser_ecran()
    resultat = await execute_workspace_tool("read_emails", {}, db_session)
    assert resultat == (
        "Aucun compte e-mail connecté. Configure ton adresse e-mail dans les paramètres."
    )
