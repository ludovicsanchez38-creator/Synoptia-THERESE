"""R5-6 : issue structurée, journal minimal et confidentialité immédiate."""
import json
from pathlib import Path
from datetime import UTC, datetime

import pytest
from app.models.entities import Activity, Contact, Conversation, Project
from app.services.tool_confirmations import register_pending
from sqlmodel import select


@pytest.mark.asyncio
@pytest.mark.parametrize('resultat,issue', [
    ({'success': False, 'error': 'Échec factice'}, 'echouee'),
    ({'success': True, 'message_id': 'recu-factice'}, 'envoyee'),
    ({'success': True}, 'indeterminee'),
    ('Envoyé selon une prose sans reçu', 'indeterminee'),
])
async def test_confirmation_journalise_issue_avant_traduction(client, db_session, monkeypatch, resultat, issue):
    import app.routers.chat as chat
    async def executer(*args, **kwargs):
        return json.dumps(resultat) if isinstance(resultat, dict) else resultat
    monkeypatch.setattr(chat, 'execute_workspace_tool', executer)
    conv = Conversation(title='Source factice')
    db_session.add(conv)
    await db_session.commit()
    cid = register_pending('send_email', {'body': 'CORPS_NON_RECOPIE', 'subject': 'OBJET_NON_RECOPIE'}, conv.id)
    rep = await client.post('/api/chat/confirm-tool', json={'confirmation_id': cid, 'approved': True})
    assert rep.status_code == 200
    lignes = (await client.get('/api/crm/activities?type=agent_action')).json()
    assert len(lignes) == 1
    trace = lignes[0]
    assert trace['conversation_id'] == conv.id and trace['execution_id'] == cid
    assert json.loads(trace['extra_data'])['outcome'] == issue
    assert 'NON_RECOPIE' not in json.dumps(trace)
    assert (await client.post('/api/chat/confirm-tool', json={'confirmation_id': cid, 'approved': True})).status_code == 404
    assert len((await client.get('/api/crm/activities?type=agent_action')).json()) == 1


@pytest.mark.asyncio
async def test_annulation_exception_et_recu_non_falsifiable(client, db_session, monkeypatch):
    import app.routers.chat as chat
    async def executer(*args, **kwargs):
        raise TimeoutError('DONNEE_A_NE_PAS_CONSERVER')
    monkeypatch.setattr(chat, 'execute_workspace_tool', executer)
    cid = register_pending('send_email', {})
    await client.post('/api/chat/confirm-tool', json={'confirmation_id': cid, 'approved': False})
    cid = register_pending('send_email', {})
    rep = await client.post('/api/chat/confirm-tool', json={'confirmation_id': cid, 'approved': True})
    assert rep.status_code == 200
    traces = (await client.get('/api/crm/activities?type=agent_action')).json()
    assert {json.loads(t['extra_data'])['outcome'] for t in traces} == {'annulee', 'indeterminee'}
    assert 'DONNEE_A_NE_PAS_CONSERVER' not in json.dumps(traces)
    # Le CRUD utilisateur ne doit pas inventer de reçu d'exécution.
    rep = await client.post('/api/crm/activities', json={'type': 'agent_action', 'title': 'Faux reçu'})
    assert rep.status_code == 422


@pytest.mark.asyncio
@pytest.mark.parametrize('champ', ['title', 'description', 'extra_data'])
async def test_garde_recursive_sans_trace(client, db_session, champ):
    personne = Contact(first_name='Fictive')
    db_session.add(personne)
    await db_session.commit()
    data = {'type': 'note', 'contact_id': personne.id, 'title': 'Note professionnelle'}
    valeur = 'mot de passe : fictif-interdit'
    data[champ] = json.dumps({'nested': [{'valeur': valeur}]}) if champ == 'extra_data' else valeur
    rep = await client.post('/api/crm/activities', json=data)
    assert rep.status_code == 422
    assert valeur not in rep.text
    assert not (await client.get('/api/crm/activities')).json()


@pytest.mark.asyncio
async def test_note_sans_contact_et_journal_sans_effet_crm(client, db_session, monkeypatch):
    import app.routers.chat as chat
    personne = Contact(first_name='Fictive', score=40, next_follow_up=datetime(2027, 1, 1, tzinfo=UTC))
    db_session.add(personne)
    await db_session.commit()
    async def executer(*args, **kwargs):
        return json.dumps({'success': True})
    monkeypatch.setattr(chat, 'execute_workspace_tool', executer)
    cid = register_pending('create_task', {'contact_id': personne.id})
    await client.post('/api/chat/confirm-tool', json={'confirmation_id': cid, 'approved': True})
    await db_session.refresh(personne)
    assert personne.score == 40 and personne.next_follow_up is not None
    rep = await client.post('/api/crm/activities', json={'type': 'note', 'title': 'Note générale'})
    assert rep.status_code == 200 and rep.json()['contact_id'] is None


@pytest.mark.asyncio
@pytest.mark.parametrize('action', ['contact', 'anonymisation', 'projet', 'purge'])
async def test_journal_export_effacement_et_chiffrement(client, db_session, monkeypatch, action):
    import app.routers.chat as chat
    from app.config import settings
    personne = Contact(first_name='Fictive')
    db_session.add(personne)
    await db_session.commit()
    projet = Project(name='Dossier fictif', contact_id=personne.id)
    db_session.add(projet)
    await db_session.commit()
    conv = Conversation(title='Source', project_id=projet.id)
    db_session.add(conv)
    await db_session.commit()
    async def executer(*args, **kwargs):
        return json.dumps({'success': True, 'message_id': 'recu-factice'})
    monkeypatch.setattr(chat, 'execute_workspace_tool', executer)
    cid = register_pending('send_email', {'contact_id': personne.id}, conv.id)
    await client.post('/api/chat/confirm-tool', json={'confirmation_id': cid, 'approved': True})
    trace = (await client.get('/api/crm/activities?type=agent_action')).json()[0]
    assert trace['project_id'] == projet.id
    assert trace['id'] in {a['id'] for a in (await client.get('/api/data/export')).json()['activities']}
    assert trace['id'] in {a['id'] for a in (await client.get(f'/api/rgpd/export/{personne.id}')).json()['activities']}
    note = await client.post('/api/crm/activities', json={'type': 'note', 'title': 'SENTINELLE_R5_JOURNAL', 'project_id': projet.id})
    assert note.status_code == 200
    for fichier in Path(settings.data_dir).rglob('*'):
        if fichier.is_file():
            assert b'SENTINELLE_R5_JOURNAL' not in fichier.read_bytes(), fichier.name
    if action == 'contact':
        rep = await client.delete(f'/api/memory/contacts/{personne.id}', params={'cascade': True})
    elif action == 'anonymisation':
        rep = await client.post(f'/api/rgpd/anonymize/{personne.id}', json={})
    elif action == 'projet':
        ensemble = await client.get(f'/api/memory/projects/{projet.id}/ensemble')
        assert ensemble.json()['activities']['total'] == 2
        rep = await client.delete(f'/api/memory/projects/{projet.id}')
    else:
        rep = await client.delete('/api/data/all', params={'confirm': True})
    assert rep.status_code == 200, rep.text
    assert not (await db_session.execute(select(Activity).where(Activity.type.in_(['agent_action', 'note'])))).scalars().all()


@pytest.mark.asyncio
async def test_correction_visible_sans_modifier_recu(client, db_session, monkeypatch):
    import app.routers.chat as chat
    async def executer(*args, **kwargs):
        return '{"success":true,"message_id":"recu-factice"}'
    monkeypatch.setattr(chat, 'execute_workspace_tool', executer)
    cid = register_pending('send_email', {})
    await client.post('/api/chat/confirm-tool', json={'confirmation_id': cid, 'approved': True})
    trace = (await client.get('/api/crm/activities?type=agent_action')).json()[0]
    rep = await client.post(f"/api/crm/activities/{trace['id']}/correction", json={'description': 'Correction professionnelle'})
    assert rep.status_code == 200, rep.text
    traces = (await client.get('/api/crm/activities')).json()
    originale = next(t for t in traces if t['id'] == trace['id'])
    assert originale['extra_data'] == trace['extra_data']
    assert originale['statut'] == 'annulee' and originale['remplace_id'] == rep.json()['id']
    assert rep.json()['description'] == 'Correction professionnelle'


def test_garde_journal_corpus_v1_sur_tous_champs():
    from fastapi import HTTPException
    from app.services.action_journal import verifier_texte
    from tests.test_r2_2_protection import SENSIBLES, ADMISSIBLES
    for valeur in SENSIBLES:
        for champ in range(3):
            args = ['Note professionnelle', None, None]
            args[champ] = json.dumps({'notes': [{'texte': valeur}]}) if champ == 2 else valeur
            with pytest.raises(HTTPException) as refus:
                verifier_texte(*args)
            assert valeur not in str(refus.value)
    for valeur in ADMISSIBLES:
        verifier_texte(valeur, valeur, json.dumps({'notes': [valeur]}))


@pytest.mark.parametrize('voie', ['desktop', 'alembic'])
def test_migration_ancienne_base_chiffree_sans_perdre_crm(tmp_path, voie):
    import importlib.util
    from alembic.migration import MigrationContext
    from alembic.operations import Operations
    from app.models.database import db_connect
    from app.models.activity_migration import migrer_activites
    from sqlalchemy import create_engine, inspect
    from sqlmodel import SQLModel
    chemin = tmp_path / 'activites.db'
    import sqlcipher3
    from app.models.database import _db_key_pragma
    def connecter():
        connexion = sqlcipher3.connect(str(chemin))
        connexion.execute(_db_key_pragma())
        return connexion
    moteur = create_engine('sqlite://', creator=connecter)
    with moteur.begin() as conn:
        SQLModel.metadata.create_all(conn, tables=[t for n, t in SQLModel.metadata.tables.items() if n != 'activities'])
        conn.execute(Contact.__table__.insert().values(**Contact(id='c').model_dump()))
        conn.exec_driver_sql('''CREATE TABLE activities(id VARCHAR PRIMARY KEY, contact_id VARCHAR NOT NULL REFERENCES contacts(id),
            type VARCHAR NOT NULL, title VARCHAR NOT NULL, description VARCHAR, statut VARCHAR NOT NULL,
            remplace_id VARCHAR REFERENCES activities(id), extra_data VARCHAR, created_at DATETIME NOT NULL)''')
        conn.exec_driver_sql("INSERT INTO activities VALUES ('a','c','note','SENTINELLE_R5_MIGRATION','Texte','en_vigueur',NULL,NULL,CURRENT_TIMESTAMP)")
    if voie == 'desktop':
        conn = db_connect(chemin)
        try:
            migrer_activites(conn)
            migrer_activites(conn)
        finally:
            conn.close()
    else:
        path = Path(__file__).resolve().parents[1] / 'src/backend/alembic/versions/e1f2a3b4c5d6_activity_journal.py'
        spec = importlib.util.spec_from_file_location('revision_r5', path)
        revision = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(revision)
        with moteur.begin() as conn:
            with Operations.context(MigrationContext.configure(conn)):
                revision.upgrade()
                revision.upgrade()
    with moteur.begin() as conn:
        colonnes = {c['name']: c for c in inspect(conn).get_columns('activities')}
        assert colonnes['contact_id']['nullable']
        assert set(colonnes) == set(Activity.__table__.columns.keys())
        assert conn.exec_driver_sql('SELECT title FROM activities WHERE id="a"').scalar() == 'SENTINELLE_R5_MIGRATION'
        conn.exec_driver_sql("INSERT INTO activities(id,type,title,statut,created_at) VALUES ('b','note','Sans contact','en_vigueur',CURRENT_TIMESTAMP)")
        assert not conn.exec_driver_sql('PRAGMA foreign_key_check').all()
    moteur.dispose()
    assert b'SENTINELLE_R5_MIGRATION' not in chemin.read_bytes()


@pytest.mark.asyncio
async def test_journal_sauvegarde_et_restauration_chiffrees(client, db_session, monkeypatch):
    import app.routers.chat as chat
    async def executer(*args, **kwargs):
        return '{"success":true,"message_id":"recu-factice"}'
    monkeypatch.setattr(chat, 'execute_workspace_tool', executer)
    cid = register_pending('send_email', {})
    await client.post('/api/chat/confirm-tool', json={'confirmation_id': cid, 'approved': True})
    trace = (await client.get('/api/crm/activities?type=agent_action')).json()[0]
    sauvegarde = await client.post('/api/data/backup', json={'password': 'Phrase-factice-R5-2026'})
    assert sauvegarde.status_code == 200, sauvegarde.text
    assert (await client.delete(f"/api/crm/activities/{trace['id']}")).status_code == 200
    nom = sauvegarde.json()['backup_name']
    rep = await client.post(f'/api/data/restore/{nom}?confirm=true', json={'password': 'Phrase-factice-R5-2026'})
    assert rep.status_code == 200, rep.text
    assert (await client.get('/api/crm/activities?type=agent_action')).json()[0]['id'] == trace['id']


@pytest.mark.asyncio
async def test_confirmation_avant_inscription_ne_survit_pas_a_la_purge(client, db_session, monkeypatch):
    import asyncio
    from app.services import memory_tools
    entree, reprendre = asyncio.Event(), asyncio.Event()
    original = memory_tools._proteger_le_geste
    async def retarder(coro):
        entree.set()
        await reprendre.wait()
        return await original(coro)
    monkeypatch.setattr(memory_tools, '_proteger_le_geste', retarder)
    cid = register_pending('send_email', {})
    from app.routers.chat import confirm_tool, ConfirmToolRequest
    tache = asyncio.create_task(confirm_tool(ConfirmToolRequest(confirmation_id=cid, approved=True), db_session))
    await entree.wait()
    async with memory_tools.creations_du_chat_suspendues():
        await memory_tools.attendre_les_gestes_de_creation()
    reprendre.set()
    assert (await tache)['status'] == 'cancelled'
    assert not (await client.get('/api/crm/activities?type=agent_action')).json()


@pytest.mark.asyncio
@pytest.mark.parametrize('recu,corps,issue', [('recu-factice', 'Corps professionnel', 'envoyee'),
    (None, 'Corps professionnel', 'indeterminee'), ('non-sollicite', '', 'echouee')])
async def test_issue_native_de_l_envoi_sans_classer_la_prose(client, db_session, monkeypatch, recu, corps, issue):
    from app.services import workspace_tools
    from unittest.mock import AsyncMock
    provider = AsyncMock()
    provider.send_message.return_value = recu
    fournir = AsyncMock(return_value=(provider, None))
    monkeypatch.setattr(workspace_tools, '_get_email_provider', fournir)
    cid = register_pending('send_email', {'to': 'fictif@example.test', 'subject': 'Objet fictif', 'body': corps})
    rep = await client.post('/api/chat/confirm-tool', json={'confirmation_id': cid, 'approved': True})
    assert rep.status_code == 200
    trace = (await client.get('/api/crm/activities?type=agent_action')).json()[0]
    assert json.loads(trace['extra_data'])['outcome'] == issue
    if not corps: fournir.assert_not_called()
    if recu is None: assert 'envoye' not in rep.json()['result'].lower()
