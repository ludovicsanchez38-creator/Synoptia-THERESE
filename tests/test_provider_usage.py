"""Usage réel des providers (tokens), pas l'estimation ~2 tokens/mot.

Dette relevée dans le rapport de tests Syn du 14/06/2026 : chat.py et board.py
estiment `len(text.split()) * 2` au lieu de lire l'usage réel remonté par
chaque provider (usage.input_tokens côté Anthropic, usageMetadata côté
Gemini, etc.). Suffisant pour un garde-fou de budget, mais imprécis.

Ces tests vérifient que chaque provider émet bien input_tokens/output_tokens
réels sur le StreamEvent(type="done"), contre des flux HTTP rejoués (formats
officiels de chaque API).
"""
import json

import pytest
from app.services.providers.base import LLMConfig, LLMProvider, ToolCall, ToolResult


class _FakeStreamResponse:
    def __init__(self, lines: list[str], status: int = 200):
        self.status_code = status
        self._lines = lines

    def raise_for_status(self) -> None:
        pass

    async def aiter_lines(self):
        for line in self._lines:
            yield line


class _FakeClient:
    def __init__(self, lines: list[str]):
        self._response = _FakeStreamResponse(lines)
        self.requests: list[dict] = []

    @property
    def last_request(self) -> dict | None:
        return self.requests[-1] if self.requests else None

    def stream(self, method, url, **kwargs):
        self.requests.append({"method": method, "url": url, **kwargs})
        resp = self._response

        class _CM:
            async def __aenter__(_s):
                return resp

            async def __aexit__(_s, *a):
                return False

        return _CM()


async def _collect(gen):
    return [event async for event in gen]


def _done_event(events):
    done = [e for e in events if e.type == "done"]
    assert len(done) == 1, f"attendu exactement 1 event done, trouvé {len(done)}"
    return done[0]


# ---------------------------------------------------------------------------
# Anthropic (message_start.message.usage.input_tokens + message_delta.usage.output_tokens)
# ---------------------------------------------------------------------------


def _anthropic(client):
    from app.services.providers.anthropic import AnthropicProvider

    return AnthropicProvider(
        LLMConfig(provider=LLMProvider.ANTHROPIC, model="claude-sonnet-5", api_key="x"),
        client=client,
    )


@pytest.mark.asyncio
async def test_anthropic_remonte_usage_reel():
    message_start = {
        "type": "message_start",
        "message": {"usage": {"input_tokens": 42}},
    }
    content_delta = {
        "type": "content_block_delta",
        "delta": {"type": "text_delta", "text": "Bonjour"},
    }
    message_delta = {
        "type": "message_delta",
        "delta": {"stop_reason": "end_turn"},
        "usage": {"output_tokens": 7},
    }
    message_stop = {"type": "message_stop"}

    client = _FakeClient([
        f"data: {json.dumps(message_start)}",
        f"data: {json.dumps(content_delta)}",
        f"data: {json.dumps(message_delta)}",
        f"data: {json.dumps(message_stop)}",
        "data: [DONE]",
    ])

    events = await _collect(_anthropic(client).stream(None, [{"role": "user", "content": "salut"}]))

    done = _done_event(events)
    assert done.input_tokens == 42
    assert done.output_tokens == 7


@pytest.mark.asyncio
async def test_anthropic_usage_absent_reste_none():
    """Un stream sans message_start/message_delta usage (ex: mock incomplet,
    ou format API futur qui change) ne doit pas planter - juste None, pour
    que l'appelant retombe sur l'estimation."""
    message_stop = {"type": "message_stop"}
    client = _FakeClient([f"data: {json.dumps(message_stop)}", "data: [DONE]"])

    events = await _collect(_anthropic(client).stream(None, [{"role": "user", "content": "salut"}]))

    done = _done_event(events)
    assert done.input_tokens is None
    assert done.output_tokens is None


# ---------------------------------------------------------------------------
# OpenAI (chunk usage final, requiert stream_options.include_usage=true dans le body)
# ---------------------------------------------------------------------------


def _openai(client):
    from app.services.providers.openai import OpenAIProvider

    return OpenAIProvider(
        LLMConfig(provider=LLMProvider.OPENAI, model="gpt-5.2", api_key="x"),
        client=client,
    )


@pytest.mark.asyncio
async def test_openai_demande_include_usage_dans_le_body():
    client = _FakeClient(["data: [DONE]"])
    await _collect(_openai(client).stream(None, [{"role": "user", "content": "hi"}]))
    body = client.last_request["json"]
    assert body["stream_options"] == {"include_usage": True}


@pytest.mark.asyncio
async def test_openai_remonte_usage_reel():
    text_chunk = {"choices": [{"delta": {"content": "Bonjour"}, "finish_reason": None}]}
    finish_chunk = {"choices": [{"delta": {}, "finish_reason": "stop"}]}
    # Chunk final officiel OpenAI (stream_options.include_usage) : choices vide,
    # usage au niveau racine, envoyé APRÈS le chunk finish_reason.
    usage_chunk = {"choices": [], "usage": {"prompt_tokens": 42, "completion_tokens": 7}}
    client = _FakeClient([
        f"data: {json.dumps(text_chunk)}",
        f"data: {json.dumps(finish_chunk)}",
        f"data: {json.dumps(usage_chunk)}",
        "data: [DONE]",
    ])

    events = await _collect(_openai(client).stream(None, [{"role": "user", "content": "salut"}]))

    done = _done_event(events)
    assert done.stop_reason == "stop"
    assert done.input_tokens == 42
    assert done.output_tokens == 7


@pytest.mark.asyncio
async def test_openai_usage_absent_reste_none_sans_planter():
    """Un provider OpenAI-compatible qui ignore stream_options.include_usage
    (reverse-proxy tiers) ne doit pas casser le flux - juste None."""
    finish_chunk = {"choices": [{"delta": {"content": "ok"}, "finish_reason": "stop"}]}
    client = _FakeClient([f"data: {json.dumps(finish_chunk)}", "data: [DONE]"])

    events = await _collect(_openai(client).stream(None, [{"role": "user", "content": "salut"}]))

    done = _done_event(events)
    assert done.stop_reason == "stop"
    assert done.input_tokens is None
    assert done.output_tokens is None


@pytest.mark.asyncio
async def test_openai_filet_si_flux_coupe_sans_done_apres_finish_reason():
    """Régression introduite par le passage à un "done" différé (chunk usage) :
    si la connexion se coupe juste après le chunk finish_reason (avant le
    chunk usage ET avant [DONE], ex: coupure réseau), un "done" doit quand
    même être émis - sinon le chat reste bloqué en attente indéfiniment
    (chat.py attend l'event "done" pour savoir si des tool_calls suivent)."""
    finish_chunk = {"choices": [{"delta": {"content": "ok"}, "finish_reason": "stop"}]}
    # Pas de [DONE] du tout : simule une coupure de flux.
    client = _FakeClient([f"data: {json.dumps(finish_chunk)}"])

    events = await _collect(_openai(client).stream(None, [{"role": "user", "content": "salut"}]))

    done = _done_event(events)
    assert done.stop_reason == "stop"


# ---------------------------------------------------------------------------
# Les 4 autres providers OpenAI-compatible (implémentations dupliquées, pas
# d'héritage d'OpenAIProvider sauf Grok) : même contrat de chunk usage final.
# ---------------------------------------------------------------------------


def _provider_classes():
    from app.services.providers.deepseek import DeepSeekProvider
    from app.services.providers.infomaniak import InfomaniakProvider
    from app.services.providers.openrouter import OpenRouterProvider
    from app.services.providers.perplexity import PerplexityProvider

    return {
        "deepseek": (DeepSeekProvider, LLMProvider.DEEPSEEK, "deepseek-chat"),
        "infomaniak": (InfomaniakProvider, LLMProvider.INFOMANIAK, "llama3"),
        "openrouter": (OpenRouterProvider, LLMProvider.OPENROUTER, "openrouter/auto"),
        "perplexity": (PerplexityProvider, LLMProvider.PERPLEXITY, "sonar"),
    }


@pytest.mark.asyncio
@pytest.mark.parametrize("provider_name", ["deepseek", "infomaniak", "openrouter", "perplexity"])
async def test_openai_compatible_remonte_usage_reel(provider_name):
    provider_cls, llm_provider, model = _provider_classes()[provider_name]

    text_chunk = {"choices": [{"delta": {"content": "Bonjour"}, "finish_reason": None}]}
    finish_chunk = {"choices": [{"delta": {}, "finish_reason": "stop"}]}
    usage_chunk = {"choices": [], "usage": {"prompt_tokens": 42, "completion_tokens": 7}}
    client = _FakeClient([
        f"data: {json.dumps(text_chunk)}",
        f"data: {json.dumps(finish_chunk)}",
        f"data: {json.dumps(usage_chunk)}",
        "data: [DONE]",
    ])
    provider = provider_cls(LLMConfig(provider=llm_provider, model=model, api_key="x"), client=client)

    events = await _collect(provider.stream(None, [{"role": "user", "content": "salut"}]))

    done = _done_event(events)
    assert done.stop_reason == "stop"
    assert done.input_tokens == 42
    assert done.output_tokens == 7
    assert client.last_request["json"]["stream_options"] == {"include_usage": True}


@pytest.mark.asyncio
@pytest.mark.parametrize("provider_name", ["deepseek", "infomaniak", "openrouter", "perplexity"])
async def test_openai_compatible_usage_absent_reste_none_sans_planter(provider_name):
    provider_cls, llm_provider, model = _provider_classes()[provider_name]

    finish_chunk = {"choices": [{"delta": {"content": "ok"}, "finish_reason": "stop"}]}
    client = _FakeClient([f"data: {json.dumps(finish_chunk)}", "data: [DONE]"])
    provider = provider_cls(LLMConfig(provider=llm_provider, model=model, api_key="x"), client=client)

    events = await _collect(provider.stream(None, [{"role": "user", "content": "salut"}]))

    done = _done_event(events)
    assert done.stop_reason == "stop"
    assert done.input_tokens is None
    assert done.output_tokens is None


@pytest.mark.asyncio
@pytest.mark.parametrize("provider_name", ["deepseek", "infomaniak", "openrouter", "perplexity"])
async def test_openai_compatible_filet_si_flux_coupe_sans_done_apres_finish_reason(provider_name):
    """Même régression que pour openai.py (cf test_openai_filet_...) : le
    "done" différé jusqu'au chunk usage/[DONE] doit quand même être émis via
    un filet post-boucle si la connexion coupe juste après finish_reason."""
    provider_cls, llm_provider, model = _provider_classes()[provider_name]

    finish_chunk = {"choices": [{"delta": {"content": "ok"}, "finish_reason": "stop"}]}
    client = _FakeClient([f"data: {json.dumps(finish_chunk)}"])
    provider = provider_cls(LLMConfig(provider=llm_provider, model=model, api_key="x"), client=client)

    events = await _collect(provider.stream(None, [{"role": "user", "content": "salut"}]))

    done = _done_event(events)
    assert done.stop_reason == "stop"


@pytest.mark.asyncio
async def test_openrouter_filet_flux_coupe_sans_aucun_contenu_donne_une_erreur():
    """Cas particulier OpenRouter : une coupure AVANT tout contenu doit donner
    la même erreur "réponse vide" que le chemin [DONE] normal, pas un "done"
    creux - cohérence avec le comportement déjà testé au [DONE]."""
    from app.services.providers.openrouter import OpenRouterProvider

    client = _FakeClient([])  # coupure immédiate, aucune ligne du tout
    provider = OpenRouterProvider(
        LLMConfig(provider=LLMProvider.OPENROUTER, model="openrouter/auto", api_key="x"), client=client
    )

    events = await _collect(provider.stream(None, [{"role": "user", "content": "salut"}]))

    assert len(events) == 1
    assert events[0].type == "error"


# ---------------------------------------------------------------------------
# Gemini (usageMetadata cumulatif sur chaque chunk)
# ---------------------------------------------------------------------------


def _gemini(client):
    from app.services.providers.gemini import GeminiProvider

    return GeminiProvider(
        LLMConfig(provider=LLMProvider.GEMINI, model="gemini-2.5-flash", api_key="x"),
        client=client,
    )


@pytest.mark.asyncio
async def test_gemini_remonte_usage_reel():
    chunk1 = {
        "candidates": [{"content": {"parts": [{"text": "Bonjour"}]}}],
        "usageMetadata": {"promptTokenCount": 42, "candidatesTokenCount": 3},
    }
    chunk2 = {
        "candidates": [{"content": {"parts": [{"text": " !"}]}}],
        "usageMetadata": {"promptTokenCount": 42, "candidatesTokenCount": 7},
    }
    client = _FakeClient([f"data: {json.dumps(chunk1)}", f"data: {json.dumps(chunk2)}"])

    events = await _collect(_gemini(client).stream(None, [{"role": "user", "parts": [{"text": "salut"}]}]))

    done = _done_event(events)
    # Dernière valeur cumulative vue (chunk2), pas la première.
    assert done.input_tokens == 42
    assert done.output_tokens == 7


@pytest.mark.asyncio
async def test_gemini_usage_absent_reste_none():
    chunk = {"candidates": [{"content": {"parts": [{"text": "Bonjour"}]}}]}
    client = _FakeClient([f"data: {json.dumps(chunk)}"])

    events = await _collect(_gemini(client).stream(None, [{"role": "user", "parts": [{"text": "salut"}]}]))

    done = _done_event(events)
    assert done.input_tokens is None
    assert done.output_tokens is None


# ---------------------------------------------------------------------------
# Ollama (/api/chat, prompt_eval_count/eval_count sur le message done=true,
# lignes JSON brutes SANS préfixe SSE "data: ")
# ---------------------------------------------------------------------------


def _ollama(client):
    from app.services.providers.ollama import OllamaProvider

    return OllamaProvider(
        LLMConfig(provider=LLMProvider.OLLAMA, model="qwen3:8b"),
        client=client,
    )


@pytest.mark.asyncio
async def test_ollama_remonte_usage_reel():
    partial = {"message": {"role": "assistant", "content": "Bonjour"}, "done": False}
    done_chunk = {
        "message": {"role": "assistant", "content": ""},
        "done": True,
        "prompt_eval_count": 42,
        "eval_count": 7,
    }
    client = _FakeClient([json.dumps(partial), json.dumps(done_chunk)])

    events = await _collect(_ollama(client).stream(None, [{"role": "user", "content": "salut"}]))

    done = _done_event(events)
    assert done.input_tokens == 42
    assert done.output_tokens == 7


@pytest.mark.asyncio
async def test_ollama_usage_absent_reste_none_sans_planter():
    """Une version d'Ollama qui n'envoie pas prompt_eval_count/eval_count
    (ancienne version, ou modèle particulier) ne doit pas planter."""
    done_chunk = {"message": {"role": "assistant", "content": "Bonjour"}, "done": True}
    client = _FakeClient([json.dumps(done_chunk)])

    events = await _collect(_ollama(client).stream(None, [{"role": "user", "content": "salut"}]))

    done = _done_event(events)
    assert done.input_tokens is None
    assert done.output_tokens is None


# ---------------------------------------------------------------------------
# Mistral (déjà doté d'un filet done_emitted - garder ce garde en ajoutant
# l'usage réel, ne pas le perdre en différant le "done" jusqu'au chunk usage)
# ---------------------------------------------------------------------------


def _mistral(client):
    from app.services.providers.mistral import MistralProvider

    return MistralProvider(
        LLMConfig(provider=LLMProvider.MISTRAL, model="mistral-large-latest", api_key="x"),
        client=client,
    )


@pytest.mark.asyncio
async def test_mistral_demande_include_usage_dans_le_body():
    client = _FakeClient(["data: [DONE]"])
    await _collect(_mistral(client).stream(None, [{"role": "user", "content": "hi"}]))
    body = client.last_request["json"]
    assert body["stream_options"] == {"include_usage": True}


@pytest.mark.asyncio
async def test_mistral_remonte_usage_reel():
    text_chunk = {"choices": [{"delta": {"content": "Bonjour"}, "finish_reason": None}]}
    finish_chunk = {"choices": [{"delta": {}, "finish_reason": "stop"}]}
    usage_chunk = {"choices": [], "usage": {"prompt_tokens": 42, "completion_tokens": 7}}
    client = _FakeClient([
        f"data: {json.dumps(text_chunk)}",
        f"data: {json.dumps(finish_chunk)}",
        f"data: {json.dumps(usage_chunk)}",
        "data: [DONE]",
    ])

    events = await _collect(_mistral(client).stream(None, [{"role": "user", "content": "salut"}]))

    done = _done_event(events)
    assert done.stop_reason == "end_turn"
    assert done.input_tokens == 42
    assert done.output_tokens == 7


@pytest.mark.asyncio
async def test_mistral_usage_absent_reste_none_sans_planter():
    finish_chunk = {"choices": [{"delta": {"content": "ok"}, "finish_reason": "stop"}]}
    client = _FakeClient([f"data: {json.dumps(finish_chunk)}", "data: [DONE]"])

    events = await _collect(_mistral(client).stream(None, [{"role": "user", "content": "salut"}]))

    done = _done_event(events)
    assert done.input_tokens is None
    assert done.output_tokens is None


@pytest.mark.asyncio
async def test_mistral_filet_si_flux_coupe_sans_done_apres_finish_reason():
    """Garde de robustesse (déjà présent avant l'usage réel, à préserver) : si
    la connexion se coupe juste après le chunk finish_reason (avant le chunk
    usage ET avant [DONE]), un seul "done" doit quand même être émis - via le
    filet post-boucle, avec le stop_reason mémorisé."""
    finish_chunk = {"choices": [{"delta": {"content": "ok"}, "finish_reason": "stop"}]}
    # Pas de [DONE] du tout : simule une coupure de flux.
    client = _FakeClient([f"data: {json.dumps(finish_chunk)}"])

    events = await _collect(_mistral(client).stream(None, [{"role": "user", "content": "salut"}]))

    done = _done_event(events)
    assert done.stop_reason == "end_turn"


# ---------------------------------------------------------------------------
# continue_with_tool_results doit AUSSI remonter l'usage réel, pas seulement
# stream() en 1er tour - tous les providers délèguent à self.stream(), donc
# l'usage devrait déjà suivre, mais on le prouve explicitement (pas d'affirmer
# sans vérifier - cf grep manuel : les 9 providers font bien
# `async for event in self.stream(...): yield event` dans leur continuation).
# ---------------------------------------------------------------------------

_TOOL_CALLS = [ToolCall(id="call_1", name="create_contact", arguments={"name": "Marie"})]
_TOOL_RESULTS = [ToolResult(tool_call_id="call_1", result={"ok": True})]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "provider_name",
    ["openai", "deepseek", "infomaniak", "openrouter", "perplexity", "grok", "mistral"],
)
async def test_openai_compatible_continuation_remonte_usage_reel(provider_name):
    """Couvre aussi Grok (hérite d'OpenAIProvider en entier, aucune méthode à
    lui - le test prouve que l'héritage inclut bien le comportement usage)."""
    if provider_name == "grok":
        from app.services.providers.grok import GrokProvider
        provider_cls, llm_provider, model = GrokProvider, LLMProvider.GROK, "grok-4.3"
    elif provider_name == "mistral":
        from app.services.providers.mistral import MistralProvider
        provider_cls, llm_provider, model = MistralProvider, LLMProvider.MISTRAL, "mistral-large-latest"
    elif provider_name == "openai":
        from app.services.providers.openai import OpenAIProvider
        provider_cls, llm_provider, model = OpenAIProvider, LLMProvider.OPENAI, "gpt-5.2"
    else:
        provider_cls, llm_provider, model = _provider_classes()[provider_name]

    text_chunk = {"choices": [{"delta": {"content": "Contact créé."}, "finish_reason": None}]}
    finish_chunk = {"choices": [{"delta": {}, "finish_reason": "stop"}]}
    usage_chunk = {"choices": [], "usage": {"prompt_tokens": 42, "completion_tokens": 7}}
    client = _FakeClient([
        f"data: {json.dumps(text_chunk)}",
        f"data: {json.dumps(finish_chunk)}",
        f"data: {json.dumps(usage_chunk)}",
        "data: [DONE]",
    ])
    provider = provider_cls(LLMConfig(provider=llm_provider, model=model, api_key="x"), client=client)

    events = await _collect(provider.continue_with_tool_results(
        None,
        [{"role": "user", "content": "crée Marie"}],
        assistant_content="",
        tool_calls=_TOOL_CALLS,
        tool_results=_TOOL_RESULTS,
    ))

    done = _done_event(events)
    assert done.input_tokens == 42
    assert done.output_tokens == 7


@pytest.mark.asyncio
async def test_anthropic_continuation_remonte_usage_reel():
    message_start = {"type": "message_start", "message": {"usage": {"input_tokens": 42}}}
    message_delta = {"type": "message_delta", "delta": {"stop_reason": "end_turn"}, "usage": {"output_tokens": 7}}
    message_stop = {"type": "message_stop"}
    client = _FakeClient([
        f"data: {json.dumps(message_start)}",
        f"data: {json.dumps(message_delta)}",
        f"data: {json.dumps(message_stop)}",
        "data: [DONE]",
    ])

    events = await _collect(_anthropic(client).continue_with_tool_results(
        None,
        [{"role": "user", "content": "crée Marie"}],
        assistant_content="",
        tool_calls=_TOOL_CALLS,
        tool_results=_TOOL_RESULTS,
    ))

    done = _done_event(events)
    assert done.input_tokens == 42
    assert done.output_tokens == 7


@pytest.mark.asyncio
async def test_gemini_continuation_remonte_usage_reel():
    chunk = {
        "candidates": [{"content": {"parts": [{"text": "Contact créé."}]}}],
        "usageMetadata": {"promptTokenCount": 42, "candidatesTokenCount": 7},
    }
    client = _FakeClient([f"data: {json.dumps(chunk)}"])

    events = await _collect(_gemini(client).continue_with_tool_results(
        None,
        [{"role": "user", "parts": [{"text": "crée Marie"}]}],
        assistant_content="",
        tool_calls=_TOOL_CALLS,
        tool_results=_TOOL_RESULTS,
    ))

    done = _done_event(events)
    assert done.input_tokens == 42
    assert done.output_tokens == 7


@pytest.mark.asyncio
async def test_ollama_continuation_remonte_usage_reel():
    done_chunk = {
        "message": {"role": "assistant", "content": "Contact créé."},
        "done": True,
        "prompt_eval_count": 42,
        "eval_count": 7,
    }
    client = _FakeClient([json.dumps(done_chunk)])

    events = await _collect(_ollama(client).continue_with_tool_results(
        None,
        [{"role": "user", "content": "crée Marie"}],
        assistant_content="",
        tool_calls=_TOOL_CALLS,
        tool_results=_TOOL_RESULTS,
    ))

    done = _done_event(events)
    assert done.input_tokens == 42
    assert done.output_tokens == 7
