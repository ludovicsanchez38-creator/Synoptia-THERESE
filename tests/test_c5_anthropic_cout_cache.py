"""Coût du cache du chat, sur des trames Anthropic rejouées sans réseau."""

import json
from unittest.mock import AsyncMock

import pytest
from app.services.llm import LLMService
from app.services.providers.anthropic import AnthropicProvider
from app.services.providers.base import LLMConfig, LLMProvider
from app.services.token_tracker import TokenTracker

from tests.test_anthropic_blocs_de_reflexion import _outil, _sse, _texte
from tests.test_provider_tools import _FakeClient, _FakeStreamResponse


def _reponse(bloc, usage, sortie, motif="end_turn"):
    return _FakeStreamResponse([
        _sse({"type": "message_start", "message": {"usage": usage}}),
        *(_sse(evenement) for evenement in bloc),
        _sse({"type": "message_delta", "delta": {"stop_reason": motif},
              "usage": {**usage, "output_tokens": sortie}}),
        _sse({"type": "message_stop"}),
    ])


def _service(monkeypatch, reponses):
    config = LLMConfig(LLMProvider.ANTHROPIC, "claude-sonnet-5-5", api_key="factice")
    transport = _FakeClient(responses=reponses)
    service = LLMService(config)
    service._provider = AnthropicProvider(config, client=transport)
    monkeypatch.setattr(service, "_ensure_provider", AsyncMock())
    monkeypatch.setattr(service, "_resolve_with_circuit_breaker", lambda: config)
    monkeypatch.setattr("app.routers.chat.get_llm_service", lambda: service)
    monkeypatch.setattr("app.routers.chat._extract_entities_background", AsyncMock())
    monkeypatch.setattr(
        "app.services.consentements.accord_valide",
        lambda purpose, provider, categories=(): purpose == "llm" and provider == "anthropic",
    )
    return transport


def _couts_enregistres(monkeypatch, module="app.routers.chat"):
    # Un traceur dédié écarte les compteurs et méthodes laissés sur
    # l'instance partagée par des tests précédents.
    traceur = object.__new__(TokenTracker)
    traceur._initialized = False
    traceur.__init__()
    monkeypatch.setattr(f"{module}.get_token_tracker", lambda: traceur)
    return traceur._usage_history


@pytest.mark.asyncio
@pytest.mark.parametrize("stream", [False, True])
async def test_ecriture_du_cache_facturee_avec_son_taux(client, monkeypatch, stream):
    # Trame de la question de contrôle réelle, contenu réduit au texte fictif.
    usage = {
        "input_tokens": 3007, "cache_creation_input_tokens": 8115,
        "cache_read_input_tokens": 0,
        "cache_creation": {"ephemeral_5m_input_tokens": 8115, "ephemeral_1h_input_tokens": 0},
    }
    transport = _service(monkeypatch, [_reponse(_texte(0, "Quatre."), usage, 7)])
    traces = _couts_enregistres(monkeypatch)
    reponse = await client.post("/api/chat/send", json={"message": "Deux et deux ?", "stream": stream})
    assert reponse.status_code == 200, reponse.text
    assert "Quatre." in reponse.text, reponse.text
    assert len(transport.requests) == 1
    assert len(traces) == 1
    assert (traces[0].input_tokens, traces[0].output_tokens) == (11122, 7)
    assert traces[0].cost_eur == pytest.approx(0.0263715)


@pytest.mark.asyncio
async def test_la_reprise_outil_conserve_le_prix_de_chaque_cache(client, monkeypatch):
    appel = _outil(0, "tool-c5", "search_invoices", {"query": "AZUR"})
    transport = _service(monkeypatch, [
        _reponse(appel, {"input_tokens": 130, "cache_creation_input_tokens": 8500,
                        "cache_read_input_tokens": 0,
                        "cache_creation": {"ephemeral_1h_input_tokens": 1000}},
                 50, "tool_use"),
        _reponse(_texte(0, "Un devis retrouvé."), {"input_tokens": 250,
                 "cache_creation_input_tokens": 0, "cache_read_input_tokens": 8500}, 100),
    ])
    traces = _couts_enregistres(monkeypatch)
    monkeypatch.setattr("app.routers.chat.execute_workspace_tool", AsyncMock(return_value='{"total": 1}'))
    reponse = await client.post("/api/chat/send", json={"message": "Cherche les factures AZUR.", "stream": True})
    assert reponse.status_code == 200, reponse.text
    chunks = [json.loads(ligne[6:]) for ligne in reponse.text.splitlines() if ligne.startswith("data: ")]
    assert any(c.get("content") == "Un devis retrouvé." for c in chunks), chunks
    assert len(transport.requests) == 2
    assert any(
        bloc.get("type") == "tool_result"
        for message in transport.requests[1]["json"]["messages"]
        if isinstance(message["content"], list)
        for bloc in message["content"]
    )
    assert len(traces) == 1
    assert (traces[0].input_tokens, traces[0].output_tokens) == (17_380, 150)
    attendu = (130 * 2 + 7500 * 2.5 + 1000 * 4 + 50 * 10
               + 250 * 2 + 8500 * .1 + 100 * 10) / 1e6
    assert traces[0].cost_eur == pytest.approx(attendu)
    terminal = next(c for c in chunks if c["type"] == "done" and c.get("usage"))
    assert terminal["usage"]["cost_eur"] == pytest.approx(attendu)
