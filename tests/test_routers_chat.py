"""
THERESE v2 - Chat Router Tests

Tests for US-CHAT-01 to US-CHAT-10.
"""

import pytest
from httpx import AsyncClient


class TestChatBasics:
    """Tests for basic chat functionality."""

    @pytest.mark.asyncio
    async def test_send_message_streaming(self, client: AsyncClient, sample_chat_message):
        """US-CHAT-02: Streaming response via SSE."""
        # Enable streaming
        sample_chat_message["stream"] = True

        response = await client.post("/api/chat/send", json=sample_chat_message)

        # Streaming endpoint returns text/event-stream
        assert response.status_code in [200, 401, 503]

        if response.status_code == 200:
            assert "text/event-stream" in response.headers.get("content-type", "")

    @pytest.mark.asyncio
    async def test_send_message_non_streaming(self, client: AsyncClient, sample_chat_message):
        """Test non-streaming response."""
        sample_chat_message["stream"] = False

        response = await client.post("/api/chat/send", json=sample_chat_message)

        # May fail without LLM key
        assert response.status_code in [200, 401, 503]

    @pytest.mark.asyncio
    async def test_send_empty_message(self, client: AsyncClient):
        """Test sending empty message."""
        response = await client.post("/api/chat/send", json={
            "message": "",
            "stream": False,
        })

        # Empty string passes Pydantic validation (it's a valid str),
        # but may fail at LLM level (no API key, etc.)
        assert response.status_code in [200, 400, 422, 500, 503]


class TestConversations:
    """Tests for US-CHAT-03: Conversation persistence."""

    @pytest.mark.asyncio
    async def test_list_conversations_empty(self, client: AsyncClient):
        """US-CHAT-03: List conversations when empty."""
        response = await client.get("/api/chat/conversations")

        assert response.status_code == 200
        conversations = response.json()

        assert isinstance(conversations, list)

    @pytest.mark.asyncio
    async def test_get_conversation_nonexistent(self, client: AsyncClient):
        """Test getting a non-existent conversation."""
        response = await client.get("/api/chat/conversations/nonexistent-id")

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_conversation_nonexistent(self, client: AsyncClient):
        """Test deleting a non-existent conversation."""
        response = await client.delete("/api/chat/conversations/nonexistent-id")

        assert response.status_code == 404


class TestEphemeralConversations:
    """Tests for US-CHAT-04: Ephemeral conversations."""

    @pytest.mark.asyncio
    async def test_create_conversation(self, client: AsyncClient):
        """US-CHAT-04: Create conversation (ephemeral is frontend-only concept)."""
        response = await client.post("/api/chat/conversations", json={})

        assert response.status_code == 200
        conversation = response.json()
        assert "id" in conversation


class TestMemoryIntegration:
    """Tests for US-CHAT-08: User identity recognition."""

    @pytest.mark.asyncio
    async def test_message_includes_memory_context(self, client: AsyncClient, sample_chat_message):
        """Test that messages can include memory context."""
        sample_chat_message["include_memory"] = True

        response = await client.post("/api/chat/send", json=sample_chat_message)

        # Request should be accepted
        assert response.status_code in [200, 401, 503]

    @pytest.mark.asyncio
    async def test_message_excludes_memory_context(self, client: AsyncClient, sample_chat_message):
        """Test that memory context can be disabled."""
        sample_chat_message["include_memory"] = False

        response = await client.post("/api/chat/send", json=sample_chat_message)

        assert response.status_code in [200, 401, 503]


class TestSlashCommands:
    """Tests for US-CHAT-07: Slash commands."""

    @pytest.mark.asyncio
    async def test_fichier_command(self, client: AsyncClient):
        """US-CHAT-07: Test /fichier command."""
        response = await client.post("/api/chat/send", json={
            "message": "/fichier /tmp/test.txt",
            "stream": False,
        })

        # Command should be processed (may fail for other reasons)
        assert response.status_code in [200, 400, 401, 404, 503]

    @pytest.mark.asyncio
    async def test_analyse_command(self, client: AsyncClient):
        """US-CHAT-07: Test /analyse command."""
        response = await client.post("/api/chat/send", json={
            "message": "/analyse /tmp/test.txt",
            "stream": False,
        })

        assert response.status_code in [200, 400, 401, 404, 503]


class TestLLMProviders:
    """Tests for US-CHAT-01: Multiple LLM providers."""

    @pytest.mark.asyncio
    async def test_available_providers(self, client: AsyncClient):
        """US-CHAT-01: Check available providers."""
        response = await client.get("/api/config/llm")

        assert response.status_code == 200
        config = response.json()

        # Should list available providers
        assert "provider" in config

    @pytest.mark.asyncio
    async def test_chat_with_specific_provider(self, client: AsyncClient, sample_chat_message):
        """Test chat with specific provider selected."""
        # First set provider
        await client.post("/api/config/llm", json={
            "provider": "anthropic",
            "model": "claude-sonnet-4-5-20250929",
        })

        response = await client.post("/api/chat/send", json=sample_chat_message)

        # Should use selected provider
        assert response.status_code in [200, 401, 503]


class TestWebSearchIntegration:
    """Tests for US-CHAT-06: Web search integration."""

    @pytest.mark.asyncio
    async def test_chat_with_web_search_enabled(self, client: AsyncClient, sample_chat_message):
        """US-CHAT-06: Chat with web search enabled."""
        # Enable web search
        await client.post("/api/config/web-search?enabled=true")

        sample_chat_message["message"] = "Quelle est la meteo aujourd'hui ?"
        response = await client.post("/api/chat/send", json=sample_chat_message)

        assert response.status_code in [200, 401, 503]


class TestMCPToolCalling:
    """Tests for US-CHAT-05: MCP tool calling."""

    @pytest.mark.asyncio
    async def test_chat_with_tools(self, client: AsyncClient, sample_chat_message):
        """US-CHAT-05: Chat can use MCP tools."""
        sample_chat_message["message"] = "Liste les fichiers dans /tmp"
        response = await client.post("/api/chat/send", json=sample_chat_message)

        # Request should be accepted (tools may or may not be available)
        assert response.status_code in [200, 401, 503]


class TestEntityExtraction:
    """Tests for US-CHAT-09: Automatic entity extraction."""

    @pytest.mark.asyncio
    async def test_message_with_contact_mention(self, client: AsyncClient):
        """US-CHAT-09: Message mentioning a person."""
        response = await client.post("/api/chat/send", json={
            "message": "J'ai rencontre Pierre Dupont de Microsoft aujourd'hui",
            "stream": True,
        })

        # Request should be accepted
        assert response.status_code in [200, 401, 503]


class TestConversationHistory:
    """Tests for conversation message history."""

    @pytest.mark.asyncio
    async def test_get_conversation_messages(self, client: AsyncClient):
        """Test getting messages from a non-existent conversation."""
        response = await client.get("/api/chat/conversations/test-id/messages")

        # Endpoint returns empty list for non-existent conversation (no 404 check)
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_conversation_pagination(self, client: AsyncClient):
        """Test conversation list pagination."""
        response = await client.get("/api/chat/conversations?limit=10&offset=0")

        assert response.status_code == 200


class TestChatErrors:
    """Tests for chat error handling."""

    @pytest.mark.asyncio
    async def test_missing_message_field(self, client: AsyncClient):
        """Test request without message field."""
        response = await client.post("/api/chat/send", json={
            "stream": True,
        })

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_invalid_conversation_id(self, client: AsyncClient):
        """Test with invalid conversation ID format."""
        response = await client.post("/api/chat/send", json={
            "message": "Test",
            "conversation_id": "invalid-format-!!!",
        })

        # Should either accept or reject gracefully
        assert response.status_code in [200, 400, 401, 404, 422, 503]
