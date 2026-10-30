"""Septième tour : arguments MCP de la carte et du connecteur (réserve 7 de la relecture 6).

Relecture 6 de la branche confidentialité ; transport HTTPX en mémoire,
adaptateur OpenAI réel, aucun envoi réseau.
"""


import pytest

# ---------------------------------------------------------------------------
# Réserve 7 : le connecteur MCP reçoit les arguments que montre la carte.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("champ_corps", ["body", "content"])
async def test_mcp_alias_carte_et_connecteur_identiques(client, monkeypatch, tmp_path, champ_corps):
    from app.routers import chat
    from app.services.context import ContextWindow
    from app.services.mcp_service import MCPServer, MCPServerStatus, MCPService, MCPTool
    from app.services.providers.base import Message as LLMMessage
    from app.services.providers.base import ToolCall
    from pydantic import BaseModel, ConfigDict, create_model

    from tests.test_chat_tool_confirmation import _FakeLLM, _parse_chunks

    class Base(BaseModel):
        model_config = ConfigDict(extra="forbid")

    # Connecteur strict : déclare `body` ou `content`, refuse tout le reste.
    Mail = create_model("Mail", __base__=Base, to=(str, ...), **{champ_corps: (str, ...)})
    mcp = MCPService(config_path=tmp_path / "non-utilise")
    outil = MCPTool(name="send_email", description="Envoi", input_schema=Mail.model_json_schema(), server_id="demo")
    mcp.servers["demo"] = MCPServer(id="demo", name="Connecteur mail", command="python3",
                                    status=MCPServerStatus.RUNNING, tools=[outil])
    recus = []

    async def serveur(_id, method, params, **kwargs):
        recus.append(params["arguments"])
        Mail.model_validate(params["arguments"])
        return {"content": [{"type": "text", "text": "Envoyé"}]}

    monkeypatch.setattr(mcp, "_send_request", serveur)
    monkeypatch.setattr(chat, "get_mcp_service", lambda: mcp)
    context = ContextWindow(messages=[LLMMessage(role="user", content="Écris à Paul")], contient_documents=False)
    appel = ToolCall(id="mail", name="demo__send_email", arguments={"to": "paul@exemple.fr", "content": "Bonjour Paul"})
    chunks = _parse_chunks([e async for e in chat._execute_tools_and_continue(
        _FakeLLM(), mcp, context, "", [appel], mcp.get_tools_for_llm(), None, 3)])
    carte = next(e["confirmation"] for e in chunks if e["type"] == "confirmation_required")
    r = await client.post("/api/chat/confirm-tool", json={"confirmation_id": carte["confirmation_id"], "approved": True})
    assert r.json().get("status") == "executed", r.json()
    publics = {k: v for k, v in carte["arguments"].items() if not k.startswith("_")}
    assert recus == [publics]
    assert recus[0][champ_corps] == "Bonjour Paul"
