"""Le budget est revu juste avant chaque appel qui suit un outil.

Le premier contrôle ne voit pas encore le résultat. Un résultat long
peut franchir un palier, et donc le budget, avant la continuation.
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

import pytest
from app.services.context import ContextWindow
from app.services.llm import ToolCall
from app.services.providers.base import LLMProvider, Message, StreamEvent
from app.services.token_tracker import TokenLimits, get_token_tracker


class _Service:
    def __init__(self) -> None:
        self.continuation = False

        class _Config:
            model = "claude-haiku-5-5"
            provider = LLMProvider.ANTHROPIC

        self.config = _Config()

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
            type="done", stop_reason="tool_calls", input_tokens=20, output_tokens=5,
        )

    async def continue_with_tool_results(self, *args, **kwargs):
        self.continuation = True
        yield StreamEvent(type="text", content="Suite envoyee.")
        yield StreamEvent(
            type="done", stop_reason="end_turn", input_tokens=20, output_tokens=5,
        )


def _poser(budget: float):
    traceur = get_token_tracker()
    avant = traceur.get_limits()
    compteurs = (traceur._today_input, traceur._today_output, traceur._month_cost)
    traceur.set_limits(TokenLimits(
        max_input_tokens=8000,
        max_output_tokens=10_000_000,
        daily_input_limit=100_000_000,
        daily_output_limit=100_000_000,
        monthly_budget_eur=budget,
        warn_at_percentage=100,
    ))
    traceur._today_input = 0
    traceur._today_output = 0
    traceur._month_cost = 0.0
    return traceur, avant, compteurs


def _restaurer(traceur, avant, compteurs) -> None:
    traceur.set_limits(avant)
    traceur._today_input, traceur._today_output, traceur._month_cost = compteurs


class TestBudgetAvantContinuation:
    @pytest.mark.asyncio
    async def test_un_resultat_long_refuse_la_continuation(self, client, monkeypatch):
        """Le message est court. Le résultat d'outil dépasse 100 000 jetons.

        Tarif court du premier appel : sous 0,02 USD. Tarif long de la
        suite : au-dessus. Le fournisseur ne doit pas être rappelé.
        """
        service = _Service()
        monkeypatch.setattr("app.routers.chat.get_llm_service", lambda: service)
        traceur, avant, compteurs = _poser(0.02)
        try:
            with patch(
                "app.routers.chat.execute_workspace_tool",
                AsyncMock(return_value="r" * (120_000 * 4)),
            ):
                reponse = await client.post(
                    "/api/chat/send", json={"message": "Bonjour", "stream": True},
                )
        finally:
            _restaurer(traceur, avant, compteurs)
        assert reponse.status_code == 200, reponse.text[:400]
        assert "Budget mensuel atteint" in reponse.text
        assert "Message trop long" not in reponse.text
        assert service.continuation is False
        assert "Suite envoyee." not in reponse.text
        evenements = [
            json.loads(ligne.removeprefix("data: "))
            for ligne in reponse.text.splitlines()
            if ligne.startswith("data: ")
        ]
        types = [e.get("type") for e in evenements]
        assert "error" in types, types
        assert "done" not in types, types
        assert types[-1] == "error", types
