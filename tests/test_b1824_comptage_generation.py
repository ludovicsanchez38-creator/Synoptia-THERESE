"""B-1824 : une génération ne compte qu'une seule issue du flux."""

from unittest.mock import AsyncMock

import pytest
from app.services.circuit_breaker import CircuitState, get_circuit_breaker
from app.services.llm import LLMConfig, LLMProvider, LLMService
from app.services.providers.base import StreamEvent


@pytest.fixture
def service(monkeypatch):
    monkeypatch.setattr(
        "app.services.consentements.accord_valide", lambda *_: True
    )
    cb = get_circuit_breaker()
    cb.reset("openai")
    instance = LLMService(LLMConfig(LLMProvider.OPENAI, "test", api_key="test"))
    instance._ensure_provider = AsyncMock()
    yield instance
    cb.reset("openai")


@pytest.mark.asyncio
@pytest.mark.parametrize("code", [429, 503])
async def test_texte_partiel_puis_panne_ne_referme_pas_le_circuit(service, code):
    class Fournisseur:
        async def stream(self, *_args, **_kwargs):
            yield StreamEvent(type="text", content="Début")
            yield StreamEvent(type="error", content=f"API error: {code}")

    service._provider = Fournisseur()
    cb = get_circuit_breaker()
    for nombre in (1, 2):
        assert await service.generate_content("Question", system_prompt="Test") == "Début"
        circuit = cb._get_circuit("openai")
        assert circuit.consecutive_failures == nombre
        assert circuit.total_successes == 0
    assert circuit.state == CircuitState.OPEN


@pytest.mark.asyncio
async def test_une_generation_reussie_compte_un_seul_succes(service):
    class Fournisseur:
        async def stream(self, *_args, **_kwargs):
            yield StreamEvent(type="text", content="Réponse")
            yield StreamEvent(type="done")

    service._provider = Fournisseur()
    assert await service.generate_content("Question", system_prompt="Test") == "Réponse"
    circuit = get_circuit_breaker()._get_circuit("openai")
    assert circuit.total_successes == 1
    assert circuit.total_failures == 0
