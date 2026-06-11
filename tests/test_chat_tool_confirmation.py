"""US-002 : la boucle d'outils n'exécute jamais send_email sans confirmation.

Test d'intégration de _execute_tools_and_continue : un appel send_email du LLM
doit être mis en attente (événement confirmation_required) et NE PAS déclencher
execute_workspace_tool.
"""
import json
from unittest.mock import MagicMock

import app.routers.chat as chat_mod
import pytest
from app.routers.chat import _execute_tools_and_continue
from app.services import tool_confirmations
from app.services.llm import ToolCall


class _Event:
    def __init__(self, type, content="", tool_call=None, stop_reason="end_turn"):
        self.type = type
        self.content = content
        self.tool_call = tool_call
        self.stop_reason = stop_reason


class _FakeLLM:
    async def continue_with_tool_results(
        self, context, assistant_content, tool_calls, tool_results, tools
    , prior_turns=None):
        self.received_tool_results = tool_results
        yield _Event("done", stop_reason="end_turn")


def _parse_chunks(raw_chunks):
    out = []
    for c in raw_chunks:
        body = c[len("data: ") :].strip() if c.startswith("data: ") else c.strip()
        try:
            out.append(json.loads(body))
        except json.JSONDecodeError:
            pass
    return out


@pytest.mark.asyncio
async def test_send_email_demande_confirmation_sans_envoyer(monkeypatch):
    executed = {"workspace": False}

    async def _spy_execute(*args, **kwargs):
        executed["workspace"] = True
        return "ENVOYÉ"

    monkeypatch.setattr(chat_mod, "execute_workspace_tool", _spy_execute)

    llm = _FakeLLM()
    tc = ToolCall(
        id="t1",
        name="send_email",
        arguments={"to": "x@y.fr", "subject": "Sujet", "body": "Corps"},
    )

    raw = [
        chunk
        async for chunk in _execute_tools_and_continue(
            llm, None, None, "", [tc], [], "conv1", 3, session=MagicMock()
        )
    ]
    chunks = _parse_chunks(raw)

    # 1. send_email n'a PAS été exécuté automatiquement.
    assert executed["workspace"] is False

    # 2. Un événement de demande de confirmation a été émis avec les détails.
    confirms = [c for c in chunks if c.get("type") == "confirmation_required"]
    assert len(confirms) == 1
    payload = confirms[0]["confirmation"]
    assert payload["tool_name"] == "send_email"
    assert payload["arguments"]["to"] == "x@y.fr"

    # 3. L'action est réellement en attente et consommable une fois.
    cid = payload["confirmation_id"]
    assert tool_confirmations.pop_pending(cid) == (
        "send_email",
        {"to": "x@y.fr", "subject": "Sujet", "body": "Corps"},
    )

    # 4. Le LLM a reçu un résultat marquant l'action comme non exécutée.
    assert any(not tr.is_error for tr in llm.received_tool_results)
