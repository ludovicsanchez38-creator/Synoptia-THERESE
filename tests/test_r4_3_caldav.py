"""#104 : découverte et synchronisation HTTP, vrai provider et DAV doublé."""
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest
from app.models.entities import Calendar, CalendarEvent
from app.services.calendar.caldav_provider import CalDAVProvider
from sqlmodel import select


@pytest.fixture
def serveur_caldav(monkeypatch):
    debut = datetime.now(UTC).replace(microsecond=0)
    fin = debut + timedelta(hours=1)
    data = ('BEGIN:VCALENDAR\r\nVERSION:2.0\r\nBEGIN:VEVENT\r\nUID:r4-evenement\r\n'
            'SUMMARY:Atelier des maquettes\r\nDTSTART:' + debut.strftime('%Y%m%dT%H%M%SZ') +
            '\r\nDTEND:' + fin.strftime('%Y%m%dT%H%M%SZ') + '\r\nEND:VEVENT\r\nEND:VCALENDAR\r\n')
    appels = []
    etat = {'erreur': False}
    def recherche(**kwargs):
        appels.append(kwargs)
        if etat['erreur']:
            raise ConnectionError('panne du serveur factice')
        return [SimpleNamespace(data=data)]
    calendrier = SimpleNamespace(id='identifiant-distant-r4', url='http://127.0.0.1:9/dav/r4/', name='Agenda fictif', date_search=recherche)
    principal = SimpleNamespace(calendars=lambda: [calendrier])
    monkeypatch.setattr(CalDAVProvider, '_get_principal', lambda self: principal)
    return appels, etat


async def setup(client):
    reponse = await client.post('/api/calendar/calendars/caldav-setup', json={
        'url': 'http://127.0.0.1:9/dav/', 'username': 'camille@example.test', 'password': 'fictif'})
    assert reponse.status_code == 200, reponse.text
    return reponse.json()[0]['id']


@pytest.mark.asyncio
async def test_setup_puis_sync_sans_compte_importe_les_evenements(client, db_session, serveur_caldav):
    identifiant = await setup(client)
    assert identifiant != 'identifiant-distant-r4'
    comptes = await client.get('/api/calendar/calendars')
    assert any(c['id'] == identifiant and c['account_id'] is None for c in comptes.json())
    sync = await client.post('/api/calendar/sync')
    assert sync.status_code == 200, sync.text
    assert sync.json()['events_synced'] == 1
    resultat = await client.get('/api/calendar/events', params={'calendar_id': identifiant})
    assert resultat.status_code == 200, resultat.text
    assert resultat.json()[0]['summary'] == 'Atelier des maquettes'
    assert resultat.json()[0]['calendar_id'] == identifiant
    evenements = (await db_session.execute(select(CalendarEvent).where(CalendarEvent.calendar_id == identifiant))).scalars().all()
    assert len(evenements) == 1
    assert evenements[0].summary == 'Atelier des maquettes'
    calendrier = await db_session.get(Calendar, identifiant)
    assert calendrier.synced_at is not None and calendrier.sync_status == 'idle'
    assert len(serveur_caldav[0]) == 2
