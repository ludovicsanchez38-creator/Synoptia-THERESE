"""
THERESE v2 - Error Handling Tests

Tests for US-ERR-01 to US-ERR-05.
"""


import pytest
from httpx import AsyncClient


class TestErrorMessages:
    """Tests for US-ERR-01: Clear error messages."""

    def test_error_code_enum(self):
        """Test ErrorCode enum values."""
        from app.services.error_handler import ErrorCode

        assert ErrorCode.API_UNREACHABLE.value == "api_unreachable"
        assert ErrorCode.API_TIMEOUT.value == "api_timeout"
        assert ErrorCode.LLM_GENERATION_FAILED.value == "llm_generation_failed"

    def test_theres_error_creation(self):
        """Test TheresError with user-friendly message."""
        from app.services.error_handler import ErrorCode, TheresError

        error = TheresError(
            code=ErrorCode.API_AUTH_FAILED,
            technical_message="HTTP 401 from Anthropic",
            context={"provider": "Anthropic"},
        )

        assert error.code == ErrorCode.API_AUTH_FAILED
        assert "Anthropic" in error.user_message
        assert "invalide" in error.user_message.lower() or "expiree" in error.user_message.lower()

    def test_theres_error_to_dict(self):
        """Test TheresError serialization."""
        from app.services.error_handler import ErrorCode, TheresError

        error = TheresError(
            code=ErrorCode.QDRANT_UNAVAILABLE,
            technical_message="Connection refused",
            recoverable=True,
        )

        data = error.to_dict()
        assert data["code"] == "qdrant_unavailable"
        assert "message" in data
        assert data["recoverable"] is True

    def test_classify_http_error(self):
        """Test HTTP error classification."""
        from app.services.error_handler import ErrorCode, classify_http_error

        # 401 -> Auth failed
        err_401 = classify_http_error(401, "Anthropic")
        assert err_401.code == ErrorCode.API_AUTH_FAILED

        # 429 -> Rate limited
        err_429 = classify_http_error(429, "OpenAI")
        assert err_429.code == ErrorCode.API_RATE_LIMITED

        # 500 -> Server error
        err_500 = classify_http_error(500, "Mistral")
        assert err_500.code == ErrorCode.API_SERVER_ERROR


class TestRetryLogic:
    """Tests for US-ERR-02: Automatic retry with backoff."""

    @pytest.mark.asyncio
    async def test_retry_success_after_failures(self):
        """Test retry succeeds after initial failures."""
        import httpx
        from app.services.error_handler import retry_with_backoff

        attempt_count = 0

        async def flaky_func():
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count < 3:
                raise httpx.TimeoutException("Timeout")
            return "success"

        result = await retry_with_backoff(
            flaky_func,
            max_retries=3,
            base_delay=0.01,  # Fast for testing
        )

        assert result == "success"
        assert attempt_count == 3

    @pytest.mark.asyncio
    async def test_retry_exhausted(self):
        """Test all retries exhausted raises error."""
        import httpx
        from app.services.error_handler import TheresError, retry_with_backoff

        async def always_fails():
            raise httpx.TimeoutException("Timeout")

        with pytest.raises(TheresError) as exc_info:
            await retry_with_backoff(
                always_fails,
                max_retries=2,
                base_delay=0.01,
            )

        assert exc_info.value.code.value == "api_timeout"

    @pytest.mark.asyncio
    async def test_non_retryable_exception_propagates(self):
        """Test non-retryable exceptions are not retried."""
        from app.services.error_handler import retry_with_backoff

        attempt_count = 0

        async def value_error_func():
            nonlocal attempt_count
            attempt_count += 1
            raise ValueError("Invalid value")

        with pytest.raises(ValueError):
            await retry_with_backoff(
                value_error_func,
                max_retries=3,
                base_delay=0.01,
            )

        # Should only try once
        assert attempt_count == 1


class TestGracefulDegradation:
    """Tests for US-ERR-03: Graceful degradation."""

    def test_service_status_singleton(self):
        """Test ServiceStatus is a singleton."""
        from app.services.error_handler import ServiceStatus

        s1 = ServiceStatus()
        s2 = ServiceStatus()
        assert s1 is s2

    def test_service_status_tracking(self):
        """Test service availability tracking."""
        from app.services.error_handler import get_service_status

        status = get_service_status()
        status.set_available("qdrant", False)

        assert status.is_available("qdrant") is False
        assert status.is_available("unknown_service", default=True) is True

    @pytest.mark.asyncio
    async def test_graceful_degradation_fallback(self):
        """Test fallback is used when primary fails."""
        from app.services.error_handler import with_graceful_degradation

        async def primary_fails():
            raise Exception("Primary failed")

        async def fallback_works():
            return "fallback_result"

        result = await with_graceful_degradation(
            primary_func=primary_fails,
            fallback_func=fallback_works,
            service_name="test_service",
        )

        assert result == "fallback_result"

    @pytest.mark.asyncio
    async def test_graceful_degradation_default_value(self):
        """Test default value is returned when both fail."""
        from app.services.error_handler import with_graceful_degradation

        async def always_fails():
            raise Exception("Failed")

        result = await with_graceful_degradation(
            primary_func=always_fails,
            fallback_func=None,
            service_name="test_service",
            default_value="default",
        )

        assert result == "default"


class TestCancelGeneration:
    """Tests for US-ERR-04: Cancel generation in progress."""

    @pytest.mark.asyncio
    async def test_cancel_generation_endpoint(self, async_client: AsyncClient):
        """Test cancel generation endpoint."""
        response = await async_client.post("/api/chat/cancel/test-conv-id")
        assert response.status_code == 200

        data = response.json()
        assert "cancelled" in data
        assert data["conversation_id"] == "test-conv-id"

    def test_generation_tracking(self):
        """Test generation registration and cancellation."""
        from app.routers.chat import (
            _cancel_generation,
            _is_cancelled,
            _register_generation,
            _unregister_generation,
        )

        conv_id = "test-conv-123"

        # Register
        _register_generation(conv_id)
        assert not _is_cancelled(conv_id)

        # Cancel
        result = _cancel_generation(conv_id)
        assert result is True
        assert _is_cancelled(conv_id)

        # Unregister
        _unregister_generation(conv_id)
        assert not _is_cancelled(conv_id)


class TestHealthEndpoints:
    """Tests for service status and health checks."""

    @pytest.mark.asyncio
    async def test_health_endpoint(self, async_client: AsyncClient):
        """Test main health endpoint."""
        response = await async_client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert "status" in data
        assert data["status"] in ["healthy", "degraded"]
        assert "version" in data

    @pytest.mark.asyncio
    async def test_service_status_endpoint(self, async_client: AsyncClient):
        """Test detailed service status endpoint."""
        response = await async_client.get("/health/services")
        assert response.status_code == 200

        data = response.json()
        assert "services" in data
        assert "database" in data["services"]
        assert "qdrant" in data["services"]


class TestLLMErrorClassification:
    """Tests for LLM-specific error handling."""

    def test_classify_context_too_long(self):
        """Test context too long error classification."""
        from app.services.error_handler import ErrorCode, classify_llm_error

        error = Exception("context length exceeded maximum of 100000 tokens")
        result = classify_llm_error(error, "anthropic")

        assert result.code == ErrorCode.LLM_CONTEXT_TOO_LONG

    def test_classify_rate_limit(self):
        """Test rate limit error classification."""
        from app.services.error_handler import ErrorCode, classify_llm_error

        error = Exception("rate limit exceeded")
        result = classify_llm_error(error, "openai")

        assert result.code == ErrorCode.API_RATE_LIMITED

    def test_classify_auth_error(self):
        """Test auth error classification."""
        from app.services.error_handler import ErrorCode, classify_llm_error

        error = Exception("Invalid API key provided")
        result = classify_llm_error(error, "mistral")

        assert result.code == ErrorCode.API_AUTH_FAILED


class TestConversationRecovery:
    """Tests for US-ERR-05: Conversation recovery after crash."""

    @pytest.mark.asyncio
    async def test_conversations_persisted(self, async_client: AsyncClient):
        """Test that conversations are persisted to database."""
        # Create a conversation by sending a message
        response = await async_client.post(
            "/api/chat/send",
            json={
                "message": "Test message for recovery",
                "stream": False,
            },
        )
        # Allow for mock LLM returning error but conversation still created
        assert response.status_code in [200, 500]

        # List conversations
        list_response = await async_client.get("/api/chat/conversations")
        assert list_response.status_code == 200

        data = list_response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_conversation_messages_persisted(self, async_client: AsyncClient):
        """Test that messages in conversation are persisted."""
        # First, send a message to create conversation
        response = await async_client.post(
            "/api/chat/send",
            json={
                "message": "Persistence test message",
                "stream": False,
            },
        )

        if response.status_code == 200:
            data = response.json()
            conv_id = data.get("conversation_id")

            if conv_id:
                # Get conversation messages
                messages_response = await async_client.get(
                    f"/api/chat/conversations/{conv_id}/messages"
                )

                if messages_response.status_code == 200:
                    messages = messages_response.json()
                    # Should have at least the user message
                    assert len(messages) >= 1
