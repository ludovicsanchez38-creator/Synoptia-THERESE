"""B-1319 : une recherche confirmée doit aboutir à une réponse sourcée."""
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
import app.routers.chat as chat
from app.services.context import ContextWindow
from app.services.llm import Message, StreamEvent
from app.services.tool_confirmations import register_pending


@pytest.mark.asyncio
async def test_recherche_confirmee_repond_et_ne_colle_pas_les_resultats(client, monkeypatch):
    brut = '[Source: web]\nURL: https://exemple.fr/aide\nAide de 500 euros.\n[End web]'
    recherche = AsyncMock(return_value=brut)
    monkeypatch.setattr(chat, 'execute_web_search', recherche)
    recus = []

    class Modele:
        config = None

        def prepare_context(self, messages):
            return ContextWindow(messages=messages)

        async def continue_with_tool_results(self, context, **kwargs):
            recus.append((context, kwargs))
            yield StreamEvent(type='text', content='L’aide est de 500 euros. [Source](https://exemple.fr/aide)')
            yield StreamEvent(type='done', input_tokens=40, output_tokens=20)

    monkeypatch.setattr(chat, 'get_llm_service', lambda: Modele())
    monkeypatch.setattr(chat, '_attribution', lambda _: ('test', 'test'))
    tracker = MagicMock()
    monkeypatch.setattr(chat, 'get_token_tracker', lambda: tracker)
    cid = register_pending('web_search', {
        'query': 'aide 2026', '_web_messages': [{'role': 'user', 'content': 'Quel est le montant de cette aide ?'}],
    })
    reponse = await client.post('/api/chat/confirm-tool', json={'confirmation_id': cid, 'approved': True})
    assert reponse.status_code == 200
    assert reponse.json()['result'] == 'L’aide est de 500 euros. [Source](https://exemple.fr/aide)'
    assert len(recus) == 1
    context, suite = recus[0]
    assert context.messages[-1].content == 'Quel est le montant de cette aide ?'
    assert suite['tool_results'][0].result == brut
    assert not suite['tools']  # aucune nouvelle action sans confirmation
    assert 'sources' in context.system_prompt
    tracker.record_usage.assert_called_once()


@pytest.mark.asyncio
async def test_annulation_ne_recherche_pas_et_ne_relance_pas_le_modele(client, monkeypatch):
    recherche = AsyncMock()
    modele = MagicMock()
    monkeypatch.setattr(chat, 'execute_web_search', recherche)
    monkeypatch.setattr(chat, 'get_llm_service', modele)
    cid = register_pending('web_search', {'query': 'aide'})
    reponse = await client.post('/api/chat/confirm-tool', json={'confirmation_id': cid, 'approved': False})
    assert reponse.json()['status'] == 'cancelled'
    recherche.assert_not_called()
    modele.assert_not_called()


@pytest.mark.asyncio
async def test_la_question_est_figee_avec_la_confirmation(monkeypatch):
    from app.services.llm import ToolCall
    from app.services.tool_confirmations import pop_pending

    class Modele:
        async def continue_with_tool_results(self, *args, **kwargs):
            yield SimpleNamespace(type='done', stop_reason='end_turn', assistant_content_brut=None)

    appel = ToolCall(id='web', name='web_search', arguments={'query': 'aide'})
    contexte = ContextWindow(messages=[Message(role='user', content='Quelle aide pour mon apprenti ?')])
    chunks = [chunk async for chunk in chat._execute_tools_and_continue(
        Modele(), None, contexte, '', [appel], [{'type': 'function', 'function': {'name': 'web_search'}}],
        'conv', 3, session=MagicMock(),
    )]
    import json
    carte = next(json.loads(c[6:])['confirmation'] for c in chunks if 'confirmation_required' in c)
    action = pop_pending(carte['confirmation_id'])
    assert action[1]['_web_messages'][-1]['content'] == 'Quelle aide pour mon apprenti ?'
