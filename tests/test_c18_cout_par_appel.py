"""Passe 3, cycle 18 : le palier se juge sur chaque appel, et le budget
voit le prompt préparé.

Un historique long ne doit pas être tarifé comme le seul dernier message.
Deux tours d'outils ne partagent pas un palier calculé sur la somme.
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

import pytest
from app.services.context import ContextWindow
from app.services.providers.base import LLMProvider, Message, StreamEvent
from app.services.token_tracker import TokenLimits, TokenTracker, get_token_tracker


def _traceur_isole() -> TokenTracker:
    traceur = object.__new__(TokenTracker)
    traceur._initialized = False
    traceur.__init__()
    return traceur


def _fenetre_longue() -> ContextWindow:
    """100 001 jetons de contenu : au-delà du palier court de Haiku 5.5."""
    return ContextWindow(
        messages=[Message(role="user", content="a" * (100_001 * 4))],
        system_prompt="",
        max_tokens=10_000_000,
    )


class _ServiceHaiku:
    """Prépare un prompt long et ne doit pas être appelé si le budget refuse."""

    def __init__(self) -> None:
        self.appele = False

        class _Config:
            model = "claude-haiku-5-5"
            provider = LLMProvider.ANTHROPIC

        self.config = _Config()

    def prepare_context(self, messages, memory_context=None):
        return _fenetre_longue()

    async def stream_response_with_tools(self, context, tools=None):
        self.appele = True
        yield StreamEvent(type="text", content="ne pas appeler")
        yield StreamEvent(type="done", stop_reason="end_turn", input_tokens=1, output_tokens=1)

    async def stream_response(self, context, raise_on_error=False, usage_sink=None):
        self.appele = True
        yield "ne pas appeler"


def _poser_budget(budget: float) -> tuple[TokenTracker, TokenLimits, float]:
    traceur = get_token_tracker()
    avant = traceur.get_limits()
    cout = traceur._month_cost
    traceur.set_limits(TokenLimits(
        max_input_tokens=10_000_000,
        max_output_tokens=10_000_000,
        daily_input_limit=100_000_000,
        daily_output_limit=100_000_000,
        monthly_budget_eur=budget,
        warn_at_percentage=100,
    ))
    traceur._month_cost = 0.0
    return traceur, avant, cout


class TestBudgetSurLePromptPrepare:
    @pytest.mark.asyncio
    async def test_le_flux_refuse_le_palier_long_du_prompt_prepare(self, client, monkeypatch):
        """Le dernier message est court. Le prompt préparé dépasse 100 000 jetons.

        Tarif court de ce prompt : environ 0,01 USD, sous le budget.
        Tarif long : environ 0,05 USD, au-dessus. Le contrôle doit refuser.
        """
        service = _ServiceHaiku()
        monkeypatch.setattr("app.routers.chat.get_llm_service", lambda: service)
        traceur, avant, cout = _poser_budget(0.02)
        try:
            reponse = await client.post(
                "/api/chat/send", json={"message": "Bonjour", "stream": True},
            )
        finally:
            traceur.set_limits(avant)
            traceur._month_cost = cout
        assert reponse.status_code == 200
        assert "Budget mensuel atteint" in reponse.text
        assert service.appele is False

    @pytest.mark.asyncio
    async def test_la_voie_directe_refuse_aussi(self, client, monkeypatch):
        service = _ServiceHaiku()
        monkeypatch.setattr("app.routers.chat.get_llm_service", lambda: service)
        traceur, avant, cout = _poser_budget(0.02)
        try:
            reponse = await client.post(
                "/api/chat/send", json={"message": "Bonjour", "stream": False},
            )
        finally:
            traceur.set_limits(avant)
            traceur._month_cost = cout
        assert reponse.status_code == 200
        assert "Budget mensuel atteint" in reponse.json()["content"]
        assert service.appele is False


class TestCoutParAppel:
    def test_deux_prompts_courts_ne_prennent_pas_le_palier_de_leur_somme(self):
        """Grok 4.7 : 150 000 reste court. 300 000 est le palier long.

        Deux appels de 150 000 ne sont pas une requête de 300 000.
        """
        traceur = _traceur_isole()
        appels = [(150_000, 1_000), (150_000, 1_000)]
        somme = traceur.cout_des_appels("grok-4.7", appels)
        court = traceur.estimate_cost("grok-4.7", 150_000, 1_000)
        assert somme == pytest.approx(court * 2)
        palier_sur_le_total = traceur.estimate_cost("grok-4.7", 300_000, 2_000)
        assert somme < palier_sur_le_total

    def test_gpt_61_sol_deux_appels_sous_272_000_restent_au_tarif_court(self):
        traceur = _traceur_isole()
        appels = [(200_000, 1_000), (200_000, 1_000)]
        somme = traceur.cout_des_appels("gpt-6.1-sol", appels)
        court = traceur.estimate_cost("gpt-6.1-sol", 200_000, 1_000)
        assert somme == pytest.approx(court * 2)
        assert somme < traceur.estimate_cost("gpt-6.1-sol", 400_000, 2_000)

    @pytest.mark.asyncio
    async def test_le_chat_enregistre_la_somme_des_couts_de_chaque_tour(
        self, client, monkeypatch,
    ):
        from app.services.llm import ToolCall
        from app.services.token_tracker import TokenTracker as Classe

        appels_vus: dict = {}
        reel = Classe.record_usage

        def espion(self, *args, **kwargs):
            appels_vus["kwargs"] = kwargs
            return reel(self, *args, **kwargs)

        monkeypatch.setattr(Classe, "record_usage", espion)

        class _Service:
            class config:
                model = "grok-4.7"
                provider = LLMProvider.GROK

            def prepare_context(self, messages, memory_context=None):
                return ContextWindow(
                    messages=[Message(role="user", content="Bonjour")],
                    system_prompt="",
                    max_tokens=10_000_000,
                )

            async def stream_response_with_tools(self, context, tools=None):
                yield StreamEvent(
                    type="tool_call",
                    tool_call=ToolCall(id="c1", name="search_emails", arguments={"query": "a"}),
                )
                yield StreamEvent(
                    type="done",
                    stop_reason="tool_calls",
                    input_tokens=150_000,
                    output_tokens=1_000,
                )

            async def continue_with_tool_results(self, *args, **kwargs):
                yield StreamEvent(type="text", content="Deux messages.")
                yield StreamEvent(
                    type="done",
                    stop_reason="end_turn",
                    input_tokens=150_000,
                    output_tokens=1_000,
                )

        monkeypatch.setattr("app.routers.chat.get_llm_service", lambda: _Service())
        with patch(
            "app.routers.chat.execute_workspace_tool",
            AsyncMock(return_value="rien"),
        ):
            reponse = await client.post(
                "/api/chat/send", json={"message": "Bonjour", "stream": True},
            )
        assert reponse.status_code == 200, reponse.text[:400]
        assert "Deux messages." in reponse.text
        kwargs = appels_vus["kwargs"]
        assert kwargs["appels"] == [(150_000, 1_000), (150_000, 1_000)]
        traceur = _traceur_isole()
        attendu = traceur.cout_des_appels("grok-4.7", kwargs["appels"])
        assert kwargs["model"] == "grok-4.7"
        cout = traceur.estimate_cost("grok-4.7", 300_000, 2_000)
        assert attendu < cout
        for ligne in reponse.text.splitlines():
            if not ligne.startswith("data: "):
                continue
            bloc = json.loads(ligne[6:])
            if bloc.get("type") == "done" and bloc.get("usage"):
                assert bloc["usage"]["cost_eur"] == pytest.approx(attendu)
                assert bloc["usage"]["cost_eur"] < cout
                break
        else:
            raise AssertionError(reponse.text[:500])
