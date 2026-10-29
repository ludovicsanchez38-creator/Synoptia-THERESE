"""Deux tours API : les citations restent documentaires après persistance."""
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from app.models.database import get_sync_session
from app.models.entities import Conversation, Message, Preference
from app.services.consentements import accord_valide, enregistrer_accord
from app.services.llm import LLMConfig, LLMProvider, LLMService
from app.services.providers.base import StreamEvent
from sqlmodel import select


@pytest.mark.parametrize('stream', [False, True])
@pytest.mark.parametrize('retrait', [True, False])
@pytest.mark.parametrize('destination', ['openai', 'mistral'])
async def test_citation_deux_tours(client, monkeypatch, stream, retrait, destination):
    from app.routers import chat

    for purpose in ('llm', 'documents'):
        enregistrer_accord(purpose, 'openai', True, '3', [])
    with get_sync_session() as session:
        session.merge(Preference(key='auto_extract_entities', value='false'))
        session.commit()
    envois = []
    extrait = 'EXTRAIT_FICHIER_CONFIDENTIEL_T4'

    async def chercher(**kwargs):
        return [{'type': 'file', 'text': extrait, 'metadata': {'name': 'temoin.txt'}, 'score': 0.99}]

    async def transport(*args, **kwargs):
        envois.append(str(args))
        yield StreamEvent(type='text', content=f'Le fichier temoin.txt indique : « {extrait} ».' if len(envois) == 1 else 'Réponse suivante.')

    service = LLMService(LLMConfig(LLMProvider.OPENAI, 'modele-fictif', api_key='factice'))
    service._provider = SimpleNamespace(stream=transport)
    service._ensure_provider = AsyncMock()
    monkeypatch.setattr(chat, 'get_llm_service', lambda: service)
    recherche = AsyncMock(side_effect=chercher)
    monkeypatch.setattr(chat, 'get_qdrant_service', lambda: SimpleNamespace(async_search=recherche))
    premier = await client.post('/api/chat/send', json={
        'message': 'Cite le fichier', 'include_memory': True, 'stream': stream, 'disable_tools': True,
    })
    assert premier.status_code == 200
    assert extrait in premier.text
    assert extrait in envois[0]
    with get_sync_session() as session:
        reponse = session.exec(select(Message).where(Message.role == 'assistant')).all()[-1]
        conversation = reponse.conversation_id
        provenance = json.loads(reponse.extra_data or '{}').get('provenance_documents')
    if retrait:
        enregistrer_accord('documents', 'openai', False, '3', [])
    if destination != 'openai':
        service.config.provider = LLMProvider(destination)
        enregistrer_accord('llm', destination, True, '3', [])
        if not retrait:
            enregistrer_accord('documents', destination, True, '3', [])
    recherche.reset_mock()
    second = await client.post('/api/chat/send', json={
        'message': 'Bonjour', 'conversation_id': conversation, 'include_memory': False,
        'stream': stream, 'disable_tools': True,
    })
    assert accord_valide('llm', 'openai')
    assert second.status_code == 200
    assert len(envois) == 2, second.text
    recherche.assert_not_called()
    if retrait:
        assert extrait not in envois[1], 'La citation enregistrée est repartie sans accord documents'
        assert 'historique' in second.text and 'accord' in second.text
    else:
        assert extrait in envois[1]
    assert provenance == 'documents'


@pytest.mark.parametrize('stream', [False, True])
@pytest.mark.parametrize('traces, attendu', [
    (None, 'inconnue'), ('invalide', 'inconnue'),
    ({'sources': [{'title': 'temoin.txt'}]}, 'documents'),
    ({'citations': ['temoin.txt']}, 'documents'),
    ({'attachments': [{'name': 'temoin.txt', 'path': '/fictif/absent'}]}, 'documents'),
    ({'provenance_documents': 'sans_document'}, 'sans_document'),
])
async def test_historique_ancien_sans_accord_documents(client, monkeypatch, stream, traces, attendu):
    from app.routers import chat

    enregistrer_accord('llm', 'openai', True, '3', [])
    extrait = 'CONTENU_ANCIEN_FICTIF'
    with get_sync_session() as session:
        session.merge(Preference(key='auto_extract_entities', value='false'))
        conv = Conversation(title='Historique fictif')
        session.add(conv)
        session.flush()
        message = Message(conversation_id=conv.id, role='assistant', content=extrait,
                          extra_data=json.dumps(traces) if isinstance(traces, dict) else traces)
        session.add(message)
        session.commit()
        identifiant, conversation = message.id, conv.id
    envois = []

    async def transport(*args, **kwargs):
        envois.append(str(args))
        yield StreamEvent(type='text', content='Réponse fictive')

    service = LLMService(LLMConfig(LLMProvider.OPENAI, 'modele-fictif', api_key='factice'))
    service._provider = SimpleNamespace(stream=transport)
    service._ensure_provider = AsyncMock()
    monkeypatch.setattr(chat, 'get_llm_service', lambda: service)
    response = await client.post('/api/chat/send', json={
        'message': 'Bonjour', 'conversation_id': conversation, 'stream': stream,
        'include_memory': False, 'disable_tools': True,
    })
    assert response.status_code == 200
    assert len(envois) == 1
    assert (extrait in envois[0]) == (attendu == 'sans_document')
    if attendu != 'sans_document':
        assert 'historique' in response.text and 'accord' in response.text
    with get_sync_session() as session:
        assert json.loads(session.get(Message, identifiant).extra_data)['provenance_documents'] == attendu
