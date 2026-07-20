"""
BUG-144 - Semantique des dates de fin « toute la journee ».

L'app est INCLUSIVE (formulaire et detail affichent la date de fin comme un
jour de l'evenement). Google Calendar et la RFC 5545 (CalDAV) sont EXCLUSIFS
(end.date / DTEND = lendemain du dernier jour). Les providers convertissent
aux frontieres : +1 jour a l'ecriture, -1 jour (clampe) a la lecture.
Sans conversion, un evenement d'un seul jour (debut = fin, desormais accepte
par le formulaire) serait refuse par Google (plage vide).
"""

from datetime import date
from unittest.mock import AsyncMock

import pytest
from app.services.calendar.base_provider import (
    CreateEventRequest,
    UpdateEventRequest,
    allday_end_from_wire,
    allday_end_to_wire,
)
from app.services.calendar.google_provider import GoogleCalendarProvider


class TestAlldayEndHelpers:
    def test_vers_le_fil_ajoute_un_jour(self):
        assert allday_end_to_wire(date(2026, 7, 19)) == date(2026, 7, 20)

    def test_depuis_le_fil_retire_un_jour(self):
        assert allday_end_from_wire(date(2026, 7, 19), date(2026, 7, 20)) == date(2026, 7, 19)

    def test_depuis_le_fil_clampe_une_plage_degeneree(self):
        # Donnee invalide (end == start sur le fil) : ne jamais rendre end < start
        assert allday_end_from_wire(date(2026, 7, 19), date(2026, 7, 19)) == date(2026, 7, 19)


GEVENT_UN_JOUR = {
    "id": "evt-1",
    "summary": "Salon pro",
    "start": {"date": "2026-07-19"},
    "end": {"date": "2026-07-20"},  # exclusif cote Google = 1 seul jour
}


def _provider() -> GoogleCalendarProvider:
    provider = GoogleCalendarProvider(access_token="jeton-test")
    provider._service = AsyncMock()
    return provider


class TestGoogleAlldaySemantics:
    @pytest.mark.asyncio
    async def test_create_envoie_une_fin_exclusive(self):
        provider = _provider()
        provider._service.create_event.return_value = GEVENT_UN_JOUR

        await provider.create_event(CreateEventRequest(
            calendar_id="cal-1", summary="Salon pro",
            start=date(2026, 7, 19), end=date(2026, 7, 19), all_day=True,
        ))

        sent = provider._service.create_event.call_args.kwargs
        assert sent["start"] == {"date": "2026-07-19"}
        assert sent["end"] == {"date": "2026-07-20"}

    @pytest.mark.asyncio
    async def test_update_envoie_une_fin_exclusive(self):
        provider = _provider()
        provider._service.update_event.return_value = GEVENT_UN_JOUR

        await provider.update_event("cal-1", "evt-1", UpdateEventRequest(
            start=date(2026, 7, 19), end=date(2026, 7, 19), all_day=True,
        ))

        sent = provider._service.update_event.call_args.kwargs
        assert sent["end"] == {"date": "2026-07-20"}

    def test_lecture_rend_une_fin_inclusive(self):
        provider = _provider()

        dto = provider._gevent_to_dto(GEVENT_UN_JOUR, "cal-1")

        assert dto.all_day is True
        assert dto.start == date(2026, 7, 19)
        assert dto.end == date(2026, 7, 19)

    def test_lecture_clampe_une_plage_degeneree(self):
        provider = _provider()
        gevent = {**GEVENT_UN_JOUR, "end": {"date": "2026-07-19"}}

        dto = provider._gevent_to_dto(gevent, "cal-1")

        assert dto.end == date(2026, 7, 19)


class TestCacheMigrationAlldaySemantics:
    """F4 contre-verif : les evenements Google/CalDAV deja en cache avaient une
    fin EXCLUSIVE (stockee avant 0.41.1). Migration ad-hoc unique (marqueur
    preferences) : -1 jour clampe, calendriers locaux intacts, idempotente."""

    def _seed_db(self, db_path):
        from contextlib import closing

        from app.models.database import db_connect

        with closing(db_connect(db_path)) as conn:
            conn.execute("CREATE TABLE calendars (id TEXT PRIMARY KEY, provider TEXT)")
            conn.execute(
                "CREATE TABLE calendar_events (id TEXT PRIMARY KEY, calendar_id TEXT,"
                " all_day INTEGER, start_date TEXT, end_date TEXT)"
            )
            conn.execute(
                "CREATE TABLE preferences (id TEXT PRIMARY KEY, key TEXT UNIQUE,"
                " value TEXT, category TEXT, created_at TEXT, updated_at TEXT)"
            )
            conn.execute("INSERT INTO calendars VALUES ('cal-g', 'google')")
            conn.execute("INSERT INTO calendars VALUES ('cal-l', 'local')")
            # Cache Google pre-0.41.1 : fin exclusive (20 = evenement d'un jour)
            conn.execute("INSERT INTO calendar_events VALUES ('e-g', 'cal-g', 1, '2026-07-19', '2026-07-20')")
            # Local : deja inclusif, ne doit PAS bouger
            conn.execute("INSERT INTO calendar_events VALUES ('e-l', 'cal-l', 1, '2026-07-19', '2026-07-19')")
            conn.commit()

    def _end_dates(self, db_path):
        from contextlib import closing

        from app.models.database import db_connect

        with closing(db_connect(db_path)) as conn:
            rows = conn.execute("SELECT id, end_date FROM calendar_events").fetchall()
        return dict(rows)

    def test_conversion_unique_et_idempotente(self, tmp_path):
        from app.models.database import apply_adhoc_migrations

        db_path = tmp_path / "migration.db"
        self._seed_db(db_path)

        apply_adhoc_migrations(db_path)

        ends = self._end_dates(db_path)
        assert ends["e-g"] == "2026-07-19"  # exclusif -> inclusif
        assert ends["e-l"] == "2026-07-19"  # local intact

        # Idempotence : un second passage ne re-decremente pas
        apply_adhoc_migrations(db_path)
        assert self._end_dates(db_path)["e-g"] == "2026-07-19"


class TestIcsAlldaySemantics:
    """F4 revue : DTEND est EXCLUSIF dans ICS (RFC 5545). L'import doit stocker
    une fin inclusive, l'export doit écrire DTEND = fin + 1 jour."""

    def test_import_ics_fin_exclusive_devient_inclusive(self):
        from app.services.import_service import parse_ics

        ics = (
            b"BEGIN:VCALENDAR\r\nVERSION:2.0\r\nBEGIN:VEVENT\r\n"
            b"UID:evt-1\r\nSUMMARY:Salon pro\r\n"
            b"DTSTART;VALUE=DATE:20260719\r\nDTEND;VALUE=DATE:20260720\r\n"
            b"END:VEVENT\r\nEND:VCALENDAR\r\n"
        )

        events = parse_ics(ics)

        assert len(events) == 1
        assert events[0]["all_day"] is True
        assert events[0]["start"] == "2026-07-19"
        # 1 seul jour : DTEND exclusif 20 -> fin inclusive 19
        assert events[0]["end"] == "2026-07-19"

    def test_import_ics_sans_dtend_reste_un_jour(self):
        from app.services.import_service import parse_ics

        ics = (
            b"BEGIN:VCALENDAR\r\nVERSION:2.0\r\nBEGIN:VEVENT\r\n"
            b"UID:evt-2\r\nSUMMARY:Salon\r\n"
            b"DTSTART;VALUE=DATE:20260719\r\n"
            b"END:VEVENT\r\nEND:VCALENDAR\r\n"
        )

        events = parse_ics(ics)

        assert events[0]["end"] == "2026-07-19"

    @pytest.mark.asyncio
    async def test_export_ics_ecrit_dtend_exclusif(self, client):
        cal = (await client.post("/api/calendar/calendars", json={
            "name": "Local export", "provider": "local",
        })).json()
        created = await client.post("/api/calendar/events", json={
            "calendar_id": cal["id"], "summary": "Salon pro",
            "start_date": "2026-07-19", "end_date": "2026-07-19",
        })
        assert created.status_code == 200, created.text

        response = await client.get("/api/calendar/export-ics")

        assert response.status_code == 200
        body = response.content.decode()
        assert "DTSTART;VALUE=DATE:20260719" in body
        # Fin inclusive 19 -> DTEND exclusif 20 (RFC 5545)
        assert "DTEND;VALUE=DATE:20260720" in body


class TestGoogleRoutesAlldaySemantics:
    """F2 revue : les routes calendrier Google (routers/calendar.py) passent
    par CalendarService DIRECTEMENT, pas par GoogleCalendarProvider - les
    conversions inclusif/exclusif doivent s'appliquer la aussi, a l'ecriture
    (end.date envoye a Google) ET au stockage local (end_date relu).
    """

    @pytest.mark.asyncio
    async def test_create_route_envoie_fin_exclusive_et_stocke_inclusif(self):
        from unittest.mock import AsyncMock, MagicMock, patch

        from app.models.entities import EmailAccount
        from app.models.schemas import CreateEventRequest
        from app.routers.calendar import _create_event_google

        request = CreateEventRequest(
            calendar_id="primary", summary="Salon pro",
            start_date="2026-07-19", end_date="2026-07-19",
        )

        captured: dict = {}
        stored: list = []

        class FakeCalendarService:
            def __init__(self, _token):
                pass

            async def create_event(self, **kwargs):
                captured.update(kwargs)
                return {
                    "id": "evt-1", "summary": kwargs["summary"],
                    "start": kwargs["start"], "end": kwargs["end"],
                    "status": "confirmed",
                }

        account = EmailAccount(id="acc-1", email="t@example.com", provider="gmail", access_token="tok")
        session = MagicMock()
        session.get = AsyncMock(return_value=account)
        session.add = MagicMock(side_effect=stored.append)
        session.commit = AsyncMock()
        session.refresh = AsyncMock()

        with patch("app.routers.calendar.CalendarService", FakeCalendarService), patch(
            "app.routers.calendar.ensure_valid_access_token", AsyncMock(return_value="tok")
        ):
            await _create_event_google("acc-1", request, session)

        # Vers Google : fin EXCLUSIVE (+1 jour), sinon plage vide refusee
        assert captured["start"] == {"date": "2026-07-19"}
        assert captured["end"] == {"date": "2026-07-20"}
        # Stockage local : fin INCLUSIVE (relue depuis la reponse Google)
        events = [obj for obj in stored if getattr(obj, "end_date", None)]
        assert events, "aucun CalendarEvent stocke"
        assert events[0].start_date == "2026-07-19"
        assert events[0].end_date == "2026-07-19"
