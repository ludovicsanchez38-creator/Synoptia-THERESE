"""R1-3 : les outils intégrés écrivent uniquement après la carte confirmée."""
from unittest.mock import MagicMock

import pytest
from app.models.entities import Contact, Conversation
from app.routers.chat import _execute_tools_and_continue
from app.services.context import ContextWindow
from app.services.providers.base import ToolCall
from app.services.tool_confirmations import requires_confirmation
from app.services.workspace_tools import WORKSPACE_TOOLS, execute_workspace_tool

from tests.test_chat_tool_confirmation import _FakeLLM, _parse_chunks


def test_outils_integres_et_classes():
    noms = {t['function']['name'] for t in WORKSPACE_TOOLS}
    assert {'list_tasks', 'create_task', 'create_invoice'} <= noms
    assert requires_confirmation('list_tasks') is False
    assert requires_confirmation('create_task') is True
    assert requires_confirmation('create_invoice') is True


@pytest.mark.asyncio
@pytest.mark.parametrize('nom,args,collection', [
    ('create_task', {'title': 'Rappeler Marie', 'due_date': '2026-10-23T10:00:00'}, '/api/tasks/'),
    ('create_invoice', {'document_type': 'facture', 'lines': [{'description': 'Acompte', 'quantity': 1, 'unit_price_ht': 540, 'tva_rate': 20}]}, '/api/invoices'),
    ('create_invoice', {'document_type': 'devis', 'lines': [{'description': 'Conseil', 'quantity': 1, 'unit_price_ht': 100, 'tva_rate': 20}]}, '/api/invoices'),
])
async def test_carte_puis_creation_dans_le_module(client, db_session, nom, args, collection):
    contact = Contact(first_name='Marie', last_name='Recette')
    conv = Conversation(title='Actions de recette')
    db_session.add_all([contact, conv])
    await db_session.commit()
    args = dict(args)
    if nom == 'create_invoice':
        args['contact_id'] = contact.id
    outils = [t for t in WORKSPACE_TOOLS if t['function']['name'] == nom]
    assert outils, f'{nom} absent des outils intégrés'
    appel = ToolCall(id='appel', name=nom, arguments=args)
    chunks = _parse_chunks([c async for c in _execute_tools_and_continue(
        _FakeLLM(), MagicMock(), ContextWindow(messages=[]), '', [appel], outils,
        conv.id, 3, session=db_session,
    )])
    pending = next(c['confirmation'] for c in chunks if c['type'] == 'confirmation_required')
    assert (await client.get(collection)).json() == []
    reponse = await client.post('/api/chat/confirm-tool', json={
        'confirmation_id': pending['confirmation_id'], 'approved': True,
    })
    assert reponse.status_code == 200, reponse.text
    lignes = (await client.get(collection)).json()
    assert len(lignes) == 1, reponse.text
    if nom == 'create_task':
        assert lignes[0]['title'] == 'Rappeler Marie'
        liste = await execute_workspace_tool('list_tasks', {}, db_session)
        assert 'Rappeler Marie' in liste
    else:
        assert lignes[0]['document_type'] == args['document_type']
        assert lignes[0]['status'] == 'draft'
    seconde = await client.post('/api/chat/confirm-tool', json={
        'confirmation_id': pending['confirmation_id'], 'approved': True,
    })
    assert seconde.status_code == 404


@pytest.mark.asyncio
async def test_annuler_et_refuser_une_tache_sans_titre(client, db_session):
    from app.services.tool_confirmations import register_pending
    identifiant = register_pending('create_task', {'title': 'À annuler'})
    annulee = await client.post('/api/chat/confirm-tool', json={'confirmation_id': identifiant, 'approved': False})
    assert annulee.json()['status'] == 'cancelled'
    assert (await client.get('/api/tasks/')).json() == []
    resultat = await execute_workspace_tool('create_task', {'title': '  '}, db_session)
    assert 'false' in resultat
    assert (await client.get('/api/tasks/')).json() == []
