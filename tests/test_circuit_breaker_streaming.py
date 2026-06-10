"""US-008 (RES4) : le circuit breaker doit voir les erreurs HTTP (429/5xx) en
streaming. Les providers les convertissent en StreamEvent(type="error") sans
lever, donc record_failure n'était jamais appelé → bascule jamais déclenchée."""
from unittest.mock import AsyncMock, MagicMock

import pytest
from app.services.circuit_breaker import CircuitState, get_circuit_breaker
from app.services.llm import LLMConfig, LLMProvider, LLMService
from app.services.providers.base import StreamEvent


class _ErrorProvider:
    """Provider qui émet une erreur 429 en streaming, sans lever (comme les vrais)."""

    async def stream(self, system_prompt, messages, tools, **kwargs):
        yield StreamEvent(type="error", content="API error: 429")


def _service_with_error_provider():
    config = LLMConfig(LLMProvider.OPENAI, "gpt-test", api_key="x", context_window=8000)
    service = LLMService(config)
    service._ensure_provider = AsyncMock()
    service._resolve_with_circuit_breaker = lambda: service.config
    service._provider = _ErrorProvider()
    return service


@pytest.mark.asyncio
async def test_erreur_streaming_ouvre_le_circuit(monkeypatch):
    cb = get_circuit_breaker()
    circuit = cb._get_circuit("openai")
    circuit.consecutive_failures = 0
    circuit.total_failures = 0
    circuit.state = CircuitState.CLOSED

    try:
        context = MagicMock()
        context.to_openai_format.return_value = []
        context.system_prompt = ""

        service = _service_with_error_provider()

        # 1er échec : l'event d'erreur est transmis (UX préservée) ET compté.
        events = [
            e async for e in service.stream_response_with_tools(context, tools=None)
        ]
        assert any(e.type == "error" for e in events)
        assert cb._get_circuit("openai").consecutive_failures == 1

        # 2e échec : seuil atteint (FAILURE_THRESHOLD=2) → circuit OPEN.
        service2 = _service_with_error_provider()
        _ = [e async for e in service2.stream_response_with_tools(context, tools=None)]
        assert cb._get_circuit("openai").state == CircuitState.OPEN
    finally:
        # Ne pas polluer le singleton pour les autres tests.
        c = cb._get_circuit("openai")
        c.consecutive_failures = 0
        c.total_failures = 0
        c.state = CircuitState.CLOSED
