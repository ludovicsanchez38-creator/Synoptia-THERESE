"""
THÉRÈSE v2 - Gemini Provider

Google Gemini API streaming implementation.
Sprint 2 - PERF-2.1: Extracted from monolithic llm.py
"""

import json
import logging
from typing import AsyncGenerator, Any

import httpx

from .base import (
    BaseProvider,
    StreamEvent,
    ToolCall,
    ToolResult,
)

logger = logging.getLogger(__name__)

GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"


class GeminiProvider(BaseProvider):
    """Google Gemini API provider."""

    async def stream(
        self,
        system_prompt: str | None,
        messages: list[dict],
        tools: list[dict] | None = None,
        enable_grounding: bool = True,
    ) -> AsyncGenerator[StreamEvent, None]:
        """
        Stream from Google Gemini API with optional Google Search grounding.

        Args:
            system_prompt: System instruction
            messages: Messages in Gemini format (contents with parts)
            tools: Not used for Gemini (grounding instead)
            enable_grounding: Enable Google Search grounding (default True)
        """
        model = self.config.model
        url = f"{GEMINI_API_BASE}/{model}:streamGenerateContent"

        try:
            request_body: dict[str, Any] = {
                "contents": messages,
                "generationConfig": {
                    "maxOutputTokens": self.config.max_tokens,
                    "temperature": self.config.temperature,
                },
            }

            # Add system instruction if present
            if system_prompt:
                request_body["systemInstruction"] = {
                    "parts": [{"text": system_prompt}]
                }

            # Add Google Search grounding tool (new format for Gemini 3)
            if enable_grounding:
                request_body["tools"] = [{"google_search": {}}]

            async with self.client.stream(
                "POST",
                url,
                params={"key": self.config.api_key, "alt": "sse"},
                headers={"Content-Type": "application/json"},
                json=request_body,
            ) as response:
                if response.status_code != 200:
                    error_body = await response.aread()
                    logger.error(f"Gemini API {response.status_code}: {error_body.decode()}")
                    yield StreamEvent(type="error", content=f"API error: {response.status_code}")
                    return
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]
                        if not data.strip():
                            continue
                        try:
                            event = json.loads(data)
                            candidates = event.get("candidates", [])
                            if candidates:
                                content = candidates[0].get("content", {})
                                parts = content.get("parts", [])
                                for part in parts:
                                    if text := part.get("text"):
                                        yield StreamEvent(type="text", content=text)
                                # Log grounding metadata if present
                                grounding = candidates[0].get("groundingMetadata")
                                if grounding:
                                    sources = grounding.get("webSearchQueries", [])
                                    if sources:
                                        logger.debug(f"Gemini grounding queries: {sources}")
                        except json.JSONDecodeError:
                            continue

            yield StreamEvent(type="done", stop_reason="end_turn")

        except httpx.HTTPStatusError as e:
            error_body = e.response.text if hasattr(e.response, 'text') else str(e)
            logger.error(f"Gemini API error: {e.response.status_code} - {error_body}")
            yield StreamEvent(type="error", content=f"API error: {e.response.status_code}")
        except Exception as e:
            logger.error(f"Gemini streaming error: {e}")
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
        """Gemini doesn't support tool calling continuation yet."""
        yield StreamEvent(type="done", stop_reason="end_turn")
