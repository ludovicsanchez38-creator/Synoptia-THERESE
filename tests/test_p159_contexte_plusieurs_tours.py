"""P-159 : le bilan reste celui des messages passés durant les tours d'outils.

Le vrai service LLM prépare et convertit la fenêtre. Seul son fournisseur
est factice : il demande deux lectures simulées avant de répondre. Le bilan
du flux final doit décrire la charge observée et survivre à la relecture DB.
"""

from collections.abc import AsyncGenerator
from copy import deepcopy
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from app.services.context import ContextWindow
from app.services.llm import LLMService
from app.services.providers.base import (
    LLMConfig,
    LLMProvider,
    StreamEvent,
    ToolCall,
    ToolResult,
    ToolTurn,
)
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.test_p159_contexte_transmis import _evenements, _fil


class _FournisseurPlusieursTours:
    def __init__(self) -> None:
        self.charges: list[list[dict[str, Any]]] = []
        self.tours_precedents: list[list[ToolTurn]] = []
        self.lectures_courantes: list[tuple[list[ToolCall], list[ToolResult]]] = []

    async def stream(
        self, system_prompt: str | None, messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None,
    ) -> AsyncGenerator[StreamEvent, None]:
        self.charges.append(deepcopy(messages))
        yield StreamEvent(
            type="tool_call",
            tool_call=ToolCall(id="lecture-a", name="search_emails", arguments={"query": "a"}),
        )
        yield StreamEvent(type="done", stop_reason="tool_calls", input_tokens=3, output_tokens=2)

    async def continue_with_tool_results(
        self, system_prompt: str | None, messages: list[dict[str, Any]],
        assistant_content: str, tool_calls: list[ToolCall], tool_results: list[ToolResult],
        tools: list[dict[str, Any]] | None = None, prior_turns: list[ToolTurn] | None = None,
        assistant_content_brut: Any = None,
    ) -> AsyncGenerator[StreamEvent, None]:
        self.charges.append(deepcopy(messages))
        self.tours_precedents.append(deepcopy(prior_turns or []))
        self.lectures_courantes.append((deepcopy(tool_calls), deepcopy(tool_results)))
        if len(self.tours_precedents) == 1:
            yield StreamEvent(
                type="tool_call",
                tool_call=ToolCall(id="lecture-b", name="search_emails", arguments={"query": "b"}),
            )
            yield StreamEvent(type="done", stop_reason="tool_calls", input_tokens=4, output_tokens=2)
        else:
            yield StreamEvent(type="text", content="Réponse finale après les deux lectures.")
            yield StreamEvent(type="done", stop_reason="end_turn", input_tokens=5, output_tokens=2)


class _LLMAvecCapture(LLMService):
    def __init__(self, budget: int, fournisseur: _FournisseurPlusieursTours) -> None:
        super().__init__(
            LLMConfig(
                provider=LLMProvider.OPENAI, model="faux-modele", max_tokens=20,
                context_window=budget + 20,
            ),
            bascule_circuit=False,
        )
        self._provider = fournisseur
        self.fenetres: list[ContextWindow] = []

    def _get_system_prompt_with_identity(self) -> str:
        return "systeme"

    async def stream_response_with_tools(
        self, context: ContextWindow, tools: list[dict[str, Any]] | None = None,
        **kwargs: Any,
    ) -> AsyncGenerator[StreamEvent, None]:
        self.fenetres.append(context)
        async for event in super().stream_response_with_tools(context, tools, **kwargs):
            yield event

    async def continue_with_tool_results(
        self, context: ContextWindow, *args: Any, **kwargs: Any,
    ) -> AsyncGenerator[StreamEvent, None]:
        self.fenetres.append(context)
        async for event in super().continue_with_tool_results(context, *args, **kwargs):
            yield event


@pytest.mark.asyncio
@pytest.mark.parametrize("budget,transmis", [(500, 3), (60, 2)])
async def test_le_bilan_de_la_fenetre_survit_aux_tours_et_au_rechargement(
    client: AsyncClient,
    db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
    budget: int,
    transmis: int,
) -> None:
    import json

    from app.routers import chat

    conv_id = await _fil(db_session, 3, taille=64)
    fournisseur = _FournisseurPlusieursTours()
    llm = _LLMAvecCapture(budget, fournisseur)
    mcp = MagicMock()
    mcp.get_tools_for_llm.return_value = []
    lectures = AsyncMock(side_effect=["Résultat du premier tour", "Résultat du second tour"])
    monkeypatch.setattr(chat, "get_llm_service", lambda: llm)
    monkeypatch.setattr(chat, "get_mcp_service", lambda: mcp)
    monkeypatch.setattr(chat, "web_tools", lambda: [])
    monkeypatch.setattr(chat, "execute_workspace_tool", lectures)
    monkeypatch.setattr(chat, "_extract_entities_background", AsyncMock())

    reponse = await client.post(
        "/api/chat/send",
        json={
            "message": "question-courante", "conversation_id": conv_id,
            "stream": True, "include_memory": False,
        },
    )
    assert reponse.status_code == 200, reponse.text
    evenements = _evenements(reponse.text)
    assert not [e for e in evenements if e.get("type") == "error"], evenements
    assert lectures.await_count == 2
    assert len(llm.fenetres) == len(fournisseur.charges) == 3
    assert all(f is llm.fenetres[0] for f in llm.fenetres)
    for fenetre, charge in zip(llm.fenetres, fournisseur.charges, strict=True):
        conversation = [m for m in charge if m["role"] != "system"]
        assert conversation == [{"role": m.role, "content": m.content} for m in fenetre.messages]
        assert len(conversation) - 1 == transmis
        assert conversation[-1]["content"] == "question-courante"
    assert fournisseur.tours_precedents[0] == []
    precedent = fournisseur.tours_precedents[1]
    assert len(precedent) == 1
    assert precedent[0].tool_calls[0].id == "lecture-a"
    assert precedent[0].tool_results[0].result == "Résultat du premier tour"
    for (appels, resultats), identifiant, resultat in zip(
        fournisseur.lectures_courantes,
        ("lecture-a", "lecture-b"),
        ("Résultat du premier tour", "Résultat du second tour"),
        strict=True,
    ):
        assert len(appels) == len(resultats) == 1
        assert appels[0].id == resultats[0].tool_call_id == identifiant
        assert resultats[0].result == resultat

    done = next(e for e in evenements if e.get("type") == "done")
    attendu = {"messages_relus": 3, "messages_transmis": transmis}
    assert done["contexte"] == attendu
    historique = await client.get(f"/api/chat/conversations/{conv_id}/messages")
    assert historique.status_code == 200, historique.text
    assistant = [m for m in historique.json() if m["role"] == "assistant"][-1]
    assert "Réponse finale après les deux lectures." in assistant["content"]
    assert json.loads(assistant["extra_data"])["contexte"] == attendu
