"""
THÉRÈSE v2 - Grok Provider

xAI Grok API streaming implementation (OpenAI-compatible).
Sprint 2 - PERF-2.1: Extracted from monolithic llm.py
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
)

logger = logging.getLogger(__name__)

GROK_API_URL = "https://api.x.ai/v1/chat/completions"


class GrokProvider(BaseProvider):
    """xAI Grok API provider (OpenAI-compatible)."""

    async def stream(
        self,
        system_prompt: str | None,
        messages: list[dict],
        tools: list[dict] | None = None,
    ) -> AsyncGenerator[StreamEvent, None]:
        """Stream from xAI Grok API."""
        try:
            async with self.client.stream(
                "POST",
                GROK_API_URL,
                headers={
                    "Authorization": f"Bearer {self.config.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.config.model,
                    "max_tokens": self.config.max_tokens,
                    "temperature": self.config.temperature,
                    "messages": messages,
                    "stream": True,
                },
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]
                        if data.strip() == "[DONE]":
                            break
                        try:
                            event = json.loads(data)
                            choices = event.get("choices", [])
                            if choices:
                                delta = choices[0].get("delta", {})
                                if content := delta.get("content"):
                                    yield StreamEvent(type="text", content=content)
                        except json.JSONDecodeError:
                            continue

            yield StreamEvent(type="done", stop_reason="end_turn")

        except httpx.HTTPStatusError as e:
            logger.error(f"Grok API error: {e.response.status_code}")
            yield StreamEvent(type="error", content=f"API error: {e.response.status_code}")
        except Exception as e:
            logger.error(f"Grok streaming error: {e}")
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
        """Grok doesn't support tool calling in this implementation."""
        yield StreamEvent(type="done", stop_reason="end_turn")
