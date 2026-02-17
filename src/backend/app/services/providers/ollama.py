"""
THÉRÈSE v2 - Ollama Provider

Local Ollama API streaming implementation.
Sprint 2 - PERF-2.1: Extracted from monolithic llm.py
"""

import json
import logging
from typing import AsyncGenerator

from .base import (
    BaseProvider,
    StreamEvent,
    ToolCall,
    ToolResult,
)

logger = logging.getLogger(__name__)


class OllamaProvider(BaseProvider):
    """Local Ollama API provider."""

    async def stream(
        self,
        system_prompt: str | None,
        messages: list[dict],
        tools: list[dict] | None = None,
    ) -> AsyncGenerator[StreamEvent, None]:
        """Stream from local Ollama."""
        base_url = (self.config.base_url or "http://localhost:11434").rstrip("/")

        try:
            # Construire la liste de messages avec le system prompt en premier
            # /api/chat attend le system prompt comme message role="system",
            # pas comme champ top-level (contrairement à /api/generate)
            chat_messages: list[dict] = []
            if system_prompt:
                chat_messages.append({"role": "system", "content": system_prompt})
            chat_messages.extend(
                m for m in messages if m.get("role") != "system"
            )

            async with self.client.stream(
                "POST",
                f"{base_url}/api/chat",
                json={
                    "model": self.config.model,
                    "messages": chat_messages,
                    "stream": True,
                },
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line:
                        try:
                            event = json.loads(line)
                            if content := event.get("message", {}).get("content"):
                                yield StreamEvent(type="text", content=content)
                        except json.JSONDecodeError:
                            continue

            yield StreamEvent(type="done", stop_reason="end_turn")

        except Exception as e:
            logger.error(f"Ollama streaming error: {e}")
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
        """Ollama doesn't support tool calling in this implementation."""
        yield StreamEvent(type="done", stop_reason="end_turn")
