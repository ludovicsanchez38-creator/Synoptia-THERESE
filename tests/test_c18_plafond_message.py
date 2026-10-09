"""Le plafond de taille vise le dernier message, pas l'historique.

Une conversation déjà longue, avec un message court, ne doit pas être
refusée : 8 000 jetons bornent le message. Le coût et le budget, eux,
continuent de voir le prompt préparé.
"""

from __future__ import annotations

import pytest
from app.services.context import ContextWindow
from app.services.providers.base import LLMProvider, Message, StreamEvent
from app.services.token_tracker import TokenLimits, get_token_tracker


def _fenetre(dernier: str, historique: str) -> ContextWindow:
    return ContextWindow(
        messages=[
            Message(role="user", content=historique),
            Message(role="assistant", content=historique),
            Message(role="user", content=dernier),
        ],
        system_prompt="s" * (5_000 * 4),
        max_tokens=10_000_000,
    )


class _Service:
    def __init__(self, dernier: str, historique: str) -> None:
        self.appele = False
        self._dernier = dernier
        self._historique = historique

        class _Config:
            model = "claude-haiku-5-5"
            provider = LLMProvider.ANTHROPIC

        self.config = _Config()

    def prepare_context(self, messages, memory_context=None):
        return _fenetre(self._dernier, self._historique)

    async def stream_response_with_tools(self, context, tools=None):
        self.appele = True
        yield StreamEvent(type="text", content="Reponse courte.")
        yield StreamEvent(
            type="done", stop_reason="end_turn", input_tokens=4, output_tokens=2,
        )

    async def stream_response(self, context, raise_on_error=False, usage_sink=None):
        self.appele = True
        if usage_sink is not None:
            usage_sink["input_tokens"] = 4
            usage_sink["output_tokens"] = 2
        yield "Reponse courte."


def _poser_plafond_message() -> tuple[object, TokenLimits, tuple[int, int, float]]:
    traceur = get_token_tracker()
    avant = traceur.get_limits()
    compteurs = (traceur._today_input, traceur._today_output, traceur._month_cost)
    traceur.set_limits(TokenLimits(
        max_input_tokens=8000,
        max_output_tokens=10_000_000,
        daily_input_limit=100_000_000,
        daily_output_limit=100_000_000,
        monthly_budget_eur=50.0,
        warn_at_percentage=100,
    ))
    traceur._today_input = 0
    traceur._today_output = 0
    traceur._month_cost = 0.0
    return traceur, avant, compteurs


def _restaurer(traceur, avant: TokenLimits, compteurs: tuple[int, int, float]) -> None:
    traceur.set_limits(avant)
    traceur._today_input, traceur._today_output, traceur._month_cost = compteurs


class TestPlafondDuDernierMessage:
    @pytest.mark.asyncio
    @pytest.mark.parametrize("flux", [True, False])
    async def test_un_historique_long_et_un_message_court_passent(
        self, client, monkeypatch, flux: bool,
    ):
        """Vingt mille jetons d'historique, plus le prompt système.

        Le nouveau message tient en un mot. L'ancien contrôle le refusait
        parce qu'il mesurait toute la fenêtre contre 8 000.
        """
        historique = "h" * (20_000 * 4)
        service = _Service("Bonjour", historique)
        monkeypatch.setattr("app.routers.chat.get_llm_service", lambda: service)
        traceur, avant, compteurs = _poser_plafond_message()
        try:
            reponse = await client.post(
                "/api/chat/send",
                json={"message": "Bonjour", "stream": flux, "disable_tools": True},
            )
        finally:
            _restaurer(traceur, avant, compteurs)
        assert reponse.status_code == 200, reponse.text[:400]
        assert "Message trop long" not in reponse.text
        assert "Reponse courte." in reponse.text
        assert service.appele is True

    @pytest.mark.asyncio
    @pytest.mark.parametrize("flux", [True, False])
    async def test_un_dernier_message_au_dela_de_8000_est_refuse(
        self, client, monkeypatch, flux: bool,
    ):
        service = _Service("m" * (8_001 * 4), "")
        monkeypatch.setattr("app.routers.chat.get_llm_service", lambda: service)
        traceur, avant, compteurs = _poser_plafond_message()
        try:
            reponse = await client.post(
                "/api/chat/send",
                json={"message": "long", "stream": flux, "disable_tools": True},
            )
        finally:
            _restaurer(traceur, avant, compteurs)
        assert reponse.status_code == 200, reponse.text[:400]
        assert "Message trop long" in reponse.text
        assert service.appele is False
