"""Un extrait garde sa provenance quand l'accord change pendant sa recherche."""
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from app.services.consentements import accord_valide, enregistrer_accord
from app.services.llm import LLMConfig, LLMProvider, LLMService
from app.services.providers.base import StreamEvent


@pytest.mark.parametrize('stream', [False, True])
@pytest.mark.parametrize('retrait', [True, False])
async def test_retrait_documents_pendant_recherche(client, monkeypatch, stream, retrait):
    from app.routers import chat

    enregistrer_accord('llm', 'openai', True, '3', [])
    enregistrer_accord('documents', 'openai', True, '3', [])
    envois = []

    async def chercher(**kwargs):
        if retrait:
            enregistrer_accord('documents', 'openai', False, '3', [])
        return [{'type': 'file', 'text': 'EXTRAIT_DOCUMENT_FICTIF',
                 'metadata': {'name': 'exemple.txt'}, 'score': 0.9}]

    async def transport(*args, **kwargs):
        envois.append(args)
        yield StreamEvent(type='text', content='Réponse fictive')

    service = LLMService(LLMConfig(LLMProvider.OPENAI, 'modele-fictif', api_key='factice'))
    service._provider = SimpleNamespace(stream=transport)
    service._ensure_provider = AsyncMock()
    monkeypatch.setattr(chat, 'get_llm_service', lambda: service)
    monkeypatch.setattr(chat, 'get_qdrant_service', lambda: SimpleNamespace(async_search=chercher))
    response = await client.post('/api/chat/send', json={
        'message': 'Résume le fichier', 'include_memory': True, 'stream': stream,
    })
    assert accord_valide('llm', 'openai')
    if retrait:
        assert not envois, 'Un extrait est parti après le retrait documents'
        assert 'documents' in response.text
    else:
        assert 'EXTRAIT_DOCUMENT_FICTIF' in str(envois), response.text
