"""Un retrait acquitté pendant la préparation interdit le prochain transport."""
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from app.services.consentements import accord_valide, enregistrer_accord
from app.services.context import ContextWindow
from app.services.error_handler import ErreurPourEcran
from app.services.llm import LLMConfig, LLMProvider, LLMService
from app.services.providers.base import Message, StreamEvent


@pytest.mark.parametrize('suite', [False, True])
@pytest.mark.parametrize('purpose', ['llm', 'documents'])
@pytest.mark.parametrize('moment', ['fiches', 'fournisseur'])
async def test_retrait_avant_transport(client, monkeypatch, suite, purpose, moment):
    enregistrer_accord('llm', 'openai', True, '3', [])
    if purpose == 'documents':
        enregistrer_accord('documents', 'openai', True, '3', [])
    envois = []

    async def transport(*args, **kwargs):
        envois.append(args)
        yield StreamEvent(type='text', content='Parti')

    async def lire(*args):
        if moment == 'fiches':
            enregistrer_accord(purpose, 'openai', False, '3', [])
        return []

    async def preparer():
        if moment == 'fournisseur':
            enregistrer_accord(purpose, 'openai', False, '3', [])

    monkeypatch.setattr('app.services.memory_card_context.lire_pour_chat', lire)
    service = LLMService(LLMConfig(LLMProvider.OPENAI, 'modele-fictif', api_key='factice'))
    service._ensure_provider = AsyncMock(side_effect=preparer)
    service._provider = SimpleNamespace(stream=transport, continue_with_tool_results=transport)
    context = ContextWindow(messages=[Message(role='user', content='Demande fictive')])
    context.contient_documents = purpose == 'documents'
    context.memory_request = {'requete': 'fictif', 'scope': 'global', 'scope_id': None,
                              'conversation_id': None, 'purpose': purpose}
    appel = (service.continue_with_tool_results(context, '', [], []) if suite
             else service.stream_response_with_tools(context))
    erreur = None
    try:
        async for _ in appel:
            pass
    except ErreurPourEcran as exc:
        erreur = str(exc)
    assert not envois, 'Transport appelé malgré le retrait acquitté'
    assert erreur and purpose in erreur
    if purpose == 'documents':
        assert accord_valide('llm', 'openai')


@pytest.mark.parametrize('suite', [False, True])
async def test_adaptateur_revérifie_avant_http(client, suite):
    """Une attente interne à l'adaptateur ne dépasse pas la garde HTTP."""
    from contextlib import asynccontextmanager

    from app.services.providers.openai import OpenAIProvider

    enregistrer_accord('llm', 'openai', True, '3', [])
    envois = []

    @asynccontextmanager
    async def transport(*args, **kwargs):
        envois.append(args)
        yield None

    class AdaptateurAvecAttente(OpenAIProvider):
        async def stream(self, *args, **kwargs):
            enregistrer_accord('llm', 'openai', False, '3', [])
            async for event in super().stream(*args, **kwargs):
                yield event

    config = LLMConfig(LLMProvider.OPENAI, 'gpt-test', api_key='factice')
    service = LLMService(config)
    service._provider = AdaptateurAvecAttente(config, SimpleNamespace(stream=transport))
    context = ContextWindow(messages=[Message(role='user', content='Fictif')])
    appel = (service.continue_with_tool_results(context, '', [], []) if suite
             else service.stream_response_with_tools(context))
    erreur = None
    try:
        async for _ in appel:
            pass
    except ErreurPourEcran as exc:
        erreur = str(exc)
    assert not envois
    assert erreur and 'accord' in erreur
