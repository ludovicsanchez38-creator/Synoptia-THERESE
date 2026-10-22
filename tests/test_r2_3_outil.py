"""R2-3 : HTTP/SSE et vrai service LLM, fournisseur intégralement factice."""
import json
from copy import deepcopy
from unittest.mock import AsyncMock, MagicMock

import pytest
from app.models.entities import Message
from app.services import llm
from app.services.providers.base import LLMProvider, StreamEvent, ToolCall
from sqlmodel import select

from tests.test_p159_contexte_transmis import _evenements


@pytest.fixture
def fournisseur(monkeypatch):
    from app.routers import chat
    from app.services.memory_card_tools import MEMORY_CARD_TOOL
    captures = []
    actions = []

    class Factice:
        async def stream(self, system_prompt, messages, tools=None, **kwargs):
            captures.append(deepcopy({'system': system_prompt, 'messages': messages, 'tools': tools}))
            if actions:
                action = actions.pop(0)
                yield StreamEvent(type='tool_call', tool_call=ToolCall(id='appel-factice', name='upsert_memory_card', arguments=action))
                yield StreamEvent(type='done', stop_reason='tool_calls')
            else:
                yield StreamEvent(type='text', content='Réponse factice.')
                yield StreamEvent(type='done', stop_reason='end_turn')

        async def continue_with_tool_results(self, *args, **kwargs):
            yield StreamEvent(type='text', content='Réponse après outil.')
            yield StreamEvent(type='done', stop_reason='end_turn')

    service = llm.LLMService(llm.LLMConfig(LLMProvider.OLLAMA, 'modele-factice', context_window=128000))
    service._provider = Factice()
    monkeypatch.setattr(llm, '_llm_service', service)
    monkeypatch.setattr(llm.LLMService, '_resolve_with_circuit_breaker', lambda self: self.config)
    mcp = MagicMock()
    mcp.get_tools_for_llm.return_value = []
    monkeypatch.setattr(chat, 'get_mcp_service', lambda: mcp)
    monkeypatch.setattr(chat, '_extract_entities_background', AsyncMock())
    monkeypatch.setattr(chat, 'web_tools', lambda: [])
    monkeypatch.setattr(chat, 'MEMORY_TOOLS', [MEMORY_CARD_TOOL])
    return service, actions, captures


def action(**kwargs):
    return {'kind': 'preference', 'subject': 'rédaction', 'title': 'Rédaction',
            'content': 'Préfère des phrases courtes.'} | kwargs


@pytest.mark.asyncio
async def test_outil_autonome_recu_durable_identifiants(client, db_session, fournisseur):
    from app.services.memory_cards import lister
    from app.services.tool_confirmations import requires_confirmation
    assert not requires_confirmation('upsert_memory_card')
    assert requires_confirmation('serveur__upsert_memory_card')
    assert requires_confirmation('create_contact')
    fournisseur[1].append(action())
    rep = await client.post('/api/chat/send', json={'message': 'Préfère des phrases courtes.', 'stream': True})
    evenements = _evenements(rep.text)
    assert not any(e['type'] == 'confirmation_required' for e in evenements)
    recu = next(e['receipt'] for e in evenements if e['type'] == 'memory_receipt')
    assert set(recu) == {'id', 'version', 'operation'}
    assert (await lister())['items'][0]['id'] == recu['id']
    messages = (await db_session.execute(select(Message))).scalars().all()
    metadata = [json.loads(m.extra_data) for m in messages if m.extra_data]
    assert any(recu in d.get('memory_receipts', []) for d in metadata)
    assert 'Préfère des phrases courtes.' not in json.dumps(metadata, ensure_ascii=False)


@pytest.mark.asyncio
@pytest.mark.parametrize('message', ['Mon mot de passe est Factice!2026', 'Ma clé API est sk-test-factice123456', 'Il souffre de diabète'])
async def test_source_sensible_ne_devient_pas_fiche(client, db_session, fournisseur, message):
    from app.services.memory_cards import lister
    fournisseur[1].append(action(content=message))
    rep = await client.post('/api/chat/send', json={'message': message, 'stream': True})
    evenements = _evenements(rep.text)
    assert not (await lister())['items']
    assert not any(e['type'] == 'memory_receipt' for e in evenements)
    assert any('donnée sensible' in e.get('content', '') for e in evenements)


@pytest.mark.asyncio
async def test_memoire_desactivee_refus_visible(client, db_session, fournisseur):
    from app.services.memory_cards import lister
    fournisseur[1].append(action())
    rep = await client.post('/api/chat/send', json={'message': 'Préfère des phrases courtes.', 'stream': True, 'include_memory': False})
    assert not (await lister())['items']
    assert any('mémoire est désactivée' in e.get('content', '') for e in _evenements(rep.text))
    assert not any(e['type'] == 'memory_receipt' for e in _evenements(rep.text))
