"""Relecture R1 : la réponse HTTP simulée par le panneau vient du vrai routeur."""

import json
from pathlib import Path
from unittest.mock import AsyncMock

import httpx
import pytest
from app.models.entities import Calendar, CalendarEvent, EmailAccount
from app.services import calendar_service

REPONSE_PANNEAU = (
    Path(__file__).resolve().parents[1]
    / "src/frontend/src/components/calendar/fixtures/googleCalendar403.json"
)
REFUS_GOOGLE = "Google Calendar API has not been used in project 42 before or it is disabled."


@pytest.mark.parametrize("operation", ["calendriers", "evenements", "synchronisation"])
async def test_relecture_r1_le_403_du_routeur_correspond_a_la_reponse_du_panneau(
    client, db_session, monkeypatch, operation: str,
):
    compte = EmailAccount(id="compte-403", email="agenda@example.test", provider="gmail")
    agenda = Calendar(id="agenda-403", summary="Agenda", provider="google", account_id=compte.id)
    evenement = CalendarEvent(id="cache-403", calendar_id=agenda.id, summary="Rendez-vous conservé")
    db_session.add_all([compte, agenda, evenement])
    await db_session.commit()
    appels = []

    def google_refuse(requete: httpx.Request) -> httpx.Response:
        appels.append((requete.method, requete.url.path))
        return httpx.Response(403, json={"error": {"code": 403, "message": REFUS_GOOGLE}})

    async with httpx.AsyncClient(transport=httpx.MockTransport(google_refuse)) as transport:
        monkeypatch.setattr(calendar_service, "get_http_client", AsyncMock(return_value=transport))
        if operation == "calendriers":
            reponse = await client.get("/api/calendar/calendars", params={"account_id": compte.id})
        elif operation == "evenements":
            reponse = await client.get("/api/calendar/events", params={
                "account_id": compte.id, "calendar_id": agenda.id,
            })
        else:
            reponse = await client.post("/api/calendar/sync", params={"account_id": compte.id})

    attendu = json.loads(REPONSE_PANNEAU.read_text(encoding="utf-8"))
    assert {"status": reponse.status_code, "body": reponse.json()} == attendu
    assert REFUS_GOOGLE not in reponse.text
    chemin = "/calendar/v3/calendars/agenda-403/events" if operation == "evenements" else "/calendar/v3/users/me/calendarList"
    assert appels == [("GET", chemin)]
    await db_session.refresh(evenement)
    assert (evenement.calendar_id, evenement.summary) == (agenda.id, "Rendez-vous conservé")
