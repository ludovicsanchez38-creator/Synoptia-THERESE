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
