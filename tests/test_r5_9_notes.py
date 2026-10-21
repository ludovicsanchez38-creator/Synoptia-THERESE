"""Notes de rendez-vous : événement vérifié, contact facultatif, RGPD immédiat."""
import json
from pathlib import Path
import pytest
from app.models.entities import Activity, Calendar, CalendarEvent, Contact, Project
from sqlmodel import select


async def rendez_vous(db_session):
    contact = Contact(first_name='Fictive')
    db_session.add(contact)
    await db_session.commit()
    projet = Project(name='Dossier fictif', contact_id=contact.id)
    calendrier = Calendar(id='agenda-factice', summary='Agenda fictif')
    db_session.add_all([projet, calendrier])
    await db_session.commit()
    event = CalendarEvent(id='rdv-factice', calendar_id=calendrier.id, project_id=projet.id, summary='Rendez-vous fictif')
    db_session.add(event)
    await db_session.commit()
    return contact, projet, event


@pytest.mark.asyncio
@pytest.mark.parametrize('avec_contact', [False, True])
async def test_note_evenement_obligatoire_projet_herite_et_remplacement(client, db_session, avec_contact):
    contact, projet, event = await rendez_vous(db_session)
    data = {'calendar_event_id': event.id, 'calendar_id': event.calendar_id, 'description': 'SENTINELLE_R5_NOTE'}
    if avec_contact:
        data['contact_id'] = contact.id
    assert (await client.post('/api/crm/meeting-notes', json={'description': 'Sans événement'})).status_code == 422
    assert (await client.post('/api/crm/meeting-notes', json=data | {'calendar_id': 'autre-agenda'})).status_code == 404
    assert (await client.post('/api/crm/meeting-notes', json=data | {'contact_id': 'inconnu'})).status_code == 404
    rep = await client.post('/api/crm/meeting-notes', json=data)
    assert rep.status_code == 200, rep.text
    note = rep.json()
    assert note['project_id'] == projet.id
    assert note['contact_id'] == (contact.id if avec_contact else None)
    assert json.loads(note['extra_data'])['calendar_event_id'] == event.id
    # La création ancienne depuis l'agenda passe par la même validation.
    ancienne = await client.post('/api/crm/activities', json={'type': 'note', 'title': 'Note de séance',
        'extra_data': json.dumps({'calendar_event_id': event.id, 'calendar_id': event.calendar_id})})
    assert ancienne.status_code == 200 and ancienne.json()['project_id'] == projet.id
    corrigee = await client.post(f"/api/crm/activities/{note['id']}/correction", json={'description': 'Correction professionnelle'})
    assert corrigee.status_code == 200
    assert json.loads(corrigee.json()['extra_data'])['calendar_event_id'] == event.id
    notes = (await client.get('/api/crm/activities?meeting_notes=true')).json()
    assert {n['id'] for n in notes} == {note['id'], ancienne.json()['id'], corrigee.json()['id']}
    await db_session.delete(event)
    await db_session.commit()
    notes = (await client.get('/api/crm/activities?meeting_notes=true')).json()
    assert len(notes) == 3 and all(n['event_deleted'] for n in notes)
    from app.config import settings
    for fichier in Path(settings.data_dir).rglob('*'):
        if fichier.is_file():
            assert b'SENTINELLE_R5_NOTE' not in fichier.read_bytes(), fichier.name


@pytest.mark.asyncio
@pytest.mark.parametrize('action', ['contact', 'contact_cascade', 'anonymisation', 'auto', 'projet', 'purge'])
async def test_notes_export_effacement_anonymisation_et_purge(client, db_session, action):
    contact, projet, event = await rendez_vous(db_session)
    rep = await client.post('/api/crm/meeting-notes', json={'calendar_event_id': event.id,
        'calendar_id': event.calendar_id, 'description': 'Note professionnelle sans contact'})
    assert rep.status_code == 200, rep.text
    note = rep.json()
    assert note['id'] in {n['id'] for n in (await client.get('/api/data/export')).json()['activities']}
    assert note['id'] in {n['id'] for n in (await client.get(f'/api/rgpd/export/{contact.id}')).json()['activities']}
    if action.startswith('contact'):
        rep = await client.delete(f'/api/memory/contacts/{contact.id}', params={'cascade': action == 'contact_cascade'})
    elif action == 'anonymisation':
        rep = await client.post(f'/api/rgpd/anonymize/{contact.id}', json={})
    elif action == 'auto':
        from app.services.rgpd_identite import anonymiser_la_personne
        from datetime import UTC, datetime
        await anonymiser_la_personne(db_session, contact, datetime.now(UTC))
        await db_session.commit()
        rep = None
    elif action == 'projet':
        rep = await client.delete(f'/api/memory/projects/{projet.id}')
    else:
        rep = await client.delete('/api/data/all', params={'confirm': True})
    assert rep is None or rep.status_code == 200
    assert not (await db_session.execute(select(Activity).where(Activity.type == 'note'))).scalars().all()


@pytest.mark.asyncio
async def test_note_sensible_refusee_sans_trace(client, db_session):
    _, _, event = await rendez_vous(db_session)
    rep = await client.post('/api/crm/meeting-notes', json={'calendar_event_id': event.id,
        'calendar_id': event.calendar_id, 'description': 'Il souffre de diabète'})
    assert rep.status_code == 422 and 'diabète' not in rep.text
    assert not (await client.get('/api/crm/activities?meeting_notes=true')).json()


@pytest.mark.asyncio
async def test_anciennes_notes_reliees_une_seule_fois_sans_copie(client, db_session):
    from app.models.database import apply_adhoc_migrations
    from app.config import settings
    contact, projet, event = await rendez_vous(db_session)
    ancienne = Activity(type='note', title='Note ancienne', contact_id=contact.id,
        extra_data=json.dumps({'calendar_event_id': event.id, 'calendar_id': event.calendar_id}))
    db_session.add(ancienne)
    await db_session.commit()
    apply_adhoc_migrations(settings.db_path)
    apply_adhoc_migrations(settings.db_path)
    await db_session.refresh(ancienne)
    assert ancienne.project_id == projet.id
    assert json.loads(ancienne.extra_data)['meeting_note_v'] == 1
    assert len((await db_session.execute(select(Activity))).scalars().all()) == 1


@pytest.mark.asyncio
async def test_note_restauration_et_correction_restent_dans_la_meme_branche(client, db_session):
    _, _, event = await rendez_vous(db_session)
    note = (await client.post('/api/crm/meeting-notes', json={'calendar_event_id': event.id,
        'calendar_id': event.calendar_id, 'description': 'Note à restaurer'})).json()
    sauvegarde = (await client.post('/api/data/backup', json={'password': 'Phrase-factice-R5-Notes'})).json()
    await client.delete(f"/api/crm/activities/{note['id']}")
    assert not (await client.get('/api/crm/activities?meeting_notes=true')).json()
    rep = await client.post(f"/api/data/restore/{sauvegarde['backup_name']}?confirm=true", json={'password': 'Phrase-factice-R5-Notes'})
    assert rep.status_code == 200
    assert (await client.get('/api/crm/activities?meeting_notes=true')).json()[0]['id'] == note['id']
