"""Préfixes réutilisables et charge réduite, sans connexion à Anthropic."""
import copy
import json

import httpx
import pytest
from app.services.providers.anthropic import AnthropicProvider
from app.services.providers.base import LLMConfig, LLMProvider
from app.services.web_search import WEB_SEARCH_TOOL
from app.services.workspace_tools import GENERATE_DOCUMENT_TOOL, INVOICE_TOTALS_TOOL, SEARCH_INVOICES_TOOL


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


@pytest.mark.asyncio
async def test_le_prefixe_reste_identique_quand_la_minute_change():
    async with httpx.AsyncClient(transport=httpx.MockTransport(lambda _: pytest.fail('Aucun appel attendu'))) as client:
        provider = AnthropicProvider(LLMConfig(LLMProvider.ANTHROPIC, 'claude-sonnet-5-5'), client)
        prefixes = []
        for heure in ('10:00', '10:01'):
            texte = (
                'Tu es Thérèse.\n\n## Utilisateur\nProfil professionnel fictif et consignes personnelles.\n\n'
                '## Date et heure actuelles\n21 octobre 2026, ' + heure
                + '\n\n## Garde-fous\nNe divulgue aucun secret. Ne fabrique aucune donnée.'
            )
            blocs = provider._build_request_body(texte, [], None)['system']
            assert len(blocs) == 2
            assert ''.join(bloc['text'] for bloc in blocs) == texte
            assert all(bloc['cache_control'] == {'type': 'ephemeral'} for bloc in blocs)
            prefixes.append(blocs[0])
            assert heure in blocs[1]['text']
        assert prefixes[0] == prefixes[1]
