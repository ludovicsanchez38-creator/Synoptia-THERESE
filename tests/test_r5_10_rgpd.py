"""Fermeture croisée : fiches, reçus, journal et notes dans le même périmètre."""
import asyncio
import json
from pathlib import Path
import pytest
from app.models.entities import Activity, Conversation, MemoryCard, Message
from app.models.database import get_session_context
from app.services import memory_cards, memory_tools
from app.services.tool_confirmations import register_pending
from sqlmodel import select
from tests.test_r5_9_notes import rendez_vous
from tests.test_r2_3_outil import fournisseur  # noqa: F401


@pytest.mark.asyncio
@pytest.mark.parametrize('action', ['contact', 'contact_cascade', 'projet', 'anonymisation', 'auto', 'purge'])
async def test_effacement_croise_sans_rappel_derive(client, db_session, monkeypatch, fournisseur, action):
    import app.routers.chat as chat
    contact, projet, event = await rendez_vous(db_session)
    fiche = await memory_cards.ecrire({'kind': 'fait', 'subject': 'sentinelle croisée', 'title': 'Fiche croisée',
        'content': 'SENTINELLE_R5_CROISEE', 'contact_id': contact.id, 'project_id': projet.id,
        'scope': 'project', 'scope_id': projet.id})
    async def executer(*args, **kwargs): return '{"success":true,"message_id":"recu-factice"}'
    monkeypatch.setattr(chat, 'execute_workspace_tool', executer)
    cid = register_pending('send_email', {'contact_id': contact.id, 'project_id': projet.id})
    await client.post('/api/chat/confirm-tool', json={'confirmation_id': cid, 'approved': True})
    await client.post('/api/crm/meeting-notes', json={'calendar_event_id': event.id, 'calendar_id': event.calendar_id,
        'description': 'SENTINELLE_R5_NOTE_CROISEE'})
    # Une annotation conserve le reçu original jusqu'à l'effacement de son périmètre.
    journal = (await client.get('/api/crm/activities?type=agent_action')).json()[0]
    assert (await client.post(f"/api/crm/activities/{journal['id']}/correction", json={'description': 'Correction professionnelle'})).status_code == 200
    conversation = Conversation(title='Vérification du dossier', project_id=projet.id, memory_scope='project')
    db_session.add(conversation)
    await db_session.commit()
    avant = await client.post('/api/chat/send', json={'conversation_id': conversation.id,
        'message': 'Que sais-tu de sentinelle ?', 'stream': True})
    assert avant.status_code == 200
    assert 'SENTINELLE_R5_CROISEE' in json.dumps(fournisseur[2][-1])
    export = (await client.get(f'/api/rgpd/export/{contact.id}')).json()
    assert fiche['id'] in {c['id'] for c in export['memory_cards']}
    assert len(export['activities']) == 3
    if action.startswith('contact'):
        rep = await client.delete(f'/api/memory/contacts/{contact.id}', params={'cascade': action == 'contact_cascade'})
    elif action == 'projet': rep = await client.delete(f'/api/memory/projects/{projet.id}')
    elif action == 'anonymisation': rep = await client.post(f'/api/rgpd/anonymize/{contact.id}', json={})
    elif action == 'auto':
        from app.services.rgpd_identite import anonymiser_la_personne
        from datetime import UTC, datetime
        await anonymiser_la_personne(db_session, contact, datetime.now(UTC))
        await db_session.commit()
        rep = None
    else: rep = await client.delete('/api/data/all', params={'confirm': True})
    assert rep is None or rep.status_code == 200
    async with get_session_context() as session:
        assert not (await session.execute(select(MemoryCard))).scalars().all()
        assert not (await session.execute(select(Activity).where(Activity.type.in_(['agent_action', 'note'])))).scalars().all()
        for message in (await session.execute(select(Message))).scalars():
            assert 'SENTINELLE_R5' not in (message.extra_data or '')
    assert (await client.get(f"/api/memory/cards/{fiche['id']}")).status_code == 404
    if action == 'purge':
        # La purge réinitialise le service de chat ; réinstaller le seul fournisseur factice.
        from app.services import llm
        llm._llm_service = fournisseur[0]
    rep = await client.post('/api/chat/send', json={'conversation_id': None if action == 'purge' else conversation.id,
        'message': 'Que sais-tu de sentinelle ?', 'stream': True})
    assert rep.status_code == 200
    assert 'SENTINELLE_R5' not in json.dumps(fournisseur[2][-1])
    from app.config import settings
    for fichier in Path(settings.data_dir).rglob('*'):
        if fichier.is_file(): assert b'SENTINELLE_R5' not in fichier.read_bytes(), fichier.name


@pytest.mark.asyncio
async def test_purge_attend_issue_du_journal_puis_efface_sans_trace_tardive(db_session, monkeypatch):
    from app.routers.chat import confirm_tool, ConfirmToolRequest
    from app.routers.data import delete_all_data
    import app.routers.chat as chat
    entree, reprendre = asyncio.Event(), asyncio.Event()
    async def executer(*args, **kwargs):
        entree.set()
        await reprendre.wait()
        return '{"success":true,"message_id":"recu-factice"}'
    monkeypatch.setattr(chat, 'execute_workspace_tool', executer)
    cid = register_pending('send_email', {})
    tache = asyncio.create_task(confirm_tool(ConfirmToolRequest(confirmation_id=cid, approved=True), db_session))
    await entree.wait()
    async with get_session_context() as session:
        assert len((await session.execute(select(Activity))).scalars().all()) == 1
    async with get_session_context() as session:
        purge = asyncio.create_task(delete_all_data(confirm=True, session=session))
        await asyncio.sleep(0.01)
        assert not purge.done()
        reprendre.set()
        await tache
        await purge
    async with get_session_context() as session:
        assert not (await session.execute(select(Activity))).scalars().all()
    assert not memory_tools._gestes_en_cours


@pytest.mark.asyncio
async def test_verification_du_rendez_vous_et_ecriture_serialisees_avec_effacement_projet(db_session, monkeypatch):
    from unittest.mock import AsyncMock
    from sqlalchemy import text
    from sqlalchemy.exc import OperationalError
    from app.routers import crm, memory
    from app.models.schemas import CreateActivityRequest
    from app.services import meeting_notes, project_sync_service
    _, projet, event = await rendez_vous(db_session)
    entree, reprendre = asyncio.Event(), asyncio.Event()
    verifier = meeting_notes.verifier_evenement
    async def retenir(session, extra):
        rdv = await verifier(session, extra)
        entree.set()
        await reprendre.wait()
        return rdv
    monkeypatch.setattr(meeting_notes, 'verifier_evenement', retenir)
    # Aucun dossier synchronisé dans cette fixture ; pas de transaction annexe.
    monkeypatch.setattr(project_sync_service, 'retirer_racine', AsyncMock())
    creation = asyncio.create_task(crm.create_activity(CreateActivityRequest(type='note', title='Note de rendez-vous',
        description='Note professionnelle', extra_data=json.dumps({'calendar_event_id': event.id, 'calendar_id': event.calendar_id})), db_session))
    await entree.wait()
    try:
        async with get_session_context() as session:
            await session.execute(text('PRAGMA busy_timeout=1'))
            p = await session.get(type(projet), projet.id)
            verrouille = False
            try:
                await memory._nettoyer_et_supprimer_projet(session, p)
            except OperationalError as exc:
                assert 'locked' in str(exc).lower()
                verrouille = True
            await session.rollback()
            assert verrouille, 'La relation vérifiée doit rester protégée jusqu’au commit de la note.'
    finally:
        reprendre.set()
        await creation
    async with get_session_context() as session:
        p = await session.get(type(projet), projet.id)
        await memory._nettoyer_et_supprimer_projet(session, p)
    async with get_session_context() as session:
        assert not (await session.execute(select(Activity))).scalars().all()
