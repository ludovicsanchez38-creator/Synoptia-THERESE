"""B-481 (05/09/2026) : CalDAV annonçait `supports_reminders` et jetait
rappels, participants (à la mise à jour), récurrence et statut.

La requête de création porte reminders=[30] par défaut : l'iCalendar
sauvé n'avait ni VALARM ni STATUS ; la mise à jour ne touchait que
summary/description/location/dtstart/dtend, donc un participant ou une
règle de récurrence modifiés ne partaient jamais au serveur.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from app.services.calendar.base_provider import CreateEventRequest, UpdateEventRequest
from app.services.calendar.caldav_provider import CalDAVProvider
from icalendar import Calendar as ICalendar


class _Evenement:
    def __init__(self, data: str):
        self.data = data

    def load(self, only_if_unloaded: bool = False):
        return None


class _Calendrier:
    def __init__(self, ident: str, evenements: list[_Evenement]):
        self.id, self.url, self._evenements = ident, ident, evenements
        self.sauves: list[str] = []

    def save_event(self, texte: str):
        self.sauves.append(texte)
        return _Evenement(texte)

    def events(self):
        return self._evenements

    def event_by_uid(self, uid: str):
        raise Exception("non supporté")


class _Principal:
    def __init__(self, cal):
        self._cal = cal

    def calendars(self):
        return [self._cal]


def _provider(monkeypatch, cal):
    provider = CalDAVProvider(url="https://cal.test/", username="marie", password="x")
    monkeypatch.setattr(provider, "_get_principal", lambda: _Principal(cal))
    monkeypatch.setattr(provider, "_caldav_event_to_dto", lambda event, calendar_id: {"ok": True})
    return provider


def _vevent(texte: str):
    for c in ICalendar.from_ical(texte).walk():
        if c.name == "VEVENT":
            return c
    raise AssertionError("pas de VEVENT")


@pytest.mark.asyncio
async def test_la_creation_ecrit_les_rappels(monkeypatch):
    cal = _Calendrier("cal-1", [])
    provider = _provider(monkeypatch, cal)
    debut = datetime.now(UTC) + timedelta(days=1)

    await provider.create_event(
        CreateEventRequest(
            calendar_id="cal-1", summary="Point", start=debut, end=debut + timedelta(hours=1),
            attendees=["paul@durand.test"], reminders=[30, 10],
        )
    )

    vevent = _vevent(cal.sauves[0])
    alarmes = [c for c in vevent.subcomponents if c.name == "VALARM"]
    assert len(alarmes) == 2, "aucun VALARM écrit"
    triggers = sorted(str(a["trigger"].to_ical()) for a in alarmes)
    assert any("PT30M" in t for t in triggers) and any("PT10M" in t for t in triggers), triggers
    assert "paul@durand.test" in str(vevent.get("attendee"))


@pytest.mark.asyncio
async def test_la_mise_a_jour_ecrit_participants_recurrence_statut_et_rappels(monkeypatch):
    existant = (
        "BEGIN:VCALENDAR\r\nVERSION:2.0\r\nPRODID:-//test//\r\nBEGIN:VEVENT\r\nUID:evt-1\r\n"
        "SUMMARY:Point\r\nDTSTART:20260910T100000Z\r\nDTEND:20260910T110000Z\r\n"
        "BEGIN:VALARM\r\nACTION:DISPLAY\r\nTRIGGER:-PT30M\r\nEND:VALARM\r\nEND:VEVENT\r\nEND:VCALENDAR\r\n"
    )
    evenement = _Evenement(existant)
    cal = _Calendrier("cal-1", [evenement])
    provider = _provider(monkeypatch, cal)
    ecrits: list[str] = []
    monkeypatch.setattr(provider, "_enregistrer_avec_precondition", lambda event, donnees: ecrits.append(donnees))

    await provider.update_event(
        "cal-1", "evt-1",
        UpdateEventRequest(attendees=["claire@roux.test"], recurrence=["RRULE:FREQ=WEEKLY"], status="cancelled", reminders=[15]),
    )

    vevent = _vevent(ecrits[0])
    assert "claire@roux.test" in str(vevent.get("attendee")), "participant non écrit"
    assert "WEEKLY" in vevent["rrule"].to_ical().decode().upper(), "récurrence non écrite"
    assert str(vevent.get("status")).upper() == "CANCELLED"
    alarmes = [c for c in vevent.subcomponents if c.name == "VALARM"]
    assert len(alarmes) == 1 and "PT15M" in str(alarmes[0]["trigger"].to_ical()), "rappel non remplacé"
