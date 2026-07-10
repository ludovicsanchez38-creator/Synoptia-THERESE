"""
THÉRÈSE v2 - OpenAI Provider

GPT API streaming implementation with tool support.
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
)

logger = logging.getLogger(__name__)

OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"


def _uses_max_completion_tokens(model: str) -> bool:
    """Check if model uses max_completion_tokens instead of max_tokens.

    GPT-5.x and o-series models require max_completion_tokens parameter.
    """
    model_lower = model.lower()
    return (
        model_lower.startswith("gpt-5") or
        model_lower.startswith("o1") or
        model_lower.startswith("o3") or
        model_lower.startswith("o4")
    )


class OpenAIProvider(BaseProvider):
    """OpenAI GPT API provider."""

    # US-009 : URL surclassable - GrokProvider réutilise toute la boucle
    # d'outils (xAI est OpenAI-compatible) en ne changeant que l'endpoint.
    API_URL = OPENAI_API_URL

    def _build_request_body(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
    ) -> dict[str, Any]:
        """Build request body with correct token parameter."""
        request_body: dict[str, Any] = {
            "model": self.config.model,
            "temperature": self.config.temperature,
            "messages": messages,
            "stream": True,
            # Usage réel (dette 14/06/2026) : sans ce flag, le chunk usage final
            # n'est pas envoyé du tout par l'API OpenAI en streaming.
            "stream_options": {"include_usage": True},
        }

        if _uses_max_completion_tokens(self.config.model):
            request_body["max_completion_tokens"] = self.config.max_tokens
        else:
            request_body["max_tokens"] = self.config.max_tokens

        if tools:
            request_body["tools"] = tools
            request_body["tool_choice"] = "auto"

        # Effort de raisonnement - envoye SEULEMENT aux modeles verifies le
        # 10/07/2026 : GPT-5.6 (none->max) et Grok 4.5 (low/medium/high,
        # OpenAI-compatible via GrokProvider). Les 5.5/5.4 non sources = rien.
        if self.config.effort:
            model_lower = self.config.model.lower()
            if model_lower.startswith("gpt-5.6"):
                request_body["reasoning_effort"] = self.config.effort
            elif model_lower.startswith("grok-4.5"):
                request_body["reasoning_effort"] = (
                    "high" if self.config.effort == "max" else self.config.effort
                )

        return request_body

    async def stream(
        self,
        system_prompt: str | None,
        messages: list[dict],
        tools: list[dict] | None = None,
    ) -> AsyncGenerator[StreamEvent, None]:
        """Stream from OpenAI API with tool support."""
        request_body = self._build_request_body(messages, tools)

        try:
            async with self.client.stream(
                "POST",
                self.API_URL,
                headers={
                    "Authorization": f"Bearer {self.config.api_key}",
                    "Content-Type": "application/json",
                },
                json=request_body,
            ) as response:
                response.raise_for_status()

                # Track tool calls being built
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

                                # Handle text content
                                if content := delta.get("content"):
                                    yield StreamEvent(type="text", content=content)

                                # Handle tool calls
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

                                # Check if done
                                if finish_reason == "tool_calls":
                                    # Emit all collected tool calls
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
            logger.error(f"{type(self).__name__} API error: {e.response.status_code}")
            yield StreamEvent(type="error", content=f"API error: {e.response.status_code}")
        except Exception as e:
            logger.error(f"{type(self).__name__} streaming error: {e}")
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
        """Continue OpenAI conversation with tool results."""
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
