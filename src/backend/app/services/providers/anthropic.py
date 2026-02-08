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
)

logger = logging.getLogger(__name__)

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"


class AnthropicProvider(BaseProvider):
    """Anthropic Claude API provider."""

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

        request_body: dict[str, Any] = {
            "model": self.config.model,
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature,
            "system": system_prompt,
            "messages": messages,
            "stream": True,
        }

        if anthropic_tools:
            request_body["tools"] = anthropic_tools

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

                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]
                        if data.strip() == "[DONE]":
                            break
                        try:
                            event = json.loads(data)
                            event_type = event.get("type")

                            if event_type == "content_block_start":
                                content_block = event.get("content_block", {})
                                if content_block.get("type") == "tool_use":
                                    current_tool_call_id = content_block.get("id")
                                    current_tool_name = content_block.get("name")
                                    current_tool_input = ""

                            elif event_type == "content_block_delta":
                                delta = event.get("delta", {})
                                delta_type = delta.get("type")

                                if delta_type == "text_delta":
                                    if text := delta.get("text"):
                                        yield StreamEvent(type="text", content=text)

                                elif delta_type == "input_json_delta":
                                    if partial := delta.get("partial_json"):
                                        current_tool_input += partial

                            elif event_type == "content_block_stop":
                                if current_tool_call_id and current_tool_name:
                                    try:
                                        arguments = json.loads(current_tool_input) if current_tool_input else {}
                                    except json.JSONDecodeError:
                                        arguments = {}

                                    yield StreamEvent(
                                        type="tool_call",
                                        tool_call=ToolCall(
                                            id=current_tool_call_id,
                                            name=current_tool_name,
                                            arguments=arguments,
                                        ),
                                    )

                                    current_tool_call_id = None
                                    current_tool_name = None
                                    current_tool_input = ""

                            elif event_type == "message_delta":
                                delta = event.get("delta", {})
                                stop_reason = delta.get("stop_reason")

                            elif event_type == "message_stop":
                                yield StreamEvent(type="done", stop_reason=stop_reason or "end_turn")

                        except json.JSONDecodeError:
                            continue

        except httpx.HTTPStatusError as e:
            try:
                error_body = await e.response.aread()
                error_text = error_body.decode() if error_body else str(e)
            except Exception:
                error_text = str(e)
            logger.error(f"Anthropic API error: {e.response.status_code} - {error_text}")
            yield StreamEvent(type="error", content=f"API error: {e.response.status_code}")
        except Exception as e:
            logger.error(f"Anthropic streaming error: {e}")
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
        """Continue Anthropic conversation with tool results."""
        # Build assistant message with tool_use blocks
        assistant_content_blocks = []
        if assistant_content:
            assistant_content_blocks.append({"type": "text", "text": assistant_content})

        for tc in tool_calls:
            assistant_content_blocks.append({
                "type": "tool_use",
                "id": tc.id,
                "name": tc.name,
                "input": tc.arguments,
            })

        messages = list(messages)  # Copy
        messages.append({
            "role": "assistant",
            "content": assistant_content_blocks,
        })

        # Build user message with tool_result blocks
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

        # Stream continuation
        async for event in self.stream(system_prompt, messages, tools):
            yield event
