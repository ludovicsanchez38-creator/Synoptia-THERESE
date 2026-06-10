"""US-009 : honnêteté des outils par provider.

Avant : Grok, Ollama et Gemini acceptaient silencieusement les tools sans
jamais émettre de tool_call (stream) ni de continuation (stub) → « crée un
contact » répondait en texte sans rien créer, sans signal d'indisponibilité.

Ces tests vérifient la boucle d'outils réelle des 3 providers contre des flux
HTTP rejoués (formats officiels : OpenAI-compatible pour Grok, /api/chat tools
pour Ollama, functionDeclarations/functionCall/functionResponse pour Gemini).
"""
import json

import pytest
from app.services.providers.base import LLMConfig, LLMProvider, ToolCall, ToolResult
from app.services.providers.gemini import GeminiProvider
from app.services.providers.grok import GrokProvider
from app.services.providers.ollama import OllamaProvider

OPENAI_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "create_contact",
            "description": "Crée un contact",
            "parameters": {
                "type": "object",
                "properties": {"name": {"type": "string"}},
                "required": ["name"],
            },
        },
    }
]


class _FakeStreamResponse:
    def __init__(self, lines: list[str], status: int = 200):
        self.status_code = status
        self._lines = lines

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            import httpx

            request = httpx.Request("POST", "http://test")
            response = httpx.Response(self.status_code, request=request, json={"error": self._lines[0] if self._lines else ""})
            raise httpx.HTTPStatusError("error", request=request, response=response)

    async def aiter_lines(self):
        for line in self._lines:
            yield line

    async def aread(self) -> bytes:
        return b""


class _FakeClient:
    """Faux httpx.AsyncClient : capture la requête, rejoue des lignes."""

    def __init__(self, lines: list[str], status: int = 200):
        self._lines = lines
        self._status = status
        self.last_request: dict | None = None

    def stream(self, method, url, **kwargs):
        self.last_request = {"method": method, "url": url, **kwargs}
        resp = _FakeStreamResponse(self._lines, self._status)

        class _CM:
            async def __aenter__(_s):
                return resp

            async def __aexit__(_s, *a):
                return False

        return _CM()


async def _collect(gen):
    return [event async for event in gen]


# ---------------------------------------------------------------------------
# Grok (OpenAI-compatible, tool_calls livrés entiers dans un chunk)
# ---------------------------------------------------------------------------


def _grok(client) -> GrokProvider:
    return GrokProvider(
        LLMConfig(provider=LLMProvider.GROK, model="grok-4.3", api_key="x"),
        client=client,
    )


@pytest.mark.asyncio
async def test_grok_envoie_les_tools_dans_le_body():
    client = _FakeClient(["data: [DONE]"])
    await _collect(_grok(client).stream(None, [{"role": "user", "content": "hi"}], tools=OPENAI_TOOLS))
    body = client.last_request["json"]
    assert body["tools"] == OPENAI_TOOLS
    assert body["tool_choice"] == "auto"


@pytest.mark.asyncio
async def test_grok_parse_les_tool_calls_du_stream():
    # xAI livre le tool call ENTIER dans un seul chunk (doc officielle)
    chunk = {
        "choices": [
            {
                "delta": {
                    "tool_calls": [
                        {
                            "index": 0,
                            "id": "call_abc",
                            "function": {"name": "create_contact", "arguments": '{"name": "Marie"}'},
                        }
                    ]
                },
                "finish_reason": None,
            }
        ]
    }
    finish = {"choices": [{"delta": {}, "finish_reason": "tool_calls"}]}
    client = _FakeClient([f"data: {json.dumps(chunk)}", f"data: {json.dumps(finish)}", "data: [DONE]"])

    events = await _collect(_grok(client).stream(None, [{"role": "user", "content": "crée Marie"}], tools=OPENAI_TOOLS))

    tool_events = [e for e in events if e.type == "tool_call"]
    assert len(tool_events) == 1
    assert tool_events[0].tool_call.name == "create_contact"
    assert tool_events[0].tool_call.arguments == {"name": "Marie"}
    assert tool_events[0].tool_call.id == "call_abc"
    assert any(e.type == "done" and e.stop_reason == "tool_calls" for e in events)


@pytest.mark.asyncio
async def test_grok_continuation_construit_les_messages_outils():
    text_chunk = {"choices": [{"delta": {"content": "Contact créé."}, "finish_reason": None}]}
    client = _FakeClient([f"data: {json.dumps(text_chunk)}", "data: [DONE]"])

    events = await _collect(
        _grok(client).continue_with_tool_results(
            None,
            [{"role": "user", "content": "crée Marie"}],
            assistant_content="",
            tool_calls=[ToolCall(id="call_abc", name="create_contact", arguments={"name": "Marie"})],
            tool_results=[ToolResult(tool_call_id="call_abc", result={"ok": True})],
            tools=OPENAI_TOOLS,
        )
    )

    # La continuation NE doit PLUS être un stub : du texte revient
    assert any(e.type == "text" and e.content == "Contact créé." for e in events)
    sent = client.last_request["json"]["messages"]
    assistant_msg = next(m for m in sent if m["role"] == "assistant" and m.get("tool_calls"))
    assert assistant_msg["tool_calls"][0]["function"]["name"] == "create_contact"
    tool_msg = next(m for m in sent if m["role"] == "tool")
    assert tool_msg["tool_call_id"] == "call_abc"


# ---------------------------------------------------------------------------
# Ollama (/api/chat tools natif, arguments = objet JSON, pas de chaîne)
# ---------------------------------------------------------------------------


def _ollama(client) -> OllamaProvider:
    return OllamaProvider(
        LLMConfig(provider=LLMProvider.OLLAMA, model="qwen3:8b", base_url="http://localhost:11434"),
        client=client,
    )


@pytest.mark.asyncio
async def test_ollama_envoie_les_tools_dans_le_body():
    done = {"message": {"role": "assistant", "content": "ok"}, "done": True}
    client = _FakeClient([json.dumps(done)])
    await _collect(_ollama(client).stream(None, [{"role": "user", "content": "hi"}], tools=OPENAI_TOOLS))
    assert client.last_request["json"]["tools"] == OPENAI_TOOLS


@pytest.mark.asyncio
async def test_ollama_parse_les_tool_calls_du_stream():
    # Format officiel Ollama : arguments est un OBJET, tool_calls dans message
    tool_chunk = {
        "message": {
            "role": "assistant",
            "content": "",
            "tool_calls": [{"function": {"name": "create_contact", "arguments": {"name": "Marie"}}}],
        },
        "done": False,
    }
    done_chunk = {"message": {"role": "assistant", "content": ""}, "done": True}
    client = _FakeClient([json.dumps(tool_chunk), json.dumps(done_chunk)])

    events = await _collect(_ollama(client).stream(None, [{"role": "user", "content": "crée Marie"}], tools=OPENAI_TOOLS))

    tool_events = [e for e in events if e.type == "tool_call"]
    assert len(tool_events) == 1
    assert tool_events[0].tool_call.name == "create_contact"
    assert tool_events[0].tool_call.arguments == {"name": "Marie"}
    assert tool_events[0].tool_call.id  # id synthétisé non vide
    assert any(e.type == "done" and e.stop_reason == "tool_calls" for e in events)


@pytest.mark.asyncio
async def test_ollama_continuation_construit_les_messages_outils():
    done = {"message": {"role": "assistant", "content": "Contact créé."}, "done": True}
    client = _FakeClient([json.dumps(done)])

    events = await _collect(
        _ollama(client).continue_with_tool_results(
            None,
            [{"role": "user", "content": "crée Marie"}],
            assistant_content="",
            tool_calls=[ToolCall(id="ollama-call-0", name="create_contact", arguments={"name": "Marie"})],
            tool_results=[ToolResult(tool_call_id="ollama-call-0", result={"ok": True})],
            tools=OPENAI_TOOLS,
        )
    )

    assert any(e.type == "text" and e.content == "Contact créé." for e in events)
    sent = client.last_request["json"]["messages"]
    assistant_msg = next(m for m in sent if m["role"] == "assistant" and m.get("tool_calls"))
    assert assistant_msg["tool_calls"][0]["function"]["name"] == "create_contact"
    # Format officiel Ollama : role=tool + tool_name (pas de tool_call_id)
    tool_msg = next(m for m in sent if m["role"] == "tool")
    assert tool_msg["tool_name"] == "create_contact"


@pytest.mark.asyncio
async def test_ollama_modele_sans_tools_message_clair():
    """Honnêteté : modèle sans support tools → message explicite, pas un HTTP 400 brut."""
    import httpx

    class _RaisingClient(_FakeClient):
        def stream(self, method, url, **kwargs):
            self.last_request = {"method": method, "url": url, **kwargs}
            request = httpx.Request("POST", url)
            response = httpx.Response(
                400,
                request=request,
                json={"error": "registry.ollama.ai/library/gemma3:1b does not support tools"},
            )

            class _CM:
                async def __aenter__(_s):
                    raise httpx.HTTPStatusError("400", request=request, response=response)

                async def __aexit__(_s, *a):
                    return False

            return _CM()

    client = _RaisingClient([])
    events = await _collect(_ollama(client).stream(None, [{"role": "user", "content": "crée Marie"}], tools=OPENAI_TOOLS))

    errors = [e for e in events if e.type == "error"]
    assert errors, "Une erreur doit être émise"
    assert "outil" in errors[0].content.lower(), errors[0].content
    assert "qwen3:8b" in errors[0].content or "modèle" in errors[0].content.lower()


# ---------------------------------------------------------------------------
# Gemini (functionDeclarations / functionCall / functionResponse)
# ---------------------------------------------------------------------------


def _gemini(client, model: str = "gemini-2.5-flash") -> GeminiProvider:
    return GeminiProvider(
        LLMConfig(provider=LLMProvider.GEMINI, model=model, api_key="x"),
        client=client,
    )


@pytest.mark.asyncio
async def test_gemini_convertit_les_tools_en_function_declarations():
    client = _FakeClient(["data: " + json.dumps({"candidates": []})])
    await _collect(
        _gemini(client).stream(None, [{"role": "user", "parts": [{"text": "hi"}]}], tools=OPENAI_TOOLS)
    )
    body = client.last_request["json"]
    decls = None
    for tool_entry in body.get("tools", []):
        if "functionDeclarations" in tool_entry:
            decls = tool_entry["functionDeclarations"]
    assert decls, f"functionDeclarations absent du body: {body.get('tools')}"
    assert decls[0]["name"] == "create_contact"
    assert decls[0]["parameters"]["properties"]["name"]["type"] == "string"


@pytest.mark.asyncio
async def test_gemini_parse_les_function_calls_du_stream():
    chunk = {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {"functionCall": {"name": "create_contact", "args": {"name": "Marie"}}}
                    ]
                }
            }
        ]
    }
    client = _FakeClient(["data: " + json.dumps(chunk)])

    events = await _collect(
        _gemini(client).stream(None, [{"role": "user", "parts": [{"text": "crée Marie"}]}], tools=OPENAI_TOOLS)
    )

    tool_events = [e for e in events if e.type == "tool_call"]
    assert len(tool_events) == 1
    assert tool_events[0].tool_call.name == "create_contact"
    assert tool_events[0].tool_call.arguments == {"name": "Marie"}
    assert any(e.type == "done" and e.stop_reason == "tool_calls" for e in events)


@pytest.mark.asyncio
async def test_gemini_continuation_construit_function_response():
    text_chunk = {"candidates": [{"content": {"parts": [{"text": "Contact créé."}]}}]}
    client = _FakeClient(["data: " + json.dumps(text_chunk)])

    events = await _collect(
        _gemini(client).continue_with_tool_results(
            None,
            [{"role": "user", "parts": [{"text": "crée Marie"}]}],
            assistant_content="",
            tool_calls=[ToolCall(id="gemini-call-0", name="create_contact", arguments={"name": "Marie"})],
            tool_results=[ToolResult(tool_call_id="gemini-call-0", result={"ok": True})],
            tools=OPENAI_TOOLS,
        )
    )

    assert any(e.type == "text" and e.content == "Contact créé." for e in events)
    contents = client.last_request["json"]["contents"]
    model_turn = next(c for c in contents if c["role"] == "model")
    assert any("functionCall" in p for p in model_turn["parts"])
    user_response_turn = contents[-1]
    fr_parts = [p for p in user_response_turn["parts"] if "functionResponse" in p]
    assert fr_parts, "functionResponse absent du dernier tour"
    assert fr_parts[0]["functionResponse"]["name"] == "create_contact"
    assert fr_parts[0]["functionResponse"]["response"] == {"result": {"ok": True}}


@pytest.mark.asyncio
async def test_gemini_2x_avec_tools_desactive_le_grounding():
    """Sur gemini-2.x, combiner google_search et functionDeclarations n'est pas
    garanti par l'API : avec des tools, le grounding est écarté."""
    client = _FakeClient(["data: " + json.dumps({"candidates": []})])
    await _collect(
        _gemini(client, model="gemini-2.5-flash").stream(
            None, [{"role": "user", "parts": [{"text": "hi"}]}], tools=OPENAI_TOOLS
        )
    )
    body = client.last_request["json"]
    assert not any("google_search" in t for t in body.get("tools", []))


@pytest.mark.asyncio
async def test_gemini_sans_tools_garde_le_grounding():
    client = _FakeClient(["data: " + json.dumps({"candidates": []})])
    await _collect(
        _gemini(client, model="gemini-2.5-flash").stream(
            None, [{"role": "user", "parts": [{"text": "hi"}]}], tools=None
        )
    )
    body = client.last_request["json"]
    assert any("google_search" in t for t in body.get("tools", []))
