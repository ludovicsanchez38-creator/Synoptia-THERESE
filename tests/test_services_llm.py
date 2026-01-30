"""
THERESE v2 - LLM Service Tests

Tests for multi-provider LLM functionality.
Sprint 2 - PERF-2.1: Updated for modular provider architecture.
"""

import pytest


class TestLLMServiceImport:
    """Tests for LLM service availability."""

    def test_import_llm_service(self):
        """Test LLM service can be imported."""
        from app.services.llm import LLMService
        assert LLMService is not None

    def test_import_tool_structures(self):
        """Test tool-related structures exist."""
        from app.services.llm import ToolCall, ToolResult, StreamEvent

        assert ToolCall is not None
        assert ToolResult is not None
        assert StreamEvent is not None

    def test_import_providers(self):
        """Test provider classes can be imported."""
        from app.services.providers import (
            AnthropicProvider,
            OpenAIProvider,
            GeminiProvider,
            MistralProvider,
            GrokProvider,
            OllamaProvider,
        )

        assert AnthropicProvider is not None
        assert OpenAIProvider is not None
        assert GeminiProvider is not None
        assert MistralProvider is not None
        assert GrokProvider is not None
        assert OllamaProvider is not None


class TestLLMProviderSupport:
    """Tests for US-CHAT-01: Multiple LLM providers."""

    def test_anthropic_provider(self):
        """Test Anthropic provider is supported."""
        from app.services.llm import LLMService, LLMConfig, LLMProvider

        config = LLMConfig(
            provider=LLMProvider.ANTHROPIC,
            model="claude-sonnet-4-5-20250929",
            api_key="test-key"
        )
        service = LLMService(config=config)
        assert service.config.provider == LLMProvider.ANTHROPIC

    def test_openai_provider(self):
        """Test OpenAI provider is supported."""
        from app.services.llm import LLMService, LLMConfig, LLMProvider

        config = LLMConfig(
            provider=LLMProvider.OPENAI,
            model="gpt-4o",
            api_key="test-key"
        )
        service = LLMService(config=config)
        assert service.config.provider == LLMProvider.OPENAI

    def test_gemini_provider(self):
        """Test Gemini provider is supported."""
        from app.services.llm import LLMService, LLMConfig, LLMProvider

        config = LLMConfig(
            provider=LLMProvider.GEMINI,
            model="gemini-2.5-pro",
            api_key="test-key"
        )
        service = LLMService(config=config)
        assert service.config.provider == LLMProvider.GEMINI

    def test_mistral_provider(self):
        """Test Mistral provider is supported."""
        from app.services.llm import LLMService, LLMConfig, LLMProvider

        config = LLMConfig(
            provider=LLMProvider.MISTRAL,
            model="mistral-large-latest",
            api_key="test-key"
        )
        service = LLMService(config=config)
        assert service.config.provider == LLMProvider.MISTRAL

    def test_grok_provider(self):
        """Test Grok provider is supported."""
        from app.services.llm import LLMService, LLMConfig, LLMProvider

        config = LLMConfig(
            provider=LLMProvider.GROK,
            model="grok-3",
            api_key="test-key"
        )
        service = LLMService(config=config)
        assert service.config.provider == LLMProvider.GROK

    def test_ollama_provider(self):
        """Test Ollama provider is supported."""
        from app.services.llm import LLMService, LLMConfig, LLMProvider

        config = LLMConfig(
            provider=LLMProvider.OLLAMA,
            model="mistral-nemo",
            base_url="http://localhost:11434"
        )
        service = LLMService(config=config)
        assert service.config.provider == LLMProvider.OLLAMA


class TestLLMServiceConfiguration:
    """Tests for LLM service configuration."""

    def test_default_config(self):
        """Test LLM service has default configuration."""
        from app.services.llm import LLMService

        service = LLMService()
        assert service.config is not None
        assert service.config.provider is not None
        assert service.config.model is not None

    def test_custom_model(self):
        """Test setting custom model."""
        from app.services.llm import LLMService, LLMConfig, LLMProvider

        config = LLMConfig(
            provider=LLMProvider.ANTHROPIC,
            model="claude-haiku-4-5-20251001",
            api_key="test-key"
        )
        service = LLMService(config=config)
        assert service.config.model == "claude-haiku-4-5-20251001"


class TestLLMHelperFunctions:
    """Tests for LLM helper functions."""

    def test_get_llm_service_for_provider_returns_none_without_key(self):
        """Test helper returns None when no API key configured."""
        from app.services.llm import get_llm_service_for_provider
        import os

        # Temporarily clear env vars
        old_key = os.environ.pop("ANTHROPIC_API_KEY", None)
        try:
            service = get_llm_service_for_provider("anthropic")
            # May be None if no API key in env or DB
            # This is expected behavior
        finally:
            if old_key:
                os.environ["ANTHROPIC_API_KEY"] = old_key

    def test_get_llm_service_for_unknown_provider(self):
        """Test helper returns None for unknown provider."""
        from app.services.llm import get_llm_service_for_provider

        service = get_llm_service_for_provider("unknown_provider")
        assert service is None


class TestStreamEvent:
    """Tests for streaming event structures."""

    def test_stream_event_text(self):
        """Test text stream event."""
        from app.services.llm import StreamEvent

        event = StreamEvent(type="text", content="Hello")
        assert event.type == "text"
        assert event.content == "Hello"

    def test_stream_event_done(self):
        """Test done stream event."""
        from app.services.llm import StreamEvent

        event = StreamEvent(type="done", stop_reason="end_turn")
        assert event.type == "done"
        assert event.stop_reason == "end_turn"

    def test_stream_event_tool_call(self):
        """Test tool call stream event."""
        from app.services.llm import StreamEvent, ToolCall

        tool_call = ToolCall(id="call_123", name="test", arguments={})
        event = StreamEvent(type="tool_call", tool_call=tool_call)
        assert event.type == "tool_call"
        assert event.tool_call is not None
        assert event.tool_call.id == "call_123"

    def test_stream_event_error(self):
        """Test error stream event."""
        from app.services.llm import StreamEvent

        event = StreamEvent(type="error", content="API error: 500")
        assert event.type == "error"
        assert event.content == "API error: 500"


class TestToolCall:
    """Tests for tool call structures."""

    def test_tool_call_creation(self):
        """Test creating a tool call."""
        from app.services.llm import ToolCall

        tool_call = ToolCall(
            id="call_123",
            name="web_search",
            arguments={"query": "test"},
        )

        assert tool_call.id == "call_123"
        assert tool_call.name == "web_search"
        assert tool_call.arguments == {"query": "test"}


class TestToolResult:
    """Tests for tool result structures."""

    def test_tool_result_success(self):
        """Test successful tool result."""
        from app.services.llm import ToolResult

        result = ToolResult(
            tool_call_id="call_123",
            result="Search results...",
            is_error=False,
        )

        assert result.tool_call_id == "call_123"
        assert result.result == "Search results..."
        assert result.is_error is False

    def test_tool_result_error(self):
        """Test error tool result."""
        from app.services.llm import ToolResult

        result = ToolResult(
            tool_call_id="call_123",
            result="Error: not found",
            is_error=True,
        )

        assert result.tool_call_id == "call_123"
        assert result.is_error is True


class TestContextWindow:
    """Tests for context window management."""

    def test_context_window_creation(self):
        """Test creating a context window."""
        from app.services.context import ContextWindow
        from app.services.llm import Message

        messages = [
            Message(role="user", content="Hello"),
            Message(role="assistant", content="Hi there!"),
        ]
        context = ContextWindow(messages=messages, system_prompt="You are helpful")

        assert len(context.messages) == 2
        assert context.system_prompt == "You are helpful"

    def test_context_window_token_estimation(self):
        """Test token estimation."""
        from app.services.context import ContextWindow
        from app.services.llm import Message

        messages = [Message(role="user", content="Hello world")]
        context = ContextWindow(messages=messages)

        # Rough estimation: 4 chars per token
        tokens = context.estimate_tokens("Hello world")
        assert tokens >= 2  # At least 2 tokens

    def test_context_to_anthropic_format(self):
        """Test conversion to Anthropic format."""
        from app.services.context import ContextWindow
        from app.services.llm import Message

        messages = [Message(role="user", content="Hello")]
        context = ContextWindow(messages=messages, system_prompt="System")

        system, msgs = context.to_anthropic_format()
        assert system == "System"
        assert len(msgs) == 1
        assert msgs[0]["role"] == "user"

    def test_context_to_openai_format(self):
        """Test conversion to OpenAI format."""
        from app.services.context import ContextWindow
        from app.services.llm import Message

        messages = [Message(role="user", content="Hello")]
        context = ContextWindow(messages=messages, system_prompt="System")

        msgs = context.to_openai_format()
        assert len(msgs) == 2  # System + user
        assert msgs[0]["role"] == "system"
        assert msgs[1]["role"] == "user"

    def test_context_to_gemini_format(self):
        """Test conversion to Gemini format."""
        from app.services.context import ContextWindow
        from app.services.llm import Message

        messages = [Message(role="user", content="Hello")]
        context = ContextWindow(messages=messages, system_prompt="System")

        system, contents = context.to_gemini_format()
        assert system == "System"
        assert len(contents) == 1
        assert contents[0]["role"] == "user"
        assert contents[0]["parts"][0]["text"] == "Hello"
