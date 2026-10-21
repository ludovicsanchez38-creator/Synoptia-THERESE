"""R4-0a : un échange français qui tient dans 8k doit partir entier."""
import json

import httpx
import pytest
from app.services.context import ContextWindow
from app.services.memory_card_context import borner_payload
from app.services.providers.base import LLMConfig, LLMProvider, Message
from app.services.providers.ollama import OllamaProvider


@pytest.mark.asyncio
async def test_petit_poste_accepte_une_charge_francaise_de_douze_ko(monkeypatch):
    from app.services import ollama_budget
    monkeypatch.setattr(ollama_budget, 'plafond_memoire', lambda: 8192)
    systeme = 'Consigne : réponds en français, garde ce profil intégral. ' * 190
    config = LLMConfig(LLMProvider.OLLAMA, 'qwen3:1.7b', context_window=40960)
    context = ContextWindow([Message('user', 'Qui suis-je ?')], system_prompt=systeme)
    borner_payload(context, [], config, [])
    assert context.system_prompt == systeme
    appels = []
    def transport(request):
        appels.append(json.loads(request.content))
        return httpx.Response(200, content=json.dumps({'message': {'content': 'Fictif'}, 'done': True}))
    async with httpx.AsyncClient(transport=httpx.MockTransport(transport)) as client:
        provider = OllamaProvider(config, client)
        events = [e async for e in provider.stream(context.system_prompt, context.to_openai_format())]
    assert len(appels) == 1
    assert appels[0]['messages'][0]['content'] == systeme
    assert not any(e.type == 'error' for e in events)
