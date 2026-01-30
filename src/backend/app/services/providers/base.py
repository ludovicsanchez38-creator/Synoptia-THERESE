"""
THÉRÈSE v2 - LLM Provider Base Module

Shared types and ABC for all LLM providers.
Sprint 2 - PERF-2.1: Extracted from monolithic llm.py
"""

import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import AsyncGenerator, Literal, Any

import httpx

logger = logging.getLogger(__name__)


class LLMProvider(str, Enum):
    """Supported LLM providers."""

    ANTHROPIC = "anthropic"
    MISTRAL = "mistral"
    OLLAMA = "ollama"
    OPENAI = "openai"
    GEMINI = "gemini"
    GROK = "grok"


@dataclass
class LLMConfig:
    """LLM configuration."""

    provider: LLMProvider
    model: str
    max_tokens: int = 4096
    temperature: float = 0.7
    context_window: int = 128000
    api_key: str | None = None
    base_url: str | None = None


@dataclass
class Message:
    """Chat message."""

    role: Literal["user", "assistant", "system"]
    content: str


@dataclass
class ToolCall:
    """A tool call from the LLM."""
    id: str
    name: str
    arguments: dict[str, Any]


@dataclass
class ToolResult:
    """Result of a tool execution to send back to the LLM."""
    tool_call_id: str
    result: Any
    is_error: bool = False


@dataclass
class StreamEvent:
    """An event from the LLM stream."""
    type: Literal["text", "tool_call", "done", "error"]
    content: str | None = None
    tool_call: ToolCall | None = None
    stop_reason: str | None = None


class BaseProvider(ABC):
    """Abstract base class for LLM providers."""

    def __init__(self, config: LLMConfig, client: httpx.AsyncClient):
        self.config = config
        self.client = client

    @abstractmethod
    async def stream(
        self,
        system_prompt: str | None,
        messages: list[dict],
        tools: list[dict] | None = None,
    ) -> AsyncGenerator[StreamEvent, None]:
        """
        Stream response from the LLM.

        Args:
            system_prompt: System prompt
            messages: Messages in provider-native format
            tools: Optional tools definitions

        Yields:
            StreamEvent objects
        """
        pass

    @abstractmethod
    async def continue_with_tool_results(
        self,
        system_prompt: str | None,
        messages: list[dict],
        assistant_content: str,
        tool_calls: list[ToolCall],
        tool_results: list[ToolResult],
        tools: list[dict] | None = None,
    ) -> AsyncGenerator[StreamEvent, None]:
        """
        Continue streaming after tool execution.

        Args:
            system_prompt: System prompt
            messages: Messages before tool calls
            assistant_content: Text generated before tool calls
            tool_calls: The tool calls that were made
            tool_results: Results of those tool calls
            tools: Tools to make available

        Yields:
            StreamEvent objects
        """
        pass

    def _parse_sse_line(self, line: str) -> dict | None:
        """Parse an SSE data line to JSON."""
        if line.startswith("data: "):
            data = line[6:]
            if data.strip() == "[DONE]":
                return None
            try:
                return json.loads(data)
            except json.JSONDecodeError:
                return None
        return None
