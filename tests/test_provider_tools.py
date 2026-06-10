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
    """Reproduit le contrat httpx d'une réponse STREAMING : le body d'erreur
    n'est pas pré-chargé, il faut le lire via aread() (revue adversariale :
    un fake au body pré-lu validait du code mort en prod)."""

    def __init__(self, lines: list[str], status: int = 200, body: bytes = b""):
        self.status_code = status
        self._lines = lines
        self._body = body

    def raise_for_status(self) -> None:
        # Contrat streaming honnête : la réponse levée n'a PAS de body lu
        # (e.response.json() échoue, comme en prod sur client.stream()).
        if self.status_code >= 400:
            import httpx

            request = httpx.Request("POST", "http://test")
            response = httpx.Response(self.status_code, request=request)
            raise httpx.HTTPStatusError("error", request=request, response=response)

    async def aiter_lines(self):
        for line in self._lines:
            yield line

    async def aread(self) -> bytes:
        return self._body


class _FakeClient:
    """Faux httpx.AsyncClient : capture les requêtes, rejoue des réponses.

    Accepte une réponse unique (lines) ou une séquence de réponses
    (responses=[...]) pour tester les retries.
    """

    def __init__(
        self,
        lines: list[str] | None = None,
        status: int = 200,
        responses: list[_FakeStreamResponse] | None = None,
    ):
        self._responses = responses or [_FakeStreamResponse(lines or [], status)]
        self._call_index = 0
        self.requests: list[dict] = []

    @property
    def last_request(self) -> dict | None:
        return self.requests[-1] if self.requests else None

    def stream(self, method, url, **kwargs):
        import copy

        # deepcopy : le provider peut muter request_body APRÈS l'envoi
        # (retry sans tools) ; on capture ce qui a été réellement envoyé.
        captured = {k: copy.deepcopy(v) if k == "json" else v for k, v in kwargs.items()}
        self.requests.append({"method": method, "url": url, **captured})
        idx = min(self._call_index, len(self._responses) - 1)
        self._call_index += 1
        resp = self._responses[idx]

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


@pytest.fixture(autouse=True)
def _reset_ollama_capability_cache():
    """Le cache de capacité tools est process-local : l'isoler entre tests."""
    from app.services.providers import ollama as ollama_module

    ollama_module._MODELS_WITHOUT_TOOLS.clear()
    yield
    ollama_module._MODELS_WITHOUT_TOOLS.clear()


@pytest.mark.asyncio
async def test_ollama_modele_sans_tools_degradation_gracieuse():
    """Revue adversariale US-009 : modèle sans tools -> le chat TEXTE doit
    continuer de fonctionner (avant : 400 à chaque message, chat inutilisable
    sur gemma3 & co). Attendu : avis honnête UNE fois + retry sans tools."""
    error_400 = _FakeStreamResponse(
        [],
        status=400,
        body=json.dumps(
            {"error": "registry.ollama.ai/library/qwen3:8b does not support tools"}
        ).encode(),
    )
    text_ok = _FakeStreamResponse(
        [json.dumps({"message": {"role": "assistant", "content": "Bonjour !"}, "done": True})]
    )
    client = _FakeClient(responses=[error_400, text_ok])

    events = await _collect(
        _ollama(client).stream(None, [{"role": "user", "content": "salut"}], tools=OPENAI_TOOLS)
    )

    # Pas d'événement error : dégradation gracieuse
    assert not [e for e in events if e.type == "error"], events
    texts = [e.content for e in events if e.type == "text"]
    # Avis honnête (outils indisponibles) PUIS la vraie réponse
    assert any("outil" in t.lower() for t in texts), texts
    assert any("Bonjour !" in t for t in texts), texts
    # Deux requêtes : la première avec tools, le retry SANS
    assert len(client.requests) == 2
    assert "tools" in client.requests[0]["json"]
    assert "tools" not in client.requests[1]["json"]


@pytest.mark.asyncio
async def test_ollama_capacite_memorisee_pas_de_400_au_message_suivant():
    """Une fois l'incapacité connue, plus d'aller-retour 400 : les tools ne
    sont plus envoyés pour ce modèle (et plus d'avis répété)."""
    error_400 = _FakeStreamResponse(
        [], status=400,
        body=json.dumps({"error": "model does not support tools"}).encode(),
    )
    text_ok = _FakeStreamResponse(
        [json.dumps({"message": {"role": "assistant", "content": "ok"}, "done": True})]
    )
    client = _FakeClient(responses=[error_400, text_ok, text_ok])
    provider = _ollama(client)

    await _collect(provider.stream(None, [{"role": "user", "content": "a"}], tools=OPENAI_TOOLS))
    events2 = await _collect(
        provider.stream(None, [{"role": "user", "content": "b"}], tools=OPENAI_TOOLS)
    )

    # 3e requête (2e message) : directement sans tools, une seule tentative
    assert len(client.requests) == 3
    assert "tools" not in client.requests[2]["json"]
    texts2 = [e.content for e in events2 if e.type == "text"]
    assert not any("outil" in t.lower() for t in texts2), "l'avis ne doit pas se répéter"


@pytest.mark.asyncio
async def test_ollama_404_modele_absent_message_clair():
    """Le body d'erreur est lu via aread() (streaming) : le 404 doit produire
    le message d'installation, pas un HTTP brut."""
    error_404 = _FakeStreamResponse(
        [], status=404,
        body=json.dumps({"error": 'model "qwen3:8b" not found'}).encode(),
    )
    client = _FakeClient(responses=[error_404])
    events = await _collect(
        _ollama(client).stream(None, [{"role": "user", "content": "salut"}], tools=None)
    )
    errors = [e for e in events if e.type == "error"]
    assert errors and "ollama pull" in errors[0].content.lower(), errors


@pytest.mark.asyncio
async def test_ollama_texte_et_tool_call_dans_le_meme_stream():
    """Cas réel fréquent : contenu texte ET tool_calls dans le même message."""
    mixed = {
        "message": {
            "role": "assistant",
            "content": "Je crée Marie.",
            "tool_calls": [{"function": {"name": "create_contact", "arguments": {"name": "Marie"}}}],
        },
        "done": False,
    }
    done = {"message": {"role": "assistant", "content": ""}, "done": True}
    client = _FakeClient([json.dumps(mixed), json.dumps(done)])

    events = await _collect(
        _ollama(client).stream(None, [{"role": "user", "content": "crée Marie"}], tools=OPENAI_TOOLS)
    )

    assert any(e.type == "text" and e.content == "Je crée Marie." for e in events)
    assert any(e.type == "tool_call" for e in events)
    assert any(e.type == "done" and e.stop_reason == "tool_calls" for e in events)


@pytest.mark.asyncio
async def test_ollama_plusieurs_tool_calls_ids_distincts():
    chunk = {
        "message": {
            "role": "assistant",
            "content": "",
            "tool_calls": [
                {"function": {"name": "create_contact", "arguments": {"name": "Marie"}}},
                {"function": {"name": "create_contact", "arguments": {"name": "Paul"}}},
            ],
        },
        "done": False,
    }
    done = {"message": {"role": "assistant", "content": ""}, "done": True}
    client = _FakeClient([json.dumps(chunk), json.dumps(done)])

    events = await _collect(
        _ollama(client).stream(None, [{"role": "user", "content": "x"}], tools=OPENAI_TOOLS)
    )
    tool_events = [e for e in events if e.type == "tool_call"]
    assert len(tool_events) == 2
    assert tool_events[0].tool_call.id != tool_events[1].tool_call.id


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


@pytest.mark.asyncio
async def test_gemini_3_combine_grounding_et_functions():
    """Gemini 3 : seule combinaison documentée tools intégrés + function calling."""
    client = _FakeClient(["data: " + json.dumps({"candidates": []})])
    await _collect(
        _gemini(client, model="gemini-3.1-pro-preview").stream(
            None, [{"role": "user", "parts": [{"text": "hi"}]}], tools=OPENAI_TOOLS
        )
    )
    tools_sent = client.last_request["json"]["tools"]
    combined = tools_sent[0]
    assert "google_search" in combined and "functionDeclarations" in combined


@pytest.mark.asyncio
async def test_gemini_sanitise_les_schemas_mcp():
    """Revue adversariale : les inputSchema MCP ($schema, additionalProperties,
    anyOf, default...) provoquaient un 400 proto Schema sur TOUTE la requête."""
    mcp_tool = {
        "type": "function",
        "function": {
            "name": "mcp_search",
            "description": "Recherche",
            "parameters": {
                "$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "query": {"type": "string", "default": "", "description": "Requête"},
                    "filters": {
                        "type": "array",
                        "items": {"type": "object", "anyOf": [{"type": "string"}], "properties": {"k": {"type": "string"}}},
                    },
                },
                "required": ["query"],
            },
        },
    }
    client = _FakeClient(["data: " + json.dumps({"candidates": []})])
    await _collect(
        _gemini(client).stream(None, [{"role": "user", "parts": [{"text": "hi"}]}], tools=[mcp_tool])
    )
    decls = next(
        t["functionDeclarations"] for t in client.last_request["json"]["tools"] if "functionDeclarations" in t
    )
    params = decls[0]["parameters"]
    flat = json.dumps(params)
    assert "$schema" not in flat and "additionalProperties" not in flat and "anyOf" not in flat
    assert "default" not in flat
    # Les clés légitimes survivent, récursivement
    assert params["properties"]["query"]["type"] == "string"
    assert params["properties"]["filters"]["items"]["properties"]["k"]["type"] == "string"
    assert params["required"] == ["query"]


@pytest.mark.asyncio
async def test_gemini_function_responses_dans_l_ordre_des_calls():
    """Sans ids (Gemini < 3), la corrélation est positionnelle : les résultats
    doivent suivre l'ordre des functionCall même si l'exécution a réordonné."""
    text_chunk = {"candidates": [{"content": {"parts": [{"text": "ok"}]}}]}
    client = _FakeClient(["data: " + json.dumps(text_chunk)])
    calls = [
        ToolCall(id="gemini-call-0", name="create_contact", arguments={"name": "A"}),
        ToolCall(id="gemini-call-1", name="create_contact", arguments={"name": "B"}),
    ]
    # Résultats fournis dans l'ordre INVERSE (cas enforce_create_cap)
    results = [
        ToolResult(tool_call_id="gemini-call-1", result={"who": "B"}),
        ToolResult(tool_call_id="gemini-call-0", result={"who": "A"}),
    ]
    await _collect(
        _gemini(client).continue_with_tool_results(
            None, [{"role": "user", "parts": [{"text": "x"}]}],
            assistant_content="", tool_calls=calls, tool_results=results, tools=OPENAI_TOOLS,
        )
    )
    contents = client.last_request["json"]["contents"]
    frs = [p["functionResponse"]["response"]["result"]["who"] for p in contents[-1]["parts"]]
    assert frs == ["A", "B"]


@pytest.mark.asyncio
async def test_grok_plusieurs_tool_calls_accumules_par_index():
    """Accumulation par index (héritée d'openai.py) avec 2 appels entrelacés."""
    chunk1 = {
        "choices": [{"delta": {"tool_calls": [
            {"index": 0, "id": "call_a", "function": {"name": "create_contact", "arguments": '{"name":'}},
            {"index": 1, "id": "call_b", "function": {"name": "read_contact", "arguments": '{"id": 1}'}},
        ]}, "finish_reason": None}]
    }
    chunk2 = {
        "choices": [{"delta": {"tool_calls": [
            {"index": 0, "function": {"arguments": ' "Marie"}'}},
        ]}, "finish_reason": None}]
    }
    finish = {"choices": [{"delta": {}, "finish_reason": "tool_calls"}]}
    client = _FakeClient([
        f"data: {json.dumps(chunk1)}", f"data: {json.dumps(chunk2)}",
        f"data: {json.dumps(finish)}", "data: [DONE]",
    ])
    events = await _collect(_grok(client).stream(None, [{"role": "user", "content": "x"}], tools=OPENAI_TOOLS))
    tool_events = [e for e in events if e.type == "tool_call"]
    assert len(tool_events) == 2
    by_id = {e.tool_call.id: e.tool_call for e in tool_events}
    assert by_id["call_a"].arguments == {"name": "Marie"}
    assert by_id["call_b"].arguments == {"id": 1}


@pytest.mark.asyncio
async def test_grok_arguments_invalides_comportement_fige():
    """Comportement actuel FIGÉ (hérité d'openai.py, partagé par 6 providers) :
    des arguments JSON invalides retombent sur {} - l'outil est appelé sans
    arguments plutôt que de casser le stream. À reconsidérer si un cas réel
    montre que l'échec explicite serait préférable."""
    chunk = {
        "choices": [{"delta": {"tool_calls": [
            {"index": 0, "id": "call_x", "function": {"name": "create_contact", "arguments": '{"name": MALFORMED'}},
        ]}, "finish_reason": None}]
    }
    finish = {"choices": [{"delta": {}, "finish_reason": "tool_calls"}]}
    client = _FakeClient([f"data: {json.dumps(chunk)}", f"data: {json.dumps(finish)}", "data: [DONE]"])
    events = await _collect(_grok(client).stream(None, [{"role": "user", "content": "x"}], tools=OPENAI_TOOLS))
    tool_events = [e for e in events if e.type == "tool_call"]
    assert len(tool_events) == 1
    assert tool_events[0].tool_call.arguments == {}
