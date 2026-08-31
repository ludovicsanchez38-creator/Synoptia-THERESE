"""Les heures Google sont normalisées avant leur stockage SQLite."""

from datetime import datetime
from unittest.mock import AsyncMock

import pytest
from app.models.entities import Calendar, CalendarEvent, EmailAccount


@pytest.mark.asyncio
async def test_sync_google_stocke_l_heure_civile_de_paris(db_session, monkeypatch):
    """22 h 30 UTC le 29 août est 00 h 30 le 30 août à Paris."""
    account = EmailAccount(
        id="account-google-clock",
        email="ludo@example.test",
        provider="gmail",
        access_token="token",
    )
    calendar = Calendar(
        id="calendar-google-clock",
        account_id=account.id,
        summary="Google",
        provider="google",
    )
    db_session.add_all([account, calendar])
    await db_session.commit()

    class FakeCalendarService:
        def __init__(self, _token):
            pass

        async def list_events(self, _calendar_id, _min, _max, _limit):
            return {
                "items": [
                    {
                        "id": "event-google-clock",
                        "summary": "Après minuit à Paris",
                        "status": "confirmed",
                        "start": {"dateTime": "2026-08-29T22:30:00Z"},
                        "end": {"dateTime": "2026-08-29T23:00:00Z"},
                    }
                ]
            }

    monkeypatch.setattr("app.routers.calendar.CalendarService", FakeCalendarService)
    monkeypatch.setattr(
        "app.routers.calendar.ensure_valid_access_token",
        AsyncMock(return_value="token"),
    )

    from app.routers.calendar import _list_events_google

    await _list_events_google(
        account.id, calendar.id, db_session, None, None, 10
    )

    stored = await db_session.get(CalendarEvent, "event-google-clock")
    assert stored is not None
    assert stored.start_datetime == datetime(2026, 8, 30, 0, 30)
