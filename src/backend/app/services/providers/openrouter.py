"""
THÉRÈSE v2 - OpenRouter Provider

OpenRouter API streaming implementation (OpenAI-compatible).
Accès unifié à 200+ modèles LLM via https://openrouter.ai/api/v1.
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
)

logger = logging.getLogger(__name__)

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"


class OpenRouterProvider(BaseProvider):
    """OpenRouter API provider (OpenAI-compatible, 200+ modèles)."""

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
        """Stream from OpenRouter API with tool support."""
        request_body = self._build_request_body(messages, tools)

        try:
            async with self.client.stream(
                "POST",
                OPENROUTER_API_URL,
                headers={
                    "Authorization": f"Bearer {self.config.api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://synoptia.fr",
                    "X-Title": "THERESE",
                },
                json=request_body,
            ) as response:
                response.raise_for_status()

                # Track tool calls being built
                tool_calls: dict[int, dict] = {}

                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]
                        if data.strip() == "[DONE]":
                            yield StreamEvent(type="done", stop_reason="stop")
                            break
                        try:
                            event = json.loads(data)
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
                                    yield StreamEvent(type="done", stop_reason="tool_calls")

                                elif finish_reason == "stop":
                                    yield StreamEvent(type="done", stop_reason="stop")

                        except json.JSONDecodeError:
                            continue

        except httpx.HTTPStatusError as e:
            logger.error(f"OpenRouter API error: {e.response.status_code}")
            yield StreamEvent(type="error", content=f"API error: {e.response.status_code}")
        except Exception as e:
            logger.error(f"OpenRouter streaming error: {e}")
            yield StreamEvent(type="error", content=str(e))

    async def continue_with_tool_results(
        self,
        system_prompt: str | None,
        messages: list[dict],
        assistant_content: str,
        tool_calls: list[ToolCall],
        tool_results: list[ToolResult],
        tools: list[dict] | None = None,
    ) -> AsyncGenerator[StreamEvent, None]:
        """Continue OpenRouter conversation with tool results."""
        messages = list(messages)  # Copy

        # Build assistant message with tool_calls
        assistant_message = {
            "role": "assistant",
            "content": assistant_content or None,
            "tool_calls": [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.name,
                        "arguments": json.dumps(tc.arguments) if tc.arguments else "{}",
                    },
                }
                for tc in tool_calls
            ],
        }
        messages.append(assistant_message)

        # Add tool result messages
        for tr in tool_results:
            result_content = tr.result
            if isinstance(result_content, dict):
                result_content = json.dumps(result_content)
            elif not isinstance(result_content, str):
                result_content = str(result_content)

            messages.append({
                "role": "tool",
                "tool_call_id": tr.tool_call_id,
                "content": result_content,
            })

        # Stream continuation
        async for event in self.stream(system_prompt, messages, tools):
            yield event
