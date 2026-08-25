"""0.48 lot A1 brique 3 - Mistral en raisonnement : chunks et rejeu brut.

Avec reasoning_effort, l'API Mistral rend `content` en LISTE de chunks
(thinking + text) au lieu d'une string, et `delta.content` change de
forme EN COURS de flux. Les parseurs supposaient une string (P2-5).

Contrats (design V3.5) :
- normaliseur local : liste -> concat des chunks text, thinking ignoré à
  l'AFFICHAGE ;
- le brut du tour (liste complète) voyage par StreamEvent jusqu'au rejeu :
  la doc Mistral exige le message assistant complet en multi-tours ;
- BUG-108 PRÉSERVÉ : un brut STRING ne se rejoue jamais (content: None
  sur les messages à tool_calls) - seule la liste (format reasoning
  documenté) se rejoue. Validation réelle Mistral en dette, comme BUG-108.
"""

import httpx
import pytest
from app.services.providers.base import (
    LLMProvider,
    StreamEvent,
    ToolCall,
    ToolResult,
    ToolTurn,
)
from app.services.providers.mistral import MistralProvider

CHUNKS = [
    {"type": "thinking", "thinking": [{"type": "text", "text": "je réfléchis"}]},
    {"type": "text", "text": "Voici "},
    {"type": "text", "text": "la réponse."},
]


def _provider() -> MistralProvider:
    from app.services.providers.base import LLMConfig

    return MistralProvider(
        LLMConfig(LLMProvider.MISTRAL, "mistral-medium-3-5", api_key="t"),
        httpx.AsyncClient(),
    )


class TestLeNormaliseur:
    def test_liste_de_chunks_concatene_le_texte(self):
        from app.services.providers.mistral import normaliser_content

        assert normaliser_content(CHUNKS) == "Voici la réponse."

    def test_string_inchangee(self):
        from app.services.providers.mistral import normaliser_content

        assert normaliser_content("déjà du texte") == "déjà du texte"

    def test_vide_et_none(self):
        from app.services.providers.mistral import normaliser_content

        assert normaliser_content(None) == ""
        assert normaliser_content([]) == ""


class TestLeFluxAFormeChangeante:
    @pytest.mark.asyncio
    async def test_delta_liste_puis_string(self, monkeypatch):
        """delta.content passe de liste (thinking) à string en cours de
        flux : les StreamEvent text portent TOUJOURS une string."""
        provider = _provider()

        lignes = [
            'data: {"choices": [{"delta": {"content": [{"type": "thinking", "thinking": [{"type": "text", "text": "hmm"}]}, {"type": "text", "text": "Début "}]}}]}',
            'data: {"choices": [{"delta": {"content": "suite."}, "finish_reason": "stop"}]}',
            "data: [DONE]",
        ]

        class FauxResponse:
            status_code = 200

            async def aiter_lines(self):
                for ligne in lignes:
                    yield ligne

            def raise_for_status(self):
                return None

            async def __aenter__(self):
                return self

            async def __aexit__(self, *a):
                return None

        monkeypatch.setattr(
            provider.client, "stream",
            lambda *a, **k: FauxResponse(),
        )

        textes = []
        async for event in provider.stream(None, [{"role": "user", "content": "x"}], None):
            if event.type == "text":
                assert isinstance(event.content, str), (
                    f"content non-string émis : {type(event.content)}"
                )
                textes.append(event.content)
        assert "".join(textes) == "Début suite."


class TestLeRejeuBrut:
    def _corps_du_rejeu(self, brut, prior=None):
        provider = _provider()
        messages: list[dict] = [{"role": "user", "content": "question"}]
        captures = {}

        async def faux_stream(system_prompt, msgs, tools):
            captures["messages"] = msgs
            if False:
                yield  # generatrice vide

        provider.stream = faux_stream

        import asyncio

        async def run():
            async for _ in provider.continue_with_tool_results(
                None, messages, "texte normalisé",
                [ToolCall(id="c1", name="outil", arguments={})],
                [ToolResult(tool_call_id="c1", result="ok")],
                prior_turns=prior,
                assistant_content_brut=brut,
            ):
                pass

        asyncio.get_event_loop()
        return captures, run

    @pytest.mark.asyncio
    async def test_le_tour_courant_rejoue_la_liste_brute(self):
        captures, run = self._corps_du_rejeu(CHUNKS)
        await run()
        assistant = next(
            m for m in captures["messages"]
            if m["role"] == "assistant" and m.get("tool_calls")
        )
        assert assistant["content"] == CHUNKS, (
            "la doc Mistral exige le message assistant COMPLET (thinking "
            "compris) en multi-tours reasoning"
        )

    @pytest.mark.asyncio
    async def test_sans_brut_bug_108_preserve(self):
        captures, run = self._corps_du_rejeu(None)
        await run()
        assistant = next(
            m for m in captures["messages"]
            if m["role"] == "assistant" and m.get("tool_calls")
        )
        assert assistant["content"] is None, (
            "BUG-108 : un content texte + tool_calls = 400 Mistral"
        )

    @pytest.mark.asyncio
    async def test_les_tours_passes_rejouent_leur_brut(self):
        prior = [ToolTurn(
            assistant_content="tour 1 normalisé",
            tool_calls=[ToolCall(id="p1", name="outil", arguments={})],
            tool_results=[ToolResult(tool_call_id="p1", result="r1")],
            assistant_content_brut=[{"type": "text", "text": "tour 1 brut"}],
        )]
        captures, run = self._corps_du_rejeu(None, prior=prior)
        await run()
        assistants = [
            m for m in captures["messages"]
            if m["role"] == "assistant" and m.get("tool_calls")
        ]
        assert assistants[0]["content"] == [{"type": "text", "text": "tour 1 brut"}]
        assert assistants[1]["content"] is None


class TestLeParametreSurTousLesProviders:
    """Le mot-clé assistant_content_brut est accepté par TOUTE la chaîne.

    chat.py le passera systématiquement à continue_with_tool_results ;
    un provider non-Mistral qui ne le déclare pas lèverait TypeError
    (design 0.48 : le paramètre s'ajoute aux neuf overrides concrets,
    à la base et à LLMService).
    """

    def test_les_neuf_overrides_declarent_le_parametre(self):
        import inspect

        from app.services.providers.anthropic import AnthropicProvider
        from app.services.providers.base import BaseProvider
        from app.services.providers.deepseek import DeepSeekProvider
        from app.services.providers.gemini import GeminiProvider
        from app.services.providers.infomaniak import InfomaniakProvider
        from app.services.providers.mistral import MistralProvider
        from app.services.providers.ollama import OllamaProvider
        from app.services.providers.openai import OpenAIProvider
        from app.services.providers.openrouter import OpenRouterProvider
        from app.services.providers.perplexity import PerplexityProvider

        classes = [
            BaseProvider, AnthropicProvider, OpenAIProvider,
            GeminiProvider, MistralProvider, OllamaProvider,
            DeepSeekProvider, OpenRouterProvider, PerplexityProvider,
            InfomaniakProvider,
        ]
        manquants = []
        for cls in classes:
            sig = inspect.signature(cls.continue_with_tool_results)
            if "assistant_content_brut" not in sig.parameters:
                manquants.append(cls.__name__)
        assert manquants == [], (
            f"continue_with_tool_results sans assistant_content_brut : {manquants}"
        )

    def test_llm_service_declare_et_transmet_le_parametre(self):
        import inspect

        from app.services.llm import LLMService

        sig = inspect.signature(LLMService.continue_with_tool_results)
        assert "assistant_content_brut" in sig.parameters


class TestLeTransportDansChat:
    """Le brut du tour voyage à travers la récursion de chat.py (0.48).

    Deux tours d'outils : le brut du tour 1 part en paramètre de la 1re
    continuation, rejoint prior_turns (sur son ToolTurn) à la 2e, et le
    brut du tour 2 - capté sur l'évènement tool_call de la continuation -
    devient le paramètre du tour suivant.
    """

    @pytest.mark.asyncio
    async def test_le_brut_traverse_la_recursion(self, client):
        from unittest.mock import AsyncMock, patch

        from app.routers.chat import _execute_tools_and_continue

        captured: list = []
        BRUT_TOUR_1 = [
            {"type": "thinking", "thinking": "je réfléchis"},
            {"type": "text", "text": "je cherche"},
        ]
        BRUT_TOUR_2 = [{"type": "thinking", "thinking": "encore"}]

        class FakeLLMService:
            call_count = 0

            async def continue_with_tool_results(
                self, context, assistant_content, tool_calls, tool_results,
                tools, prior_turns=None, assistant_content_brut=None,
            ):
                captured.append((assistant_content_brut, list(prior_turns or [])))
                FakeLLMService.call_count += 1
                if FakeLLMService.call_count == 1:
                    yield StreamEvent(
                        type="tool_call",
                        tool_call=ToolCall(
                            id="call_2", name="web_search",
                            arguments={"query": "b"},
                        ),
                        assistant_content_brut=BRUT_TOUR_2,
                    )
                    yield StreamEvent(type="done", stop_reason="tool_calls")
                else:
                    yield StreamEvent(type="text", content="Réponse finale.")
                    yield StreamEvent(type="done", stop_reason="end_turn")

        with patch(
            "app.routers.chat.execute_web_search",
            AsyncMock(return_value="résultat"),
        ):
            async for _ in _execute_tools_and_continue(
                FakeLLMService(),
                None,
                context=None,
                assistant_content="je cherche",
                tool_calls=[
                    ToolCall(id="call_1", name="web_search", arguments={"query": "a"})
                ],
                tools=[],
                conversation_id="conv-brut",
                remaining_iterations=3,
                assistant_content_brut=BRUT_TOUR_1,
            ):
                pass

        assert FakeLLMService.call_count == 2
        # 1re continuation : le brut du tour 1 en paramètre, pas d'historique
        assert captured[0][0] == BRUT_TOUR_1
        assert captured[0][1] == []
        # 2e continuation : le tour 1 rejoint prior_turns AVEC son brut,
        # le brut du tour 2 devient le paramètre courant
        assert len(captured[1][1]) == 1
        assert captured[1][1][0].assistant_content_brut == BRUT_TOUR_1
        assert captured[1][0] == BRUT_TOUR_2


class TestDeuxChatsConcurrents:
    """Design V3.5 : deux streams Mistral entrelacés ne mélangent jamais
    leurs bruts - brut_du_tour est LOCAL à chaque appel de stream()."""

    @pytest.mark.asyncio
    async def test_les_bruts_ne_se_melangent_pas(self, monkeypatch):
        provider_a = _provider()
        provider_b = _provider()

        def lignes_pour(texte, tool_id):
            return [
                'data: {"choices": [{"delta": {"content": [{"type": "thinking", "thinking": "'
                + texte + '"}]}}]}',
                'data: {"choices": [{"delta": {"tool_calls": [{"index": 0, "id": "'
                + tool_id + '", "function": {"name": "web_search", "arguments": "{}"}}]}}]}',
                'data: {"choices": [{"delta": {}, "finish_reason": "tool_calls"}]}',
                "data: [DONE]",
            ]

        def faux_stream(lignes):
            class FauxResponse:
                status_code = 200

                async def aiter_lines(self):
                    for ligne in lignes:
                        yield ligne

                def raise_for_status(self):
                    return None

                async def __aenter__(self):
                    return self

                async def __aexit__(self, *a):
                    return None

            return lambda *a, **k: FauxResponse()

        monkeypatch.setattr(
            provider_a.client, "stream", faux_stream(lignes_pour("pensee-A", "ca"))
        )
        monkeypatch.setattr(
            provider_b.client, "stream", faux_stream(lignes_pour("pensee-B", "cb"))
        )

        import asyncio

        async def collecte(provider):
            bruts = []
            async for event in provider.stream(None, [{"role": "user", "content": "x"}], None):
                if event.type == "tool_call":
                    bruts.append(event.assistant_content_brut)
            return bruts

        bruts_a, bruts_b = await asyncio.gather(
            collecte(provider_a), collecte(provider_b)
        )
        assert bruts_a == [[{"type": "thinking", "thinking": "pensee-A"}]]
        assert bruts_b == [[{"type": "thinking", "thinking": "pensee-B"}]]
