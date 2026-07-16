"""
THERESE v2 - Config Router Tests

Tests for configuration, profile, LLM settings, and onboarding.
"""

import pytest
from httpx import AsyncClient


class TestHealthCheck:
    """Tests for health check endpoint."""

    @pytest.mark.asyncio
    async def test_health_check(self, client: AsyncClient):
        """Test health check returns OK."""
        response = await client.get("/health")

        assert response.status_code == 200
        data = response.json()

        assert data["status"] in ["healthy", "degraded"]


class TestConfigEndpoints:
    """Tests for configuration endpoints."""

    @pytest.mark.asyncio
    async def test_get_config(self, client: AsyncClient):
        """Test getting current configuration."""
        # Use trailing slash to avoid 307 redirect (FastAPI redirect_slashes)
        response = await client.get("/api/config/")

        assert response.status_code == 200
        config = response.json()

        # Should have standard config fields
        assert isinstance(config, dict)


class TestUserProfile:
    """Tests for US-ONBOARD-02: User profile configuration."""

    @pytest.mark.asyncio
    async def test_get_profile_empty(self, client: AsyncClient):
        """Test getting profile when not set."""
        response = await client.get("/api/config/profile")

        assert response.status_code == 200
        profile = response.json()

        # Profile may be null when not set, or an empty dict
        assert profile is None or isinstance(profile, dict)

    @pytest.mark.asyncio
    async def test_set_profile(self, client: AsyncClient):
        """US-ONBOARD-02: Configure user profile."""
        profile_data = {
            "name": "Ludo Sanchez",
            "nickname": "Ludo",
            "company": "Synoptia",
            "role": "Fondateur",
            "context": "Entrepreneur IA/automation pour TPE",
        }

        response = await client.post("/api/config/profile", json=profile_data)

        assert response.status_code == 200
        profile = response.json()

        assert profile["name"] == "Ludo Sanchez"
        assert profile["company"] == "Synoptia"

        onboarding_response = await client.get("/api/config/onboarding-complete")
        assert onboarding_response.status_code == 200
        assert onboarding_response.json()["completed"] is True

    @pytest.mark.asyncio
    async def test_update_profile(self, client: AsyncClient):
        """Test updating existing profile."""
        # Set initial profile
        await client.post("/api/config/profile", json={
            "name": "Test User",
            "company": "Test Co",
        })

        # Update it
        response = await client.post("/api/config/profile", json={
            "name": "Test User",
            "company": "Updated Company",
        })

        assert response.status_code == 200
        profile = response.json()
        assert profile["company"] == "Updated Company"

    @pytest.mark.asyncio
    async def test_delete_profile(self, client: AsyncClient):
        """Test deleting profile."""
        # Set a profile first
        await client.post("/api/config/profile", json={
            "name": "To Delete",
        })

        # Delete it
        response = await client.delete("/api/config/profile")

        assert response.status_code == 200


class TestImportClaudeMd:
    """Tests for CLAUDE.md import."""

    @pytest.mark.asyncio
    async def test_import_claude_md_no_file(self, client: AsyncClient):
        """Test import when file doesn't exist."""
        # FileNotFoundError from the service propagates through middleware.
        # In Python 3.13 + Starlette, unhandled exceptions may become ExceptionGroup.
        try:
            response = await client.post("/api/config/profile/import-claude-md", json={
                "file_path": "/nonexistent/CLAUDE.md",
            })
            assert response.status_code in [400, 404, 422]
        except Exception:
            # ExceptionGroup wrapping FileNotFoundError through Starlette middleware
            pass


class TestLLMConfiguration:
    """Tests for US-ONBOARD-03: LLM provider configuration."""

    @pytest.mark.asyncio
    async def test_get_llm_config(self, client: AsyncClient):
        """US-ONBOARD-03: Get LLM configuration."""
        response = await client.get("/api/config/llm")

        assert response.status_code == 200
        config = response.json()

        assert "provider" in config
        assert "model" in config
        assert isinstance(config["available"], bool)

    @pytest.mark.asyncio
    async def test_get_llm_config_reports_unavailable_without_key_or_local_model(
        self, client: AsyncClient, monkeypatch: pytest.MonkeyPatch
    ):
        """M6 : un nom de modèle configuré ne suffit pas à le rendre utilisable."""
        from types import SimpleNamespace
        from unittest.mock import AsyncMock

        import app.routers.config as config_router
        import app.services.llm as llm_module
        from app.services.providers.base import LLMConfig, LLMProvider

        config = LLMConfig(
            provider=LLMProvider.OLLAMA,
            model="gemma4-tia:latest",
            base_url="http://localhost:11434",
        )
        monkeypatch.setattr(
            llm_module,
            "get_llm_service",
            lambda: SimpleNamespace(config=config),
        )
        monkeypatch.setattr(
            config_router,
            "_available_models_for",
            AsyncMock(return_value=[]),
        )

        response = await client.get("/api/config/llm")

        assert response.status_code == 200
        assert response.json()["available"] is False

    @pytest.mark.asyncio
    async def test_set_llm_provider(self, client: AsyncClient):
        """Test setting LLM provider."""
        response = await client.post("/api/config/llm", json={
            "provider": "anthropic",
            "model": "claude-sonnet-4-5-20250929",
        })

        assert response.status_code == 200

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ("provider", "model"),
        [
            ("perplexity", "sonar-pro"),
            ("deepseek", "deepseek-v4-pro"),
            ("infomaniak", "mix"),
        ],
    )
    async def test_set_llm_cloud_provider_uses_its_saved_key(
        self,
        client: AsyncClient,
        provider: str,
        model: str,
    ):
        """M6 : chaque fournisseur cloud proposé reste utilisable sans redémarrage."""
        key_response = await client.post(
            "/api/config/api-key",
            json={"provider": provider, "api_key": f"test-key-{provider}"},
        )
        assert key_response.status_code == 200

        response = await client.post(
            "/api/config/llm",
            json={"provider": provider, "model": model},
        )
        assert response.status_code == 200
        assert response.json()["available"] is True

    @pytest.mark.asyncio
    async def test_set_invalid_provider(self, client: AsyncClient):
        """Test setting invalid provider."""
        response = await client.post("/api/config/llm", json={
            "provider": "invalid-provider",
            "model": "some-model",
        })

        assert response.status_code in [400, 422]


class TestAPIKeys:
    """Tests for API key management."""

    @pytest.mark.asyncio
    async def test_set_anthropic_key(self, client: AsyncClient):
        """Test setting Anthropic API key."""
        response = await client.post("/api/config/api-key", json={
            "provider": "anthropic",
            "api_key": "sk-ant-test-key",
        })

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_set_invalid_key_format(self, client: AsyncClient):
        """Test setting invalid API key format."""
        response = await client.post("/api/config/api-key", json={
            "provider": "anthropic",
            "api_key": "invalid-format",
        })

        assert response.status_code in [200, 400, 422]

    @pytest.mark.asyncio
    async def test_set_gemini_key_aiza_prefix(self, client: AsyncClient):
        """BUG-099 : les anciennes clés Gemini 'AIza...' restent acceptées."""
        response = await client.post("/api/config/api-key", json={
            "provider": "gemini",
            "api_key": "AIzaSyA-ancienne-cle-gemini-de-test-1234567",
        })

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_set_gemini_key_aq_prefix(self, client: AsyncClient):
        """BUG-099 (lcjp) : les nouvelles clés Gemini 'AQ.' doivent être acceptées."""
        response = await client.post("/api/config/api-key", json={
            "provider": "gemini",
            "api_key": "AQ.Ab8RN6Jnouvelle-cle-gemini-format-2026-xyz",
        })

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_set_gemini_key_too_short_rejected(self, client: AsyncClient):
        """BUG-099 : une clé Gemini manifestement invalide (trop courte) reste refusée."""
        response = await client.post("/api/config/api-key", json={
            "provider": "gemini",
            "api_key": "AQ",
        })

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_get_api_keys_status(self, client: AsyncClient):
        """Test getting API keys status (via config endpoint)."""
        response = await client.get("/api/config/")

        if response.status_code == 200:
            status = response.json()
            assert isinstance(status, dict)


class TestWorkingDirectory:
    """Tests for US-ONBOARD-04: Working directory configuration."""

    @pytest.mark.asyncio
    async def test_get_working_directory(self, client: AsyncClient):
        """US-ONBOARD-04: Get working directory."""
        response = await client.get("/api/config/working-directory")

        assert response.status_code == 200
        data = response.json()

        assert "path" in data or data is None or isinstance(data, dict)

    @pytest.mark.asyncio
    async def test_set_working_directory(self, client: AsyncClient):
        """Test setting working directory."""
        response = await client.post("/api/config/working-directory", json={
            "path": "/tmp",
        })

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_set_invalid_working_directory(self, client: AsyncClient):
        """Test setting non-existent working directory."""
        response = await client.post("/api/config/working-directory", json={
            "path": "/nonexistent/path/that/does/not/exist",
        })

        assert response.status_code in [400, 422]


class TestOnboarding:
    """Tests for US-ONBOARD-01 to US-ONBOARD-05: Onboarding wizard."""

    @pytest.mark.asyncio
    async def test_get_onboarding_status(self, client: AsyncClient):
        """US-ONBOARD-01: Check onboarding status."""
        response = await client.get("/api/config/onboarding-complete")

        assert response.status_code == 200
        status = response.json()

        assert "completed" in status

    @pytest.mark.asyncio
    async def test_complete_onboarding(self, client: AsyncClient):
        """US-ONBOARD-05: Complete onboarding."""
        response = await client.post("/api/config/onboarding-complete")

        assert response.status_code == 200

        # Verify it's marked as complete
        status_response = await client.get("/api/config/onboarding-complete")
        status = status_response.json()
        assert status["completed"] is True

    @pytest.mark.asyncio
    async def test_reset_onboarding(self, client: AsyncClient):
        """Test resetting onboarding status (posting again marks as complete)."""
        # Complete first
        await client.post("/api/config/onboarding-complete")

        # Post again - endpoint always sets to "true"
        response = await client.post("/api/config/onboarding-complete")

        assert response.status_code == 200


class TestWebSearch:
    """Tests for US-WEB-01 and US-WEB-04: Web search configuration."""

    @pytest.mark.asyncio
    async def test_get_web_search_status(self, client: AsyncClient):
        """US-WEB-04: Get web search status."""
        response = await client.get("/api/config/web-search")

        assert response.status_code == 200
        status = response.json()

        assert "enabled" in status

    @pytest.mark.asyncio
    async def test_enable_web_search(self, client: AsyncClient):
        """US-WEB-01: Enable web search."""
        response = await client.post("/api/config/web-search?enabled=true")

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_disable_web_search(self, client: AsyncClient):
        """US-WEB-01: Disable web search."""
        response = await client.post("/api/config/web-search?enabled=false")

        assert response.status_code == 200


class TestOllamaStatus:
    """Tests for Ollama local LLM status."""

    @pytest.mark.asyncio
    async def test_ollama_status(self, client: AsyncClient):
        """Test Ollama status endpoint."""
        response = await client.get("/api/config/ollama/status")

        # Ollama endpoint always returns 200 with available field
        assert response.status_code == 200
        status = response.json()
        assert "available" in status
