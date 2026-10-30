"""Régression du tour 6, adaptée de la reproduction contradictoire du tour 5."""

import pytest
from app.services.context import ContextWindow
from app.services.mcp_service import MCPServer, MCPServerStatus, MCPService, MCPTool
from app.services.providers.base import Message, ToolCall
from pydantic import BaseModel, ConfigDict, Field

from tests.test_chat_tool_confirmation import _FakeLLM, _parse_chunks


@pytest.mark.parametrize("public_prive", [False, True])
async def test_metadonnee_privee_connecteur_strict(client, monkeypatch, tmp_path, public_prive):
    from app.routers import chat

    class ArgumentsLecture(BaseModel):
        model_config = ConfigDict(extra="forbid")
        query: str

    class ArgumentsAvecNomsPrives(ArgumentsLecture):
        origine: str | None = Field(None, alias="_provenance_documents")
        trace: str | None = Field(None, alias="_trace")

    validateur = ArgumentsAvecNomsPrives if public_prive else ArgumentsLecture
    mcp = MCPService(config_path=tmp_path / "non-utilise")
    outil = MCPTool(
        name="lookup",
        description="Recherche locale",
        input_schema=validateur.model_json_schema(),
        server_id="demo",
    )
    mcp.servers["demo"] = MCPServer(
        id="demo",
        name="Connecteur de test",
        command="python3",
        status=MCPServerStatus.RUNNING,
        tools=[outil],
    )
    arguments = {"query": "horaire"} | (
        {"_trace": "publique", "_provenance_documents": "valeur publique"} if public_prive else {}
    )
    payloads = []

    async def serveur(_id, method, params, **kwargs):
        assert method == "tools/call"
        payloads.append(params["arguments"])
        validateur.model_validate(params["arguments"])
        return {"content": [{"type": "text", "text": "Résultat local"}]}

    monkeypatch.setattr(mcp, "_send_request", serveur)
    monkeypatch.setattr(chat, "get_mcp_service", lambda: mcp)
    # Témoin : le connecteur accepte les seuls arguments de son schéma.
    assert (await mcp.execute_tool_call("demo__lookup", arguments)).success
    context = ContextWindow(messages=[Message(role="user", content="Lis cet horaire")])
    appel = ToolCall(id="demo-appel", name="demo__lookup", arguments=arguments)
    chunks = _parse_chunks(
        [
            e
            async for e in chat._execute_tools_and_continue(
                _FakeLLM(), mcp, context, "", [appel], mcp.get_tools_for_llm(), None, 3
            )
        ]
    )
    carte = next(e["confirmation"] for e in chunks if e["type"] == "confirmation_required")
    confirmation = await client.post(
        "/api/chat/confirm-tool",
        json={"confirmation_id": carte["confirmation_id"], "approved": True},
    )
    assert confirmation.status_code == 200
    assert payloads[-1] == arguments
    assert confirmation.json()["result"] == "Résultat local"
