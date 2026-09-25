"""
THÉRÈSE v2 - Anthropic Provider

Claude API streaming implementation with tool support.
Sprint 2 - PERF-2.1: Extracted from monolithic llm.py
"""

import json
import logging
from typing import Any, AsyncGenerator

import httpx

from .base import (
    BaseProvider,
    StreamEvent,
    ToolCall,
    ToolResult,
    ToolTurn,
    message_erreur_http,
)

logger = logging.getLogger(__name__)

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"


# Familles de modèles qui REFUSENT les paramètres de sampling (temperature,
# top_p, top_k -> 400 API). Vérifié le 10/07/2026 : Fable 5, Sonnet 5 et
# Opus 4.7/4.8 les ont retirés ; Opus 4.6 / Sonnet 4.6 / Haiku les acceptent.
_NO_SAMPLING_PREFIXES = (
    "claude-fable-5",
    "claude-sonnet-5",
    "claude-opus-5",
    "claude-opus-4-7",
    "claude-opus-4-8",
)

# 0.48 : la table _EFFORT_PREFIXES a disparu - la politique d'effort vit
# au catalogue (services/modeles_catalogue.py), resolue a la construction
# de LLMConfig (effort_resolu).


class AnthropicProvider(BaseProvider):
    """Anthropic Claude API provider."""

    def _build_request_body(
        self,
        system_prompt: str | None,
        messages: list[dict[str, Any]],
        anthropic_tools: list[dict[str, Any]] | None,
    ) -> dict[str, Any]:
        """Payload /v1/messages - `temperature` seulement sur les modèles qui
        l'acceptent (les récents la refusent avec un 400, cf. _NO_SAMPLING)."""
        request_body: dict[str, Any] = {
            "model": self.config.model,
            "max_tokens": self.config.max_tokens,
            "system": system_prompt,
            "messages": messages,
            "stream": True,
        }
        if not self.config.model.startswith(_NO_SAMPLING_PREFIXES):
            request_body["temperature"] = self.config.temperature
        if self.config.effort_resolu:
            request_body["output_config"] = {"effort": self.config.effort_resolu}
        if anthropic_tools:
            request_body["tools"] = anthropic_tools
        return request_body

    def _convert_tools(self, tools: list[dict] | None) -> list[dict] | None:
        """Convert OpenAI-format tools to Anthropic format."""
        if not tools:
            return None
        anthropic_tools = []
        for tool in tools:
            if tool.get("type") == "function":
                func = tool["function"]
                anthropic_tools.append({
                    "name": func["name"],
                    "description": func.get("description", ""),
                    "input_schema": func.get("parameters", {"type": "object", "properties": {}}),
                })
        return anthropic_tools or None

    async def stream(
        self,
        system_prompt: str | None,
        messages: list[dict],
        tools: list[dict] | None = None,
    ) -> AsyncGenerator[StreamEvent, None]:
        """Stream from Anthropic Claude API with tool support."""
        anthropic_tools = self._convert_tools(tools)
        request_body = self._build_request_body(system_prompt, messages, anthropic_tools)

        try:
            async with self.client.stream(
                "POST",
                ANTHROPIC_API_URL,
                headers={
                    "x-api-key": self.config.api_key or "",
                    "anthropic-version": ANTHROPIC_VERSION,
                    "content-type": "application/json",
                },
                json=request_body,
            ) as response:
                response.raise_for_status()

                # Track current content block for tool calls
                current_tool_call_id = None
                current_tool_name = None
                current_tool_input = ""
                stop_reason = None
                # Usage réel (dette 14/06/2026) : input_tokens arrive dans
                # message_start, output_tokens (cumulatif) dans chaque message_delta.
                input_tokens: int | None = None
                output_tokens: int | None = None
                done_emitted = False
                # P-122 (Opus 5.5) : le contenu du tour tel que reçu, dans
                # l'ordre. Sur les modèles à réflexion toujours active, la
                # reprise après outils doit le renvoyer INCHANGÉ (blocs
                # `thinking` signés compris), sinon l'API répond 400. La même
                # liste est attachée à chaque tool_call : chat.py ne l'utilise
                # qu'au `done`, quand elle est complète.
                blocs_du_tour: list[dict[str, Any]] = []
                blocs_par_index: dict[int, dict[str, Any]] = {}
                tour_avec_reflexion = False

                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]
                        if data.strip() == "[DONE]":
                            break
                        try:
                            event = json.loads(data)
                            event_type = event.get("type")

                            if event_type == "message_start":
                                input_tokens = (
                                    event.get("message", {}).get("usage", {}).get("input_tokens")
                                )

                            elif event_type == "content_block_start":
                                content_block = event.get("content_block", {})
                                bloc = dict(content_block)
                                blocs_du_tour.append(bloc)
                                blocs_par_index[event.get("index", len(blocs_du_tour) - 1)] = bloc
                                if bloc.get("type") in ("thinking", "redacted_thinking"):
                                    tour_avec_reflexion = True
                                if content_block.get("type") == "tool_use":
                                    current_tool_call_id = content_block.get("id")
                                    current_tool_name = content_block.get("name")
                                    current_tool_input = ""

                            elif event_type == "content_block_delta":
                                delta = event.get("delta", {})
                                delta_type = delta.get("type")
                                bloc_courant = blocs_par_index.get(event.get("index", -1))

                                if delta_type == "text_delta":
                                    if text := delta.get("text"):
                                        if bloc_courant is not None:
                                            bloc_courant["text"] = bloc_courant.get("text", "") + text
                                        yield StreamEvent(type="text", content=text)

                                elif delta_type == "input_json_delta":
                                    if partial := delta.get("partial_json"):
                                        current_tool_input += partial

                                # P-122 : la réflexion ne s'affiche jamais,
                                # elle est seulement gardée pour la reprise.
                                elif delta_type == "thinking_delta" and bloc_courant is not None:
                                    bloc_courant["thinking"] = bloc_courant.get("thinking", "") + (delta.get("thinking") or "")

                                elif delta_type == "signature_delta" and bloc_courant is not None:
                                    bloc_courant["signature"] = delta.get("signature", "")

                            elif event_type == "content_block_stop":
                                if current_tool_call_id and current_tool_name:
                                    try:
                                        arguments = json.loads(current_tool_input) if current_tool_input else {}
                                    except json.JSONDecodeError:
                                        arguments = {}

                                    bloc_outil = blocs_par_index.get(event.get("index", -1))
                                    if bloc_outil is not None:
                                        bloc_outil["input"] = arguments

                                    yield StreamEvent(
                                        type="tool_call",
                                        tool_call=ToolCall(
                                            id=current_tool_call_id,
                                            name=current_tool_name,
                                            arguments=arguments,
                                        ),
                                        assistant_content_brut=(
                                            blocs_du_tour if tour_avec_reflexion else None
                                        ),
                                    )

                                    current_tool_call_id = None
                                    current_tool_name = None
                                    current_tool_input = ""

                            elif event_type == "message_delta":
                                delta = event.get("delta", {})
                                stop_reason = delta.get("stop_reason")
                                if usage_out := event.get("usage", {}).get("output_tokens"):
                                    output_tokens = usage_out

                            elif event_type == "message_stop":
                                done_emitted = True
                                yield StreamEvent(
                                    type="done",
                                    stop_reason=stop_reason or "end_turn",
                                    input_tokens=input_tokens,
                                    output_tokens=output_tokens,
                                )

                        except json.JSONDecodeError:
                            continue

                # B-480 (05/09/2026) : filet post-boucle, comme les
                # fournisseurs OpenAI-compatibles. Un flux coupé après
                # message_delta(stop_reason=tool_use) sans message_stop
                # émettait le tool_call et jamais de done : le chat attendait
                # indéfiniment.
                if not done_emitted:
                    yield StreamEvent(
                        type="done",
                        stop_reason=stop_reason or "end_turn",
                        input_tokens=input_tokens,
                        output_tokens=output_tokens,
                    )

        except httpx.HTTPStatusError as e:
            error_text = ""
            try:
                error_body = await e.response.aread()
                error_text = error_body.decode() if error_body else str(e)
            except Exception as body_err:
                logger.debug("Impossible de lire le body erreur Anthropic: %s", body_err)
                error_text = str(e)
            logger.error(f"Anthropic API error: {e.response.status_code} - {error_text}")
            yield StreamEvent(
                type="error",
                content=message_erreur_http(
                    self.config.provider, e.response.status_code
                ),
            )
        except Exception as e:
            logger.error(f"Anthropic streaming error: {e}")
            # Revue 0.48 p2 (F1) : jamais str(e) brut dans un évènement
            # relayé à l'écran - le détail vit dans le log ci-dessus. La forme
            # dit la CLASSE d'erreur : une panne de transport ouvre le circuit
            # (_is_provider_outage matche « réseau »), un bug local jamais.
            if isinstance(e, httpx.TransportError):
                yield StreamEvent(
                    type="error",
                    content=f"Erreur réseau vers le service d'IA ({type(e).__name__})",
                )
            else:
                yield StreamEvent(
                    type="error",
                    content=f"Erreur interne du service d'IA ({type(e).__name__})",
                )

    async def continue_with_tool_results(
        self,
        system_prompt: str | None,
        messages: list[dict],
        assistant_content: str,
        tool_calls: list[ToolCall],
        tool_results: list[ToolResult],
        tools: list[dict] | None = None,
        prior_turns: list[ToolTurn] | None = None,
        assistant_content_brut: "list[Any] | None" = None,
    ) -> AsyncGenerator[StreamEvent, None]:
        """Continue Anthropic conversation with tool results."""
        messages = list(messages)  # Copy
        # Multi-tours (bug lcjp 11/06/2026) : rejouer les tours précédents
        for turn in prior_turns or []:
            self._append_tool_turn(
                messages,
                turn.assistant_content,
                turn.tool_calls,
                turn.tool_results,
                turn.assistant_content_brut,
            )
        self._append_tool_turn(
            messages, assistant_content, tool_calls, tool_results, assistant_content_brut
        )

        # Stream continuation
        async for event in self.stream(system_prompt, messages, tools):
            yield event

    @staticmethod
    def _append_tool_turn(
        messages: list[dict[str, Any]],
        assistant_content: str,
        tool_calls: list[ToolCall],
        tool_results: list[ToolResult],
        assistant_content_brut: Any | None = None,
    ) -> None:
        """Ajoute un tour d'outils au format Anthropic (tool_use/tool_result blocks).

        P-122 : un tour qui portait de la réflexion (Opus 5.5, Fable) est
        rejoué TEL QUE REÇU ; le reconstruire perdrait les blocs signés (400).
        """
        assistant_content_blocks: list[dict[str, Any]] = []
        if isinstance(assistant_content_brut, list) and assistant_content_brut:
            assistant_content_blocks = list(assistant_content_brut)
        else:
            if assistant_content:
                assistant_content_blocks.append({"type": "text", "text": assistant_content})
            for tc in tool_calls:
                assistant_content_blocks.append({
                    "type": "tool_use",
                    "id": tc.id,
                    "name": tc.name,
                    "input": tc.arguments,
                })
        messages.append({
            "role": "assistant",
            "content": assistant_content_blocks,
        })

        user_content_blocks = []
        for tr in tool_results:
            result_content = tr.result
            if isinstance(result_content, dict):
                result_content = json.dumps(result_content)
            elif not isinstance(result_content, str):
                result_content = str(result_content)
            user_content_blocks.append({
                "type": "tool_result",
                "tool_use_id": tr.tool_call_id,
                "content": result_content,
                "is_error": tr.is_error,
            })
        messages.append({
            "role": "user",
            "content": user_content_blocks,
        })
