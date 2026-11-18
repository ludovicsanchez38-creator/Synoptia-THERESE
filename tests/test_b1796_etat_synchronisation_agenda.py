"""Le résultat d'agenda indique au modèle l'état réellement enregistré."""

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from app.models.entities import Calendar
from app.services import workspace_tools


@pytest.mark.asyncio
async def test_etat_caldav_sain_transmis_avec_les_evenements(db_session, monkeypatch):
    calendrier = Calendar(
        id="caldav-sain", summary="Agenda fictif", provider="caldav",
        sync_status="idle", synced_at=datetime.now(UTC),
    )
    db_session.add(calendrier)
    await db_session.commit()
    debut = datetime.now(UTC) + timedelta(days=1)
    evenement = SimpleNamespace(
        summary="Rendez-vous réel fictif", start=debut, end=debut + timedelta(hours=1),
        all_day=False, location=None, attendees=[],
    )
    fournisseur = SimpleNamespace(list_events=AsyncMock(return_value=([evenement], None)))
    monkeypatch.setattr(
        workspace_tools, "_provider_depuis_calendrier",
        AsyncMock(return_value=(fournisseur, "distant-fictif", None)),
    )

    resultat = await workspace_tools.execute_workspace_tool(
        "list_calendar_events", {"calendar_id": calendrier.id}, db_session,
    )

    assert "Rendez-vous réel fictif" in resultat
    assert "synchronisation" in resultat.lower()
    assert "au repos" in resultat.lower()
    assert "panne" not in resultat.lower()
