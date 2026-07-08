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
from typing import Any, AsyncGenerator, Literal

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
    OPENROUTER = "openrouter"
    PERPLEXITY = "perplexity"
    DEEPSEEK = "deepseek"
    INFOMANIAK = "infomaniak"


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
class ToolTurn:
    """Un tour d'outils complet (texte assistant + appels + résultats).

    Les continuations multi-tours doivent REJOUER les tours précédents dans
    le contexte envoyé au modèle, sinon il re-demande les mêmes outils en
    boucle puis invente une explication d'échec (bug lcjp 11/06/2026).
    """
    assistant_content: str
    tool_calls: list[ToolCall]
    tool_results: list[ToolResult]


@dataclass
class StreamEvent:
    """An event from the LLM stream."""
    type: Literal["text", "tool_call", "done", "error"]
    content: str | None = None
    tool_call: ToolCall | None = None
    stop_reason: str | None = None
    # Usage réel du provider (event type="done"), quand disponible. None si le
    # provider ne l'a pas encore fourni : l'appelant retombe alors sur
    # l'estimation ~2 tokens/mot (cf chat.py/board.py).
    input_tokens: int | None = None
    output_tokens: int | None = None


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
        prior_turns: list[ToolTurn] | None = None,
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
            prior_turns: Tours d'outils PRÉCÉDENTS de la même réponse, à
                rejouer dans l'ordre avant le tour courant (multi-tours)

        Yields:
            StreamEvent objects
        """
        pass

    @staticmethod
    def _append_openai_tool_turn(
        messages: list[dict[str, Any]],
        assistant_content: str,
        tool_calls: list[ToolCall],
        tool_results: list[ToolResult],
    ) -> None:
        """Ajoute un tour d'outils au format OpenAI-compatible (in place).

        Un message assistant portant les tool_calls (arguments en chaîne
        JSON), puis un message role="tool" par résultat (tool_call_id).
        Partagé par OpenAI/Grok/Mistral/DeepSeek/Infomaniak/OpenRouter/
        Perplexity.
        """
        messages.append({
            "role": "assistant",
            # BUG-108 (lcjp, 12/06/2026) : Mistral rejette en 400 un message
            # assistant ayant à la fois un content NON vide ET des tool_calls
            # (le modèle écrivait du texte avant l'appel d'outil → 400 → résultat
            # read_emails perdu → boucle « Max tool iterations »). Un message
            # porteur de tool_calls ne transporte donc jamais de texte : on force
            # `None` (valeur canonique OpenAI/litellm pour un message tool-call,
            # déjà envoyée par l'ancien code quand le texte était vide, donc
            # éprouvée côté Mistral). Le texte pré-appel reste affiché/streamé à
            # l'utilisateur. Couvre aussi OpenRouter/Infomaniak routant vers Mistral.
            "content": None,
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
        })
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
