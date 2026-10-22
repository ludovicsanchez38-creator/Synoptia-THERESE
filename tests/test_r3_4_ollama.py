"""R3 : fenêtre envoyée et garde avant transport, sans réseau."""
import json

import httpx
import pytest
from app.services.context import ContextWindow
from app.services.error_handler import ErreurPourEcran
from app.services.memory_card_context import borner_payload
from app.services.providers.base import LLMConfig, LLMProvider, Message, ToolCall, ToolResult
from app.services.providers.ollama import OllamaProvider

from tests.test_r2_3_outil import fournisseur  # noqa: F401


def test_r2_utilise_la_fenetre_reellement_envoyee():
    config = LLMConfig(LLMProvider.OLLAMA, 'qwen3:8b', context_window=128000)
    provider = OllamaProvider(config, None)
    fenetre = provider._build_request_body('Système', [])['options']['num_ctx']
    contexte = ContextWindow([Message('user', 'Question')], system_prompt='S' * (4 * fenetre))
    with pytest.raises(ErreurPourEcran):
        borner_payload(contexte, [], config, [])


@pytest.mark.asyncio
async def test_aucun_transport_si_le_systeme_ne_tient_pas():
    appels = []
    async def transport(request):
        appels.append(request)
        return httpx.Response(200, content=json.dumps({'message': {'content': 'Ne doit pas arriver'}, 'done': True}))
    async with httpx.AsyncClient(transport=httpx.MockTransport(transport)) as client:
        provider = OllamaProvider(LLMConfig(LLMProvider.OLLAMA, 'qwen3:8b'), client)
        events = [e async for e in provider.stream('Identité ' * 30000, [{'role': 'user', 'content': 'Qui suis-je ?'}])]
    assert not appels
    assert any(e.type == 'error' and 'fenêtre' in e.content.lower() for e in events)


@pytest.mark.asyncio
@pytest.mark.parametrize('memoire', [True, False])
@pytest.mark.parametrize('stream', [True, False])
async def test_refus_a_lecran_meme_sans_fiches(client, db_session, fournisseur, monkeypatch, memoire, stream):
    monkeypatch.setattr(fournisseur[0], '_get_system_prompt_with_identity', lambda: 'Identité ' * 30000)
    rep = await client.post('/api/chat/send', json={'message': 'Qui suis-je ?',
        'include_memory': memoire, 'stream': stream})
    assert rep.status_code == 200
    assert not fournisseur[2]
    if stream:
        affichage = ''.join(json.loads(l[6:]).get('content', '')
            for l in rep.text.splitlines() if l.startswith('data: '))
    else:
        affichage = rep.json()['content']
    assert 'fenêtre' in affichage.lower()


@pytest.mark.asyncio
async def test_continuation_trop_longue_refuse_avant_transport():
    async with httpx.AsyncClient(transport=httpx.MockTransport(lambda r: pytest.fail('Aucun appel attendu'))) as client:
        provider = OllamaProvider(LLMConfig(LLMProvider.OLLAMA, 'qwen3:8b'), client)
        events = [e async for e in provider.continue_with_tool_results('Identité',
            [{'role': 'user', 'content': 'Question'}], '', [ToolCall(id='1', name='read_file', arguments={})],
            [ToolResult(tool_call_id='1', result={'texte': 'F' * 100000})])]
    assert any(e.type == 'error' and 'fenêtre' in e.content.lower() for e in events)


@pytest.mark.asyncio
async def test_faux_transport_verifie_systeme_integral_et_num_ctx_coherent():
    systeme = 'Identité fictive. ' + 'Projet détaillé. ' * 160 + 'Règle 3 : LOUTRE-VIOLETTE. THERESE.md : PAPILLON-CUIVRE.'
    appels = []
    def transport(request):
        body = json.loads(request.content)
        appels.append(body)
        assert body['messages'][0]['content'] == systeme
        charge = {k: body[k] for k in ('messages', 'tools') if k in body}
        cout = len(json.dumps(charge, ensure_ascii=False).encode()) + 1024
        from app.services.ollama_budget import estimer_jetons, fenetre_ollama
        cout = estimer_jetons(json.dumps(charge, ensure_ascii=False)) + 1024
        assert cout + body['options']['num_predict'] <= body['options']['num_ctx'] == fenetre_ollama(provider.config)
        return httpx.Response(200, content=json.dumps({'message': {'content': 'Réponse fictive.'},
            'done': True, 'prompt_eval_count': 123, 'eval_count': 4}))
    async with httpx.AsyncClient(transport=httpx.MockTransport(transport)) as client:
        provider = OllamaProvider(LLMConfig(LLMProvider.OLLAMA, 'qwen3:8b'), client)
        events = [e async for e in provider.stream(systeme, [{'role': 'user', 'content': 'Qui suis-je ?'}])]
    assert len(appels) == 1
    assert next(e for e in events if e.type == 'done').input_tokens == 123


def test_petites_machines_et_petite_fenetre_modele(monkeypatch):
    from app.services import ollama_budget
    monkeypatch.setattr(ollama_budget.os, 'sysconf', lambda cle: 4096 if cle == 'SC_PAGE_SIZE' else 1024 * 1024, raising=False)
    assert ollama_budget.plafond_memoire() == 8192
    config = LLMConfig(LLMProvider.OLLAMA, 'factice', context_window=2048, max_tokens=256)
    assert ollama_budget.fenetre_ollama(config) == 2048
    monkeypatch.setattr(ollama_budget.os, 'sysconf', lambda cle: 4096 if cle == 'SC_PAGE_SIZE' else 4 * 1024 * 1024, raising=False)
    assert ollama_budget.plafond_memoire() == 131072


@pytest.mark.asyncio
async def test_routeur_allege_outils_et_garde_identite_consignes(client, db_session, fournisseur, monkeypatch):
    from app.services import ollama_budget
    from app.services.memory_card_context import compter_payload
    monkeypatch.setattr(ollama_budget, 'plafond_memoire', lambda: 8192)
    contexte = 'Règle 1 : tutoyer.\n' + 'Projet fictif. ' * 155 + '\nRègle 3 : LOUTRE-VIOLETTE.'
    await client.post('/api/config/profile', json={'name': 'Camille Fictive', 'context': contexte})
    await client.post('/api/config/therese-md', json={'content': 'Témoin : PAPILLON-CUIVRE.'})
    fournisseur[0].config = LLMConfig(LLMProvider.OLLAMA, 'qwen3:8b', context_window=32768, max_tokens=2048)
    rep = await client.post('/api/chat/send', json={'message': 'Quel est mon agenda ?', 'stream': True})
    assert 'outils disponibles' in rep.text
    payload = fournisseur[2][-1]
    assert contexte in payload['system'] and 'PAPILLON-CUIVRE' in payload['system']
    assert 'list_calendar_events' in {t['function']['name'] for t in payload['tools']}
    assert len(payload['tools']) < len(__import__('app.services.workspace_tools', fromlist=['WORKSPACE_TOOLS']).WORKSPACE_TOOLS)
    assert 'web_search**' not in payload['system']
    wire = OllamaProvider(fournisseur[0].config, None)._build_request_body(payload['system'], payload['messages'], payload['tools'])
    assert wire['options']['num_ctx'] == 8192
    contexte_final = ContextWindow([Message('user', 'Qui suis-je ?')], system_prompt=payload['system'])
    assert compter_payload(contexte_final, fournisseur[0].config, payload['tools']) + 2048 <= 8192
