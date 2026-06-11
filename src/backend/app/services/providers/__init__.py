"""
THÉRÈSE v2 - LLM Providers Package

Re-exports all provider classes for convenient importing.
Sprint 2 - PERF-2.1: Modular provider structure
"""

from .anthropic import AnthropicProvider
from .base import (
    BaseProvider,
    LLMConfig,
    LLMProvider,
    Message,
    StreamEvent,
    ToolCall,
    ToolResult,
    ToolTurn,
)
from .deepseek import DeepSeekProvider
from .gemini import GeminiProvider
from .grok import GrokProvider
from .infomaniak import InfomaniakProvider
from .mistral import MistralProvider
from .ollama import OllamaProvider
from .openai import OpenAIProvider
from .openrouter import OpenRouterProvider
from .perplexity import PerplexityProvider

__all__ = [
    # Enums and types
    "LLMProvider",
    "LLMConfig",
    "Message",
    "ToolCall",
    "ToolResult",
    "ToolTurn",
    "StreamEvent",
    # Base class
    "BaseProvider",
    # Provider implementations
    "AnthropicProvider",
    "OpenAIProvider",
    "OpenRouterProvider",
    "PerplexityProvider",
    "DeepSeekProvider",
    "GeminiProvider",
    "MistralProvider",
    "GrokProvider",
    "OllamaProvider",
    "InfomaniakProvider",
]
