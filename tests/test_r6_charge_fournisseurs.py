"""Charge réellement sérialisée par les 14 adaptateurs, transport HTTP simulé."""
import hashlib
import json
import math
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest
from app.services import llm
from app.services.modeles_catalogue import CATALOGUE
from app.services.providers.base import LLMProvider


@pytest.mark.asyncio
@pytest.mark.parametrize('provider', [p.value for p in LLMProvider])
async def test_charge_sans_historique(client, monkeypatch, provider):
    from app.routers import chat
    from app.services import user_profile

    captures = []

    def recevoir(request):
        if request.method == 'POST' and '/show' not in request.url.path:
            captures.append(json.loads(request.content))
        if '/show' in request.url.path:
            return httpx.Response(200, json={'model_info': {'test.context_length': 32768}})
        if provider == 'ollama':
            return httpx.Response(200, text='{"done":true,"message":{"content":""}}\n')
        if provider == 'anthropic':
            return httpx.Response(200, text='data: {"type":"message_stop"}\n\n')
        return httpx.Response(200, text='data: [DONE]\n\n')

    monkeypatch.setattr(user_profile, 'get_cached_profile', lambda: None)
    monkeypatch.setattr(llm, 'load_therese_md', lambda: None)
    monkeypatch.setattr(llm, '_cle_depuis_environnement', lambda _: None)
    monkeypatch.setattr(llm.LLMService, '_resolve_with_circuit_breaker', lambda self: self.config)
    monkeypatch.setattr(chat, '_extract_entities_background', AsyncMock())
    mcp = MagicMock()
    mcp.get_tools_for_llm.return_value = []
    monkeypatch.setattr(chat, 'get_mcp_service', lambda: mcp)
    monkeypatch.setattr(llm, '_llm_service', None)
    async with httpx.AsyncClient(transport=httpx.MockTransport(recevoir)) as transport:
        monkeypatch.setattr(llm.LLMService, '_get_client', AsyncMock(return_value=transport))
        selection = await client.post('/api/config/llm', json={
            'provider': provider, 'model': CATALOGUE[provider].modeles[0],
        })
        assert selection.status_code == 200
        reponse = await client.post('/api/chat/send', json={
            'message': 'Bonjour', 'stream': True, 'include_memory': False,
        })
    assert reponse.status_code == 200
    assert len(captures) == 1, captures
    body = captures[0]
    system = body.get('system') or body.get('systemInstruction') or body.get('instructions')
    if system is None:
        system = [m for m in body.get('messages', body.get('input', [])) if m.get('role') in ('system', 'developer')]
    tools = body.get('tools', [])
    def mesure(value):
        texte = json.dumps(value, ensure_ascii=False, separators=(',', ':'))
        return {'octets': len(texte.encode()), 'caracteres': len(texte), 'jetons_estimes': math.ceil(len(texte) / 4)}
    resultat = {'fournisseur': provider, 'modele': CATALOGUE[provider].modeles[0],
        'systeme': mesure(system), 'outils': mesure(tools), 'requete': mesure(body)}
    schemas = []
    for tool in tools:
        for fonction in tool.get('functionDeclarations', [tool.get('function', tool)]):
            schema = fonction.get('parameters', fonction.get('input_schema', {}))
            schemas.append((fonction.get('name'), hashlib.sha256(json.dumps(
                schema, sort_keys=True, ensure_ascii=False).encode()).hexdigest()))
    resultat['signatures_outils'] = schemas
    # Seuls des comptes sont écrits : ni profil, ni consignes, ni contenu de clé.
    destination = Path(__file__).resolve().parents[1] / '.recette-r6/logs/charge'
    destination.mkdir(parents=True, exist_ok=True)
    (destination / f'{provider}.json').write_text(json.dumps(resultat, ensure_ascii=False, indent=2))
