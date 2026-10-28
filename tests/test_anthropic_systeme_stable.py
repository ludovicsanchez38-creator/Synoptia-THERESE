"""Le faux serveur applique la liaison des signatures au préfixe documentée
par Anthropic le 28/10/2026 ; aucun appel réseau, aucune clé réelle.
"""
import json
from unittest.mock import AsyncMock

import pytest
from app.services.context import ContextWindow, Message
from app.services.llm import LLMService
from app.services.providers.anthropic import AnthropicProvider
from app.services.providers.base import LLMConfig, LLMProvider, ToolResult

from tests.test_anthropic_blocs_de_reflexion import _flux, _outil, _reflexion, _texte
from tests.test_provider_tools import _collect, _FakeClient, _FakeStreamResponse


class ServeurAvecSignature(_FakeClient):
    def stream(self, method, url, **kwargs):
        body = kwargs['json']
        if not self.requests:
            response = _FakeStreamResponse(_flux(_reflexion(0, 'signature-factice'), _outil(1, 'tu1', 'memory_write', {})))
        elif any(m['role'] == 'assistant' for m in body['messages']) and body['system'] != self.requests[0]['json']['system']:
            response = _FakeStreamResponse([], 400, json.dumps({'error': {
                'type': 'invalid_request_error',
                'message': 'Invalid `signature` in `thinking` block. The block is bound to a different conversation.',
            }}).encode())
        else:
            response = _FakeStreamResponse(_flux(_texte(0, 'Bien retenu.')))
        self._responses = [response]
        return super().stream(method, url, **kwargs)


@pytest.mark.asyncio
@pytest.mark.parametrize('initialement_vide', [True, False])
async def test_fiche_ecrite_pendant_outil_attend_le_prochain_tour(monkeypatch, initialement_vide):
    from app.services import memory_card_context, memory_card_tools
    ancienne = {'id': 'f1', 'kind': 'preference', 'content': 'Avant', 'message_id': 'm0'}
    fiches = [] if initialement_vide else [ancienne]
    lecture = AsyncMock(side_effect=lambda *a: list(fiches))
    monkeypatch.setattr(memory_card_context, 'lire_pour_chat', lecture)
    monkeypatch.setattr(memory_card_tools, 'message_du_tour', AsyncMock(return_value='m1'))
    config = LLMConfig(LLMProvider.ANTHROPIC, 'claude-opus-5-5', api_key='factice')
    client = ServeurAvecSignature()
    service = LLMService(config)
    service._provider = AnthropicProvider(config, client=client)
    monkeypatch.setattr(service, '_ensure_provider', AsyncMock())
    monkeypatch.setattr(service, '_resolve_with_circuit_breaker', lambda: config)
    contexte = ContextWindow(system_prompt='Tu es THÉRÈSE.', messages=[Message(role='user', content='Retiens ma préférence')])
    memory_card_context.attacher_relecture(contexte, contexte.messages, None,
        scope='global', scope_id=None, conversation_id='c1', query='préférence', grants=['llm:anthropic'])
    premier = await _collect(service.stream_response_with_tools(contexte, []))
    evenement = next(e for e in premier if e.type == 'tool_call')
    appel = evenement.tool_call
    fiches[:] = [ancienne | {'content': 'Nouvelle préférence', 'message_id': 'm1'}]
    suite = await _collect(service.continue_with_tool_results(contexte, '', [appel],
        [ToolResult(tool_call_id='tu1', result='Fiche enregistrée')], [],
        assistant_content_brut=evenement.assistant_content_brut))
    assert not [e for e in suite if e.type == 'error'], 'le serveur simulé a refusé le système modifié'
    assert client.requests[1]['json']['system'] == client.requests[0]['json']['system']
    assert client.requests[1]['json']['messages'][1]['content'][0]['signature'] == 'signature-factice'
    assert lecture.await_count == 1
    # Le tour utilisateur suivant reprend les fiches persistées.
    await _collect(service.stream_response_with_tools(contexte, []))
    assert 'Nouvelle préférence' in json.dumps(client.requests[2]['json']['system'], ensure_ascii=False)
    assert lecture.await_count == 2
