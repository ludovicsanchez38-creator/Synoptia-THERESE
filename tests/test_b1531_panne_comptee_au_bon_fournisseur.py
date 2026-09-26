"""B-1531 : sur le chemin sans flux, la panne du fournisseur de secours
était comptée au fournisseur principal.

`stream_response(raise_on_error=True)` compte la panne avant de lever,
mais sur `self.config` : après une bascule du disjoncteur, c'est le
circuit du principal (déjà en panne) qu'on chargeait, et celui du secours
qui venait d'échouer restait fermé.
"""

import pytest
from app.services.circuit_breaker import CircuitState, get_circuit_breaker


class _SecoursEnPanne:
    async def stream(self, system_prompt, messages, tools=None, **kwargs):
        from app.services.providers.base import StreamEvent

        yield StreamEvent(type="error", content="API error: 503")


def _remettre(nom: str) -> None:
    circuit = get_circuit_breaker()._get_circuit(nom)
    circuit.consecutive_failures = 0
    circuit.total_failures = 0
    circuit.state = CircuitState.CLOSED


@pytest.mark.asyncio
async def test_la_panne_du_secours_est_comptee_au_secours(monkeypatch):
    from app.services.context import ContextWindow
    from app.services.error_handler import ErreurPourEcran
    from app.services.llm import LLMConfig, LLMProvider, LLMService

    principal = LLMConfig(provider=LLMProvider.ANTHROPIC, model="claude-test", api_key="k")
    secours = LLMConfig(provider=LLMProvider.OPENAI, model="gpt-test", api_key="k")
    service = LLMService(principal)

    async def fournisseur_pour(config):
        return _SecoursEnPanne()

    monkeypatch.setattr(service, "_provider_pour", fournisseur_pour)
    monkeypatch.setattr(service, "_resolve_with_circuit_breaker", lambda: secours)
    for nom in ("anthropic", "openai"):
        _remettre(nom)
    try:
        with pytest.raises(ErreurPourEcran):
            async for _ in service.stream_response(ContextWindow(messages=[], system_prompt=""), raise_on_error=True):
                pass
        assert get_circuit_breaker()._get_circuit("openai").consecutive_failures >= 1
        assert get_circuit_breaker()._get_circuit("anthropic").consecutive_failures == 0
    finally:
        for nom in ("anthropic", "openai"):
            _remettre(nom)
