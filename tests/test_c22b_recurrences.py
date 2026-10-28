"""B-1308/B-1309 : occurrences DAV groupées et séries locales anciennes."""
import json
from datetime import UTC, datetime
from types import SimpleNamespace

import pytest
from sqlmodel import select
from app.models.entities import Calendar, CalendarEvent, Notification
from app.routers import calendar as routes
from app.services import notification_service as notifications
from app.services.calendar.caldav_provider import CalDAVProvider


def serie_dav():
    return 'BEGIN:VCALENDAR\r\nVERSION:2.0\r\n' + ''.join(
        f'BEGIN:VEVENT\r\nUID:serie\r\nSUMMARY:Point quotidien\r\nRECURRENCE-ID:202610{jour}T090000Z\r\n'
        f'DTSTART:202610{jour}T090000Z\r\nDTEND:202610{jour}T100000Z\r\nEND:VEVENT\r\n'
        for jour in ('28', '29', '30')
    ) + 'END:VCALENDAR\r\n'


@pytest.fixture
def dav(monkeypatch):
    agenda = SimpleNamespace(id='distant', url='https://dav.example/agenda/',
        date_search=lambda **kwargs: [SimpleNamespace(data=serie_dav())])
    provider = CalDAVProvider.__new__(CalDAVProvider)
    monkeypatch.setattr(provider, '_get_principal', lambda: SimpleNamespace(calendars=lambda: [agenda]))
    provider.serveur_simule = agenda
    return provider


@pytest.mark.asyncio
async def test_tous_les_vevent_et_pagination(dav):
    premiere, suite = await dav.list_events('distant', datetime(2026, 10, 28, tzinfo=UTC), datetime(2026, 11, 1, tzinfo=UTC), max_results=2)
    assert len(premiere) == 2
    assert suite is not None
    seconde, fin = await dav.list_events('distant', datetime(2026, 10, 28, tzinfo=UTC), datetime(2026, 11, 1, tzinfo=UTC), max_results=2, page_token=suite)
    assert len(seconde) == 1 and fin is None
    assert len({e.id for e in premiere + seconde}) == 3
    assert all(e.recurring_event_id == 'serie' for e in premiere + seconde)


def figer(monkeypatch):
    class Horloge(datetime):
        @classmethod
        def now(cls, tz=None):
            instant = datetime(2026, 10, 28, 12, tzinfo=UTC)
            return instant.astimezone(tz) if tz else instant.replace(tzinfo=None)
    monkeypatch.setattr(notifications, 'datetime', Horloge)


@pytest.mark.asyncio
async def test_les_occurrences_dav_survivent_dans_le_cache_et_les_rappels(client, db_session, dav, monkeypatch):
    db_session.add(Calendar(id='dav-local', summary='iCloud', provider='caldav', remote_id='distant'))
    await db_session.commit()
    async def provider(*args):
        return dav
    monkeypatch.setattr(routes, '_get_provider_for_calendar', provider)
    reponse = await client.get('/api/calendar/events', params={'calendar_id': 'dav-local', 'time_min': '2026-10-28', 'time_max': '2026-11-01'})
    assert reponse.status_code == 200, reponse.text
    assert len(reponse.json()) == 3
    assert len((await db_session.execute(select(CalendarEvent))).scalars().all()) == 3
    figer(monkeypatch)
    assert await notifications._check_upcoming_events(db_session) == 1
    assert await notifications._check_upcoming_events(db_session) == 0
    await db_session.commit()
    # Une série effacée du téléphone ne doit pas rester dans le cache.
    dav.serveur_simule.date_search = lambda **kwargs: []
    reponse = await client.get('/api/calendar/events', params={'calendar_id': 'dav-local', 'time_min': '2026-10-28', 'time_max': '2026-11-01'})
    assert reponse.status_code == 200, reponse.text
    assert reponse.json() == []
    assert (await db_session.execute(select(CalendarEvent))).scalars().all() == []


@pytest.mark.asyncio
async def test_occurrence_annulee_et_journee_entiere(dav):
    dav.serveur_simule.date_search = lambda **kwargs: [SimpleNamespace(data=(
        'BEGIN:VCALENDAR\r\nVERSION:2.0\r\nBEGIN:VEVENT\r\nUID:jour\r\n'
        'RECURRENCE-ID;VALUE=DATE:20261029\r\nDTSTART;VALUE=DATE:20261029\r\n'
        'DTEND;VALUE=DATE:20261030\r\nSTATUS:CANCELLED\r\nEND:VEVENT\r\nEND:VCALENDAR\r\n'
    ))]
    occurrences, _ = await dav.list_events('distant')
    assert occurrences[0].all_day
    assert str(occurrences[0].start) == str(occurrences[0].end) == '2026-10-29'
    assert occurrences[0].status == 'cancelled'


@pytest.mark.asyncio
async def test_serie_locale_apres_premiere_date_dans_agenda_et_rappels(client, db_session, monkeypatch):
    db_session.add(Calendar(id='local', summary='Local', provider='local'))
    db_session.add(CalendarEvent(id='serie-locale', calendar_id='local', summary='Point local',
        start_datetime=datetime(2026, 10, 1, 10), end_datetime=datetime(2026, 10, 1, 11),
        recurrence=json.dumps(['RRULE:FREQ=WEEKLY;BYDAY=TH']), status='confirmed'))
    await db_session.commit()
    reponse = await client.get('/api/calendar/events', params={'calendar_id': 'local', 'time_min': '2026-10-28', 'time_max': '2026-11-08'})
    assert reponse.status_code == 200, reponse.text
    assert [e['start_datetime'][:10] for e in reponse.json()] == ['2026-10-29', '2026-11-05']
    figer(monkeypatch)
    assert await notifications._check_upcoming_events(db_session) == 1
    rappels = (await db_session.execute(select(Notification))).scalars().all()
    assert rappels[0].message == 'RDV demain à 10h00 : Point local'
