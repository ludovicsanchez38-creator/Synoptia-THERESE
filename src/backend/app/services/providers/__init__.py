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
)
from .gemini import GeminiProvider
from .grok import GrokProvider
from .mistral import MistralProvider
from .ollama import OllamaProvider
from .openai import OpenAIProvider

__all__ = [
    # Enums and types
    "LLMProvider",
    "LLMConfig",
    "Message",
    "ToolCall",
    "ToolResult",
    "StreamEvent",
    # Base class
    "BaseProvider",
    # Provider implementations
    "AnthropicProvider",
    "OpenAIProvider",
    "GeminiProvider",
    "MistralProvider",
    "GrokProvider",
    "OllamaProvider",
]
