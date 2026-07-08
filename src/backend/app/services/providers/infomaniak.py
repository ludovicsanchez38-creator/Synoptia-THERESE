"""
THÉRÈSE v2 - Infomaniak AI Provider

Infomaniak AI API streaming implementation (OpenAI-compatible).
Provider IA suisse souverain (serveurs en Suisse, conformité RGPD).
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
)

logger = logging.getLogger(__name__)

INFOMANIAK_API_URL = "https://api.infomaniak.com/1/ai/chat/completions"


class InfomaniakProvider(BaseProvider):
    """Infomaniak AI provider (OpenAI-compatible, serveurs suisses)."""

    def _build_request_body(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
    ) -> dict[str, Any]:
        """Build request body (OpenAI-compatible format)."""
        request_body: dict[str, Any] = {
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
        """Stream from Infomaniak AI API."""
        request_body = self._build_request_body(messages, tools)

        try:
            async with self.client.stream(
                "POST",
                INFOMANIAK_API_URL,
                headers={
                    "Authorization": f"Bearer {self.config.api_key}",
                    "Content-Type": "application/json",
                },
                json=request_body,
            ) as response:
                response.raise_for_status()

                tool_calls: dict[int, dict] = {}
                # Usage réel (dette 14/06/2026) : le chunk usage (stream_options.
                # include_usage) arrive APRÈS le chunk finish_reason, choices vide.
                # On mémorise stop_reason et on n'émet "done" qu'à la toute fin
                # (chunk usage ou [DONE]) pour ne pas le manquer.
                pending_stop_reason: str | None = None
                input_tokens: int | None = None
                output_tokens: int | None = None
                # Garde de robustesse : si la connexion se coupe après
                # finish_reason mais avant [DONE]/le chunk usage, il faut
                # quand même émettre "done" (sinon chat.py reste bloqué en
                # attente indéfiniment de ce signal).
                done_emitted = False

                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]
                        if data.strip() == "[DONE]":
                            yield StreamEvent(
                                type="done",
                                stop_reason=pending_stop_reason or "stop",
                                input_tokens=input_tokens,
                                output_tokens=output_tokens,
                            )
                            done_emitted = True
                            break
                        try:
                            event = json.loads(data)
                            if usage := event.get("usage"):
                                input_tokens = usage.get("prompt_tokens", input_tokens)
                                output_tokens = usage.get("completion_tokens", output_tokens)
                            choices = event.get("choices", [])
                            if choices:
                                delta = choices[0].get("delta", {})
                                finish_reason = choices[0].get("finish_reason")

                                if content := delta.get("content"):
                                    yield StreamEvent(type="text", content=content)

                                if tool_call_deltas := delta.get("tool_calls"):
                                    for tc_delta in tool_call_deltas:
                                        idx = tc_delta.get("index", 0)

                                        if idx not in tool_calls:
                                            tool_calls[idx] = {
                                                "id": tc_delta.get("id", ""),
                                                "name": "",
                                                "arguments": "",
                                            }

                                        if func := tc_delta.get("function"):
                                            if name := func.get("name"):
                                                tool_calls[idx]["name"] = name
                                            if args := func.get("arguments"):
                                                tool_calls[idx]["arguments"] += args

                                if finish_reason == "tool_calls":
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

                                elif finish_reason == "stop":
                                    pending_stop_reason = "stop"

                        except json.JSONDecodeError:
                            continue

            # Filet : le flux s'est terminé sans jamais voir [DONE] (coupure
            # après finish_reason, ou pas de finish_reason explicite du tout).
            if not done_emitted:
                yield StreamEvent(
                    type="done",
                    stop_reason=pending_stop_reason or "stop",
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                )

        except httpx.HTTPStatusError as e:
            logger.error(f"Infomaniak API error: {e.response.status_code}")
            yield StreamEvent(type="error", content=f"API error: {e.response.status_code}")
        except Exception as e:
            logger.error(f"Infomaniak streaming error: {e}")
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
        """Continue Infomaniak conversation with tool results."""
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
