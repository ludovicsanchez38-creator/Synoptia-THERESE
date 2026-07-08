"""
THÉRÈSE v2 - Mistral Provider

Mistral API streaming implementation.
Sprint 2 - PERF-2.1: Extracted from monolithic llm.py

API Mistral = compatible OpenAI : meme protocole de streaming des tool_calls
(arguments envoyes en chunks, accumules par index) et meme boucle de
continuation (message assistant avec tool_calls + messages role=tool, puis
re-stream). Cette implementation est alignee sur openai.py.
"""

import json
import logging
from typing import AsyncGenerator

import httpx

from .base import (
    BaseProvider,
    StreamEvent,
    ToolCall,
    ToolResult,
    ToolTurn,
)

logger = logging.getLogger(__name__)

MISTRAL_API_URL = "https://api.mistral.ai/v1/chat/completions"


class MistralProvider(BaseProvider):
    """Mistral API provider."""

    def _build_request_body(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
    ) -> dict:
        request_body: dict = {
            "model": self.config.model,
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature,
            "messages": messages,
            "stream": True,
            # Usage réel (dette 14/06/2026) : sans ce flag, le chunk usage final
            # n'est pas envoyé du tout par l'API en streaming.
            "stream_options": {"include_usage": True},
        }
        if tools:
            request_body["tools"] = tools
            request_body["tool_choice"] = "auto"
        return request_body

    async def stream(
        self,
        system_prompt: str | None,
        messages: list[dict],
        tools: list[dict] | None = None,
    ) -> AsyncGenerator[StreamEvent, None]:
        """Stream from Mistral API avec support des outils.

        Les tool_calls sont streames par fragments (id/nom dans un chunk,
        arguments en plusieurs morceaux) : on les accumule par index puis on
        les emet completement a la fin (finish_reason == "tool_calls"), avec un
        StreamEvent done stop_reason="tool_calls" pour que l'orchestrateur
        execute les outils PUIS rappelle continue_with_tool_results. Sans ca,
        Mistral renvoyait une reponse vide des qu'un outil etait sollicite
        (CRM, generation Word, synthese board).
        """
        request_body = self._build_request_body(messages, tools)
        done_emitted = False
        # Usage réel (dette 14/06/2026) : le chunk usage (stream_options.
        # include_usage) arrive APRÈS le chunk finish_reason, choices vide - on
        # mémorise stop_reason SANS break pour laisser la boucle l'atteindre.
        pending_stop_reason: str | None = None
        input_tokens: int | None = None
        output_tokens: int | None = None

        try:
            async with self.client.stream(
                "POST",
                MISTRAL_API_URL,
                headers={
                    "Authorization": f"Bearer {self.config.api_key}",
                    "Content-Type": "application/json",
                },
                json=request_body,
            ) as response:
                response.raise_for_status()

                # tool_calls en cours de construction, indexes par position
                tool_calls: dict[int, dict] = {}

                async for line in response.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    data = line[6:]
                    if data.strip() == "[DONE]":
                        if not done_emitted:
                            yield StreamEvent(
                                type="done",
                                stop_reason=pending_stop_reason or "end_turn",
                                input_tokens=input_tokens,
                                output_tokens=output_tokens,
                            )
                            done_emitted = True
                        break
                    try:
                        event = json.loads(data)
                    except json.JSONDecodeError:
                        continue

                    if usage := event.get("usage"):
                        input_tokens = usage.get("prompt_tokens", input_tokens)
                        output_tokens = usage.get("completion_tokens", output_tokens)

                    choices = event.get("choices", [])
                    if not choices:
                        continue
                    delta = choices[0].get("delta", {})
                    finish_reason = choices[0].get("finish_reason")

                    # Texte
                    if content := delta.get("content"):
                        yield StreamEvent(type="text", content=content)

                    # Fragments de tool_calls (accumulation par index)
                    if tool_call_deltas := delta.get("tool_calls"):
                        for tc_delta in tool_call_deltas:
                            idx = tc_delta.get("index", 0)
                            if idx not in tool_calls:
                                tool_calls[idx] = {"id": tc_delta.get("id", ""), "name": "", "arguments": ""}
                            if tc_delta.get("id"):
                                tool_calls[idx]["id"] = tc_delta["id"]
                            if func := tc_delta.get("function"):
                                if name := func.get("name"):
                                    tool_calls[idx]["name"] = name
                                if args := func.get("arguments"):
                                    tool_calls[idx]["arguments"] += args

                    # Fin de tour : mémoriser seulement, ne PAS émettre "done" ni
                    # break ici - il faut laisser la boucle atteindre le chunk
                    # usage (ou [DONE]) pour ne pas perdre l'usage réel.
                    if finish_reason == "tool_calls" or (finish_reason and tool_calls):
                        if not pending_stop_reason:
                            for tc in tool_calls.values():
                                try:
                                    arguments = json.loads(tc["arguments"]) if tc["arguments"] else {}
                                except json.JSONDecodeError:
                                    arguments = {}
                                yield StreamEvent(
                                    type="tool_call",
                                    tool_call=ToolCall(
                                        id=tc["id"],
                                        name=tc["name"],
                                        arguments=arguments,
                                    ),
                                )
                        pending_stop_reason = "tool_calls"
                    elif finish_reason:
                        pending_stop_reason = pending_stop_reason or "end_turn"

            # Filet : si le flux se termine sans jamais voir [DONE] (coupure
            # après finish_reason, ou pas de finish_reason explicite du tout).
            if not done_emitted:
                yield StreamEvent(
                    type="done",
                    stop_reason=pending_stop_reason or "end_turn",
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                )

        except httpx.HTTPStatusError as e:
            logger.error(f"Mistral API error: {e.response.status_code}")
            yield StreamEvent(type="error", content=f"API error: {e.response.status_code}")
        except Exception as e:
            logger.error(f"Mistral streaming error: {e}")
            yield StreamEvent(type="error", content=str(e))

    async def continue_with_tool_results(
        self,
        system_prompt: str | None,
        messages: list[dict],
        assistant_content: str,
        tool_calls: list[ToolCall],
        tool_results: list[ToolResult],
        tools: list[dict] | None = None,
        prior_turns: list[ToolTurn] | None = None,
    ) -> AsyncGenerator[StreamEvent, None]:
        """Renvoie les resultats d'outils a Mistral et re-stream la reponse finale.

        Format OpenAI-compatible : un message assistant portant les tool_calls,
        puis un message role="tool" par resultat (tool_call_id + content).
        """
        messages = list(messages)  # copie
        # Multi-tours (bug lcjp 11/06/2026) : rejouer les tours précédents
        # avant le tour courant, sinon le modèle re-demande le même outil.
        for turn in prior_turns or []:
            self._append_openai_tool_turn(
                messages, turn.assistant_content, turn.tool_calls, turn.tool_results
            )
        self._append_openai_tool_turn(messages, assistant_content, tool_calls, tool_results)

        async for event in self.stream(system_prompt, messages, tools):
            yield event
