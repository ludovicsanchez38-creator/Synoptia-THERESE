"""Multi-tours d'outils dans chat.py (bug lcjp 11/06/2026).

La récursion de _execute_tools_and_continue doit transmettre l'historique
cumulé des tours (prior_turns) à chaque continuation, sinon le modèle ne
voit jamais les résultats précédents et re-demande le même outil.
"""
from unittest.mock import AsyncMock, patch

import pytest
from app.services.llm import ToolCall
from app.services.providers.base import StreamEvent


@pytest.mark.asyncio
async def test_recursion_accumule_les_tours_dans_prior_turns(client):
    from app.routers.chat import _execute_tools_and_continue

    captured_prior_turns: list = []

    class FakeLLMService:
        call_count = 0

        async def continue_with_tool_results(
            self, context, assistant_content, tool_calls, tool_results,
            tools, prior_turns=None,
        ):
            captured_prior_turns.append(list(prior_turns or []))
            FakeLLMService.call_count += 1
            if FakeLLMService.call_count == 1:
                # 1er tour de continuation : le modèle redemande un outil
                yield StreamEvent(
                    type="tool_call",
                    tool_call=ToolCall(id="call_2", name="web_search", arguments={"query": "b"}),
                )
                yield StreamEvent(type="done", stop_reason="tool_calls")
            else:
                yield StreamEvent(type="text", content="Réponse finale.")
                yield StreamEvent(type="done", stop_reason="end_turn")

    with patch("app.routers.chat.execute_web_search", AsyncMock(return_value="résultat")):
        chunks = []
        async for chunk in _execute_tools_and_continue(
            FakeLLMService(),
            None,  # mcp_service inutile pour web_search
            context=None,
            assistant_content="",
            tool_calls=[ToolCall(id="call_1", name="web_search", arguments={"query": "a"})],
            tools=[],
            conversation_id="conv-1",
            remaining_iterations=3,
        ):
            chunks.append(chunk)

    assert FakeLLMService.call_count == 2
    # 1re continuation : aucun tour précédent
    assert captured_prior_turns[0] == []
    # 2e continuation : le tour 1 (call_1 + son résultat) est dans l'historique
    assert len(captured_prior_turns[1]) == 1
    turn = captured_prior_turns[1][0]
    assert turn.tool_calls[0].id == "call_1"
    assert turn.tool_results[0].tool_call_id == "call_1"
    assert any("finale." in c for c in chunks)  # json.dumps échappe le é en \u00e9
