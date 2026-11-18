"""Une erreur d'agenda ne doit pas inventer une absence de connexion."""

from datetime import UTC, datetime

import pytest
from app.models.entities import Calendar, EmailAccount
from app.services.workspace_tools import execute_workspace_tool, poser_ecran


@pytest.mark.asyncio
@pytest.mark.parametrize(("cas", "detail"), [
    ("introuvable", "Agenda introuvable"),
    ("google_sans_compte", "Agenda Google sans compte associé"),
    ("fournisseur_inconnu", "Fournisseur de calendrier non pris en charge"),
    ("plusieurs_comptes", "Plusieurs comptes Google sont connectés"),
])
async def test_l_outil_restitue_la_cause_sans_affirmer_une_absence_de_calendrier(
    db_session, cas, detail
):
    poser_ecran()
    arguments = {}
    if cas == "introuvable":
        db_session.add(Calendar(id="agenda-existant", summary="Existant", provider="local"))
        arguments["calendar_id"] = "agenda-absent"
    elif cas in {"google_sans_compte", "fournisseur_inconnu"}:
        db_session.add(Calendar(
            id="agenda-invalide", summary="Existant",
            provider="google" if cas == "google_sans_compte" else "inconnu",
            synced_at=datetime.now(UTC),
        ))
        arguments["calendar_id"] = "agenda-invalide"
    else:
        db_session.add_all([
            EmailAccount(id="compte-1", email="a@example.invalid", provider="gmail"),
            EmailAccount(id="compte-2", email="b@example.invalid", provider="gmail"),
        ])
    await db_session.commit()

    resultat = await execute_workspace_tool("list_calendar_events", arguments, db_session)

    assert detail.lower() in resultat.lower()
    assert "aucun calendrier connecté" not in resultat.lower()
    assert "aucun calendrier connecte" not in resultat.lower()
    assert "aucun calendrier synchronisé" not in resultat.lower()
