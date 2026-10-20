"""R1-1 : une sélection de modèle conserve l'historique jusqu'au fournisseur."""
from copy import deepcopy
from unittest.mock import AsyncMock, MagicMock

import pytest
from app.services import llm
from app.services.modeles_catalogue import CATALOGUE
from app.services.providers.base import LLMProvider, StreamEvent

from tests.test_p159_contexte_transmis import _evenements, _fil


@pytest.mark.asyncio
@pytest.mark.parametrize('provider,model', [
    ('anthropic', 'claude-haiku-5-5'), ('anthropic', 'claude-sonnet-5-5'),
    ('openai', 'gpt-6.1-sol'), ('gemini', 'gemini-3.8-flash'),
    ('mistral', 'mistral-large-latest'), ('grok', 'grok-4.7'),
    ('openrouter', 'anthropic/claude-sonnet-5-5'), ('ollama', 'modele-factice'),
    *[(nom, CATALOGUE[nom].modeles[0]) for nom in (
        'perplexity', 'deepseek', 'infomaniak', 'glm', 'kimi', 'qwen', 'minimax',
    )],
])
async def test_selection_puis_chat_transmet_les_deux_messages(
    client, db_session, monkeypatch, provider, model,
):
    from app.routers import chat
    from app.services.modeles_catalogue import fenetre_de_contexte

    conv = await _fil(db_session, 2)
    charges = []

    class Fournisseur:
        async def stream(self, system_prompt, messages, tools, **kwargs):
            charges.append(deepcopy(messages))
            yield StreamEvent(type='text', content='Le mot est pivoine.')
            yield StreamEvent(type='done', stop_reason='end_turn')

    # On conserve le constructeur ET la conversion du vrai service.
    monkeypatch.setattr(llm, '_cle_depuis_environnement', lambda _: None)
    monkeypatch.setattr(llm.LLMService, '_get_system_prompt_with_identity', lambda _: 'Tu es Thérèse.')
    monkeypatch.setattr(llm.LLMService, '_resolve_with_circuit_breaker', lambda self: self.config)
    mcp = MagicMock()
    mcp.get_tools_for_llm.return_value = []
    monkeypatch.setattr(chat, 'get_mcp_service', lambda: mcp)
    monkeypatch.setattr(chat, '_extract_entities_background', AsyncMock())
    monkeypatch.setattr(chat, 'web_tools', lambda: [])
    monkeypatch.setattr(llm, '_llm_service', None)
    selection = await client.post('/api/config/llm', json={'provider': provider, 'model': model})
    assert selection.status_code == 200, selection.text
    service = llm.get_llm_service()
    service._provider = Fournisseur()
    reponse = await client.post('/api/chat/send', json={
        'conversation_id': conv, 'message': 'Quel mot ?', 'stream': True,
        'include_memory': False, 'disable_tools': True,
    })
    assert reponse.status_code == 200, reponse.text
    assert len(charges) == 1, reponse.text
    conversation = [m for m in charges[0] if m['role'] != 'system']
    if provider == 'gemini':
        textes = [m['parts'][0]['text'] for m in conversation]
    else:
        textes = [m['content'] for m in conversation]
    assert len(textes) == 3, textes
    assert textes[0].startswith('passe-00-')
    assert textes[1].startswith('passe-01-')
    assert textes[2] == 'Quel mot ?'
    done = next(e for e in _evenements(reponse.text) if e['type'] == 'done')
    assert done['contexte'] == {'messages_relus': 2, 'messages_transmis': 2}
    assert service.config.context_window == fenetre_de_contexte(provider, model)
    assert service.config.provider == LLMProvider(provider)
