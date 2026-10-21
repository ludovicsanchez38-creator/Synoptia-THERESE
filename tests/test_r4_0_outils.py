"""R4-0b : capacités utiles conservées et fenêtre annoncée par le modèle."""
import json

import httpx
import pytest
from app.services.context import ContextWindow
from app.services.memory_card_context import alleger_outils_locaux
from app.services.memory_card_tools import MEMORY_CARD_TOOL
from app.services.providers.base import LLMConfig, LLMProvider, Message
from app.services.providers.ollama import OllamaProvider
from app.services.workspace_tools import WORKSPACE_TOOLS


def _context(question):
    return ContextWindow([Message('user', question)], system_prompt='Identité et consignes. ' * 160)


@pytest.mark.parametrize('question,noms', [
 ('Quel est mon agenda du jour ?', {'list_calendar_events', 'create_calendar_event'}),
 ('Lis mes mails', {'read_emails', 'search_emails'}),
 ('Liste mes tâches', {'list_tasks', 'create_task'}),
 ('Retrouve mes factures', {'search_invoices', 'invoice_totals'}),
])
def test_reduction_conserve_le_domaine_demande(monkeypatch, question, noms):
    from app.services import ollama_budget
    monkeypatch.setattr(ollama_budget, 'plafond_memoire', lambda: 8192)
    config = LLMConfig(LLMProvider.OLLAMA, 'qwen3:1.7b', max_tokens=3072)
    outils = [*WORKSPACE_TOOLS, MEMORY_CARD_TOOL]
    selection = alleger_outils_locaux(_context(question), config, outils)
    assert noms <= {t['function']['name'] for t in selection}
    assert len(selection) < len(outils)


def test_conserve_le_domaine_du_tour_precedent(monkeypatch):
    from app.services import ollama_budget
    monkeypatch.setattr(ollama_budget, 'plafond_memoire', lambda: 8192)
    config = LLMConfig(LLMProvider.OLLAMA, 'qwen3:1.7b', max_tokens=3072)
    context = _context('Et ensuite ?')
    context.memory_original_messages = [Message('user', 'Quel est mon agenda ?'), Message('assistant', 'Je consulte.'), *context.messages]
    selection = alleger_outils_locaux(context, config, [*WORKSPACE_TOOLS, MEMORY_CARD_TOOL])
    assert 'list_calendar_events' in {t['function']['name'] for t in selection}


@pytest.mark.asyncio
async def test_grand_poste_envoie_la_fenetre_api_show(monkeypatch):
    from app.services import ollama_budget
    monkeypatch.setattr(ollama_budget.os, 'sysconf', lambda cle: 4096 if cle == 'SC_PAGE_SIZE' else 4 * 1024 * 1024)
    appels = []
    def transport(request):
        appels.append(request)
        if request.url.path == '/api/show':
            return httpx.Response(200, json={'model_info': {'general.architecture': 'qwen3', 'qwen3.context_length': 40960}})
        body = json.loads(request.content)
        assert body['options']['num_ctx'] == 40960
        return httpx.Response(200, content=json.dumps({'message': {'content': 'Fictif'}, 'done': True}))
    async with httpx.AsyncClient(transport=httpx.MockTransport(transport)) as client:
        provider = OllamaProvider(LLMConfig(LLMProvider.OLLAMA, 'qwen3:1.7b', context_window=32000), client)
        await provider.actualiser_fenetre()
        events = [e async for e in provider.stream('Consignes', [{'role': 'user', 'content': 'Qui suis-je ?'}])]
    assert [r.url.path for r in appels] == ['/api/show', '/api/chat']
    assert not any(e.type == 'error' for e in events)
