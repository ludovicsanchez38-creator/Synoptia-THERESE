"""B-1553 : le brief et la semaine rendent un instant daté, comme l'Agenda."""

from datetime import date, datetime

import pytest
from app.models.entities import Calendar, CalendarEvent
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_brief_rend_le_fuseau_de_paris_pour_un_rendez_vous(
    client: AsyncClient, db_session, monkeypatch
):
    monkeypatch.setattr(
        "app.routers.dashboard.date_civile_paris", lambda *_a, **_k: date(2026, 10, 1)
    )
    db_session.add(Calendar(id="cal-b1553-brief", summary="Agenda jetable", provider="local"))
    await db_session.flush()
    db_session.add(
        CalendarEvent(
            id="ev-b1553-brief",
            calendar_id="cal-b1553-brief",
            summary="Point jetable",
            start_datetime=datetime(2026, 10, 1, 16, 0),
            end_datetime=datetime(2026, 10, 1, 17, 0),
        )
    )
    await db_session.commit()

    reponse = await client.get("/api/dashboard/today")

    assert reponse.status_code == 200
    evenement = next(ev for ev in reponse.json()["events"] if ev["id"] == "ev-b1553-brief")
    assert evenement["start_datetime"] == "2026-10-01T16:00:00+02:00"
    assert evenement["end_datetime"] == "2026-10-01T17:00:00+02:00"


@pytest.mark.asyncio
async def test_semaine_rend_le_fuseau_de_paris_pour_un_rendez_vous(
    client: AsyncClient, db_session, monkeypatch
):
    monkeypatch.setattr(
        "app.routers.dashboard.date_civile_paris", lambda *_a, **_k: date(2026, 10, 1)
    )
    db_session.add(Calendar(id="cal-b1553-semaine", summary="Agenda jetable", provider="local"))
    await db_session.flush()
    db_session.add(
        CalendarEvent(
            id="ev-b1553-semaine",
            calendar_id="cal-b1553-semaine",
            summary="Point jetable",
            start_datetime=datetime(2026, 10, 2, 1, 0),
            end_datetime=datetime(2026, 10, 2, 2, 0),
        )
    )
    await db_session.commit()

    reponse = await client.get("/api/dashboard/semaine")

    assert reponse.status_code == 200
    evenement = next(ev for ev in reponse.json()["a_venir"] if ev["id"] == "ev-b1553-semaine")
    assert evenement["date"] == "2026-10-02T01:00:00+02:00"
