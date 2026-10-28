"""B-1307 : routes HTTP, vrai fournisseur et serveur DAV simulé en mémoire."""
from types import SimpleNamespace

import pytest
from icalendar import Calendar as ICalendar
from app.models.entities import Calendar
from app.services.calendar.caldav_provider import CalDAVProvider
from app.routers import calendar as routes


class EvenementDAV:
    def __init__(self, serveur, data):
        self.serveur, self.data = serveur, data
        self.url = 'https://dav.example/agenda/evenement.ics'
        self.props = {'{DAV:}getetag': '"version-1"'}
        self.client = self

    def load(self, **kwargs):
        return self

    def put(self, url, body, headers):
        assert headers['If-Match'] == '"version-1"'
        self.data = body
        self.serveur.ecritures.append('modification')
        return SimpleNamespace(status=204, headers={})

    def delete(self):
        self.serveur.ecritures.append('suppression')
        self.serveur.evenement = None


class ServeurDAV:
    id = 'agenda-distant'
    url = 'https://dav.example/agenda/'

    def __init__(self):
        self.evenement = None
        self.ecritures = []

    def calendars(self):
        return [self]

    def save_event(self, data):
        calendrier = ICalendar.from_ical(data)
        calendrier.walk('VEVENT')[0].add('uid', 'evenement-distant')
        self.evenement = EvenementDAV(self, calendrier.to_ical().decode())
        self.ecritures.append('création')
        return self.evenement

    def event_by_uid(self, uid):
        assert uid == 'evenement-distant'
        if self.evenement is None:
            raise ValueError('absent')
        return self.evenement

    def events(self):
        return [self.evenement] if self.evenement else []


@pytest.mark.asyncio
async def test_creer_modifier_supprimer_avec_identifiant_local(client, db_session, monkeypatch):
    serveur = ServeurDAV()
    fournisseur = CalDAVProvider.__new__(CalDAVProvider)
    monkeypatch.setattr(fournisseur, '_get_principal', lambda: serveur)

    async def provider(*args):
        return fournisseur

    monkeypatch.setattr(routes, '_get_provider_for_calendar', provider)
    agenda = Calendar(id='agenda-local', summary='iCloud', provider='caldav', remote_id=serveur.url)
    db_session.add(agenda)
    await db_session.commit()
    creation = await client.post('/api/calendar/events', json={
        'calendar_id': agenda.id, 'summary': 'Rendez-vous',
        'start_datetime': '2026-10-28T10:00:00', 'end_datetime': '2026-10-28T11:00:00',
    })
    assert creation.status_code == 200, creation.text
    assert creation.json()['calendar_id'] == agenda.id
    identifiant = creation.json()['id']
    modification = await client.put(f'/api/calendar/events/{identifiant}', params={'calendar_id': agenda.id}, json={'summary': 'Titre corrigé'})
    assert modification.status_code == 200, modification.text
    assert modification.json()['calendar_id'] == agenda.id
    assert modification.json()['summary'] == 'Titre corrigé'
    suppression = await client.delete(f'/api/calendar/events/{identifiant}', params={'calendar_id': agenda.id})
    assert suppression.status_code == 200, suppression.text
    assert serveur.ecritures == ['création', 'modification', 'suppression']
