"""
THÉRÈSE v2 - OpenAI Provider

GPT API streaming implementation with tool support.
Sprint 2 - PERF-2.1: Extracted from monolithic llm.py
"""

import json
import logging
from typing import AsyncGenerator, Any

import httpx

from .base import (
    BaseProvider,
    LLMConfig,
    StreamEvent,
    ToolCall,
    ToolResult,
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
        }

        if _uses_max_completion_tokens(self.config.model):
            request_body["max_completion_tokens"] = self.config.max_tokens
        else:
            request_body["max_tokens"] = self.config.max_tokens

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
        """Stream from OpenAI API with tool support."""
        request_body = self._build_request_body(messages, tools)

        try:
            async with self.client.stream(
                "POST",
                OPENAI_API_URL,
                headers={
                    "Authorization": f"Bearer {self.config.api_key}",
                    "Content-Type": "application/json",
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
                                    yield StreamEvent(type="done", stop_reason="tool_calls")

                                elif finish_reason == "stop":
                                    yield StreamEvent(type="done", stop_reason="stop")

                        except json.JSONDecodeError:
                            continue

        except httpx.HTTPStatusError as e:
            logger.error(f"OpenAI API error: {e.response.status_code}")
            yield StreamEvent(type="error", content=f"API error: {e.response.status_code}")
        except Exception as e:
            logger.error(f"OpenAI streaming error: {e}")
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
        """Continue OpenAI conversation with tool results."""
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
