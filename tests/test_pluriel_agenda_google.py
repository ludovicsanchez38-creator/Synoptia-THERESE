"""Finding 3 (revue 30/08) : le second agenda Google écrasait le premier.

Les fériés ont le même id Google sur deux comptes. Le sync de B mettait à
jour le summary et laissait `account_id` de A. Déconnecter A, et l'agenda
férié de B 401. On refuse d'écrire sur une ligne qui n'est pas à nous.
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest
from app.models.entities import Calendar, CalendarEvent, EmailAccount

FERIE = "fr.french#holiday@group.v.calendar.google.com"


@pytest.mark.asyncio
async def test_sync_b_n_ecrase_pas_l_agenda_de_a(db_session, monkeypatch):
    a = EmailAccount(id="acc-a", email="a@gmail.com", provider="gmail", access_token="tok-a")
    b = EmailAccount(id="acc-b", email="b@gmail.com", provider="gmail", access_token="tok-b")
    ferie_a = Calendar(
        id=FERIE,
        account_id="acc-a",
        summary="Jours fériés A",
        provider="google",
        remote_id=FERIE,
    )
    db_session.add_all([a, b, ferie_a])
    await db_session.commit()

    class FakeCalendarService:
        def __init__(self, _token):
            pass

        async def list_calendars(self):
            return [
                {
                    "id": FERIE,
                    "summary": "Jours fériés B",
                    "timeZone": "Europe/Paris",
                    "primary": False,
                }
            ]

    async def fake_ensure(account, session):
        return "tok"

    monkeypatch.setattr("app.routers.calendar.CalendarService", FakeCalendarService)
    monkeypatch.setattr("app.routers.calendar.ensure_valid_access_token", fake_ensure)

    from app.routers.calendar import _list_google_calendars

    rendus = await _list_google_calendars("acc-b", b, db_session)
    ids_rendus = {cal.id for cal in rendus}
    assert FERIE not in ids_rendus

    reste = await db_session.get(Calendar, FERIE)
    assert reste is not None
    assert reste.account_id == "acc-a"
    assert reste.summary == "Jours fériés A"


@pytest.mark.asyncio
async def test_sync_b_n_ecrase_pas_l_evenement_de_a(db_session, monkeypatch):
    a = EmailAccount(id="acc-a", email="a@gmail.com", provider="gmail", access_token="tok-a")
    b = EmailAccount(id="acc-b", email="b@gmail.com", provider="gmail", access_token="tok-b")
    cal_a = Calendar(
        id="cal-a",
        account_id="acc-a",
        summary="A",
        provider="google",
        remote_id="cal-a",
    )
    cal_b = Calendar(
        id="cal-b",
        account_id="acc-b",
        summary="B",
        provider="google",
        remote_id="cal-b",
    )
    evt = CalendarEvent(
        id="evt-partage",
        calendar_id="cal-a",
        summary="Férié A",
        start_date="2026-07-14",
        end_date="2026-07-14",
        all_day=True,
        synced_at=datetime.now(UTC),
    )
    db_session.add_all([a, b, cal_a, cal_b, evt])
    await db_session.commit()

    class FakeCalendarService:
        def __init__(self, _token):
            pass

        async def list_events(self, calendar_id, dt_min, dt_max, max_results):
            return {
                "items": [
                    {
                        "id": "evt-partage",
                        "summary": "Férié B",
                        "status": "confirmed",
                        "start": {"date": "2026-07-14"},
                        "end": {"date": "2026-07-15"},
                    }
                ]
            }

    monkeypatch.setattr("app.routers.calendar.CalendarService", FakeCalendarService)
    monkeypatch.setattr(
        "app.routers.calendar.ensure_valid_access_token",
        AsyncMock(return_value="tok"),
    )

    from app.routers.calendar import _list_events_google

    rendus = await _list_events_google(
        "acc-b", "cal-b", db_session, None, None, 10
    )
    ids_rendus = {e.id for e in rendus}
    assert "evt-partage" not in ids_rendus

    reste = await db_session.get(CalendarEvent, "evt-partage")
    assert reste is not None
    assert reste.calendar_id == "cal-a"
    assert reste.summary == "Férié A"
