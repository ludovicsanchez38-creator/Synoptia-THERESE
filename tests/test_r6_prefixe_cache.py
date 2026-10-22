"""Préfixes réutilisables et charge réduite, sans connexion à Anthropic."""
import copy
import json
from datetime import datetime
from unittest.mock import AsyncMock

import httpx
import pytest
from app.services import llm, memory_card_context, user_profile
from app.services.memory_card_context import borner_payload
from app.services.modeles_catalogue import CATALOGUE
from app.services.providers.anthropic import AnthropicProvider
from app.services.providers.base import LLMConfig, LLMProvider, Message
from app.services.user_profile import UserProfile
from app.services.web_search import WEB_SEARCH_TOOL
from app.services.workspace_tools import (
    GENERATE_DOCUMENT_TOOL,
    INVOICE_TOTALS_TOOL,
    SEARCH_INVOICES_TOOL,
)


@pytest.mark.asyncio
@pytest.mark.parametrize('reprise', [False, True])
async def test_prefixe_cache_et_comptage_complet(reprise):
    charges = []
    def recevoir(request):
        charges.append(json.loads(request.content))
        return httpx.Response(200, text=(
            'data: {"type":"message_start","message":{"usage":'
            '{"input_tokens":11,"cache_creation_input_tokens":23,"cache_read_input_tokens":101}}}\n\n'
            'data: {"type":"message_stop"}\n\n'
        ))
    tools = [copy.deepcopy(WEB_SEARCH_TOOL)]
    original = copy.deepcopy(tools)
    async with httpx.AsyncClient(transport=httpx.MockTransport(recevoir)) as client:
        provider = AnthropicProvider(LLMConfig(LLMProvider.ANTHROPIC, 'claude-sonnet-5-5'), client)
        messages = [{'role': 'user', 'content': 'Bonjour'}]
        if reprise:
            flux = provider.continue_with_tool_results('Consignes intactes.', messages, '', [], [], tools)
        else:
            flux = provider.stream('Consignes intactes.', messages, tools)
        events = [event async for event in flux]
    assert charges[0]['system'] == [{
        'type': 'text', 'text': 'Consignes intactes.', 'cache_control': {'type': 'ephemeral'},
    }]
    assert charges[0]['tools'][-1]['cache_control'] == {'type': 'ephemeral'}
    assert charges[0]['tools'][-1]['input_schema'] == original[0]['function']['parameters']
    assert tools == original, 'Le catalogue partagé ne doit pas être muté'
    assert next(e for e in events if e.type == 'done').input_tokens == 135


def test_budget_des_descriptions_sans_changer_les_outils():
    # Ces quatre descriptions pesaient 2 534 caractères, hors paramètres.
    # Le budget force à retirer les répétitions et le numéro de ticket,
    # en conservant les règles de déclenchement et de prudence métier.
    tools = [WEB_SEARCH_TOOL, GENERATE_DOCUMENT_TOOL, SEARCH_INVOICES_TOOL, INVOICE_TOTALS_TOOL]
    assert sum(len(t['function']['description']) for t in tools) <= 1950
    texte = GENERATE_DOCUMENT_TOOL['function']['description']
    assert all(mot in texte for mot in ('EXPLICITEMENT', 'DANS CE MESSAGE', 'confirmation', 'content'))
    totaux = INVOICE_TOTALS_TOOL['function']['description']
    assert all(mot in totaux for mot in ('du_au_client_par_devise', 'encours_par_devise', 'NEGATIF', 'BRUT'))
    recherche = SEARCH_INVOICES_TOOL['function']['description']
    assert all(mot in recherche for mot in ('impossible', 'send_email', 'PDF', 'Envoyee'))


@pytest.fixture
def prompt_reel(monkeypatch):
    """Vrais constructeur, contexte et insertion des fiches ; données fictives."""
    monkeypatch.setattr(llm, 'load_therese_md', lambda: 'Consigne personnelle témoin : conserver les détails {utiles}.')

    def construire(instant, tour, avec_profil=True, provider=LLMProvider.ANTHROPIC):
        locale = datetime.fromisoformat(instant)

        class HorlogeDuPoste(datetime):
            @classmethod
            def now(cls, tz=None):
                return cls.fromtimestamp(locale.timestamp(), tz or locale.tzinfo)

            def astimezone(self, tz=None):
                return super().astimezone(tz or locale.tzinfo)

        monkeypatch.setattr(llm, 'datetime', HorlogeDuPoste)
        profil = UserProfile(name='Camille Fictive', context='Entreprise de plomberie fictive.') if avec_profil else None
        monkeypatch.setattr(user_profile, 'get_cached_profile', lambda: profil)
        service = llm.LLMService(LLMConfig(provider, CATALOGUE[provider.value].modeles[0]))
        context = service.prepare_context([Message('user', 'Bonjour')], memory_context=f'Dossier témoin du tour {tour}.')
        context.system_prompt = service._avec_consigne_de_langue(context.system_prompt)
        fiches = [{'id': 'fiche-temoin', 'kind': 'correction',
            'content': f'Correction fictive du tour {tour}.'}]
        borner_payload(context, fiches, service.config, None)
        monkeypatch.setattr(memory_card_context, 'lire_pour_chat', AsyncMock(return_value=fiches))
        context.memory_request = {'requete': 'Bonjour', 'scope': 'global', 'scope_id': None,
            'conversation_id': 'conversation-fictive', 'grants': [f'llm:{provider.value}'], 'purpose': 'llm'}
        return service, context

    return construire


@pytest.mark.asyncio
@pytest.mark.parametrize('avec_profil', [False, True])
async def test_le_prefixe_reste_identique_quand_la_minute_change(prompt_reel, avec_profil):
    async with httpx.AsyncClient(transport=httpx.MockTransport(lambda _: pytest.fail('Aucun appel attendu'))) as client:
        prefixes = []
        outils = [copy.deepcopy(WEB_SEARCH_TOOL), copy.deepcopy(INVOICE_TOTALS_TOOL)]
        originaux = copy.deepcopy(outils)
        for tour, instant in enumerate(('2026-10-21T23:59:00+02:00', '2026-10-22T00:00:00+02:00')):
            service, context = prompt_reel(instant, tour, avec_profil)
            provider = AnthropicProvider(service.config, client)
            body = provider._build_request_body(context.system_prompt, [], provider._convert_tools(outils))
            blocs = body['system']
            assert len(blocs) == 2
            assert ''.join(bloc['text'] for bloc in blocs) == context.system_prompt
            assert [i for i, bloc in enumerate(blocs) if 'cache_control' in bloc] == [0]
            assert blocs[0]['cache_control'] == {'type': 'ephemeral'}
            stable, variable = [bloc['text'] for bloc in blocs]
            for consigne in (service.LANGUE_BLOCK, service.SOVEREIGNTY_BLOCK,
                             service.LEGAL_GUARDRAIL_BLOCK, service.DATA_HONESTY_BLOCK,
                             '## Style de réponse', '## Instructions THERESE.md:',
                             'Consigne personnelle témoin : conserver les détails {utiles}.'):
                assert consigne in stable
            if avec_profil:
                assert 'Camille Fictive' in stable
                assert 'Entreprise de plomberie fictive.' in stable
                assert "Si l'utilisateur" in stable
                assert f'- Date : {21 + tour} octobre 2026' in variable
            for changeant in ('## Date et heure actuelles', '## Contexte mémoire:',
                             'Fiches mémoire utiles', f'Dossier témoin du tour {tour}',
                             f'Correction fictive du tour {tour}'):
                assert changeant in variable
                assert changeant not in stable
            assert [i for i, outil in enumerate(body['tools']) if 'cache_control' in outil] == [1]
            assert body['tools'][-1]['cache_control'] == {'type': 'ephemeral'}
            prefixes.append(blocs[0])
        assert prefixes[0] == prefixes[1]
        assert outils == originaux


@pytest.mark.asyncio
@pytest.mark.parametrize('provider', list(LLMProvider))
async def test_les_adaptateurs_transmettent_tout_le_prompt_reel(prompt_reel, monkeypatch, provider):
    service, context = prompt_reel('2026-10-21T10:00:00+02:00', 0, provider=provider)
    attendu = context.system_prompt
    charges = []

    def recevoir(request):
        charges.append(json.loads(request.content))
        if provider == LLMProvider.OLLAMA:
            return httpx.Response(200, text='{"done":true,"message":{"content":""}}\n')
        if provider == LLMProvider.ANTHROPIC:
            return httpx.Response(200, text='data: {"type":"message_stop"}\n\n')
        return httpx.Response(200, text='data: [DONE]\n\n')

    monkeypatch.setattr(service, '_resolve_with_circuit_breaker', lambda: service.config)
    async with httpx.AsyncClient(transport=httpx.MockTransport(recevoir)) as client:
        monkeypatch.setattr(service, '_get_client', AsyncMock(return_value=client))
        _ = [event async for event in service.stream_response_with_tools(context, enable_grounding=False)]
    assert len(charges) == 1
    body = charges[0]
    if provider == LLMProvider.ANTHROPIC:
        recu = ''.join(bloc['text'] for bloc in body['system'])
    elif provider == LLMProvider.GEMINI:
        recu = ''.join(part['text'] for part in body['systemInstruction']['parts'])
    else:
        recu = body.get('instructions') or next(m['content'] for m in body.get('messages', body.get('input', []))
                                              if m['role'] in ('system', 'developer'))
    assert recu == attendu
    if provider != LLMProvider.ANTHROPIC:
        assert 'cache_control' not in json.dumps(body)
