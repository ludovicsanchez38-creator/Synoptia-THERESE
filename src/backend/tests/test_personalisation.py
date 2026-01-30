"""
THERESE v2 - Personalisation Tests

Tests for US-PERS-01 to US-PERS-05.
"""

import pytest
from httpx import AsyncClient


class TestPromptTemplates:
    """Tests for US-PERS-02: Custom prompt templates."""

    @pytest.mark.asyncio
    async def test_list_templates_empty(self, async_client: AsyncClient):
        """Test listing templates when none exist."""
        response = await async_client.get("/api/personalisation/templates")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    @pytest.mark.asyncio
    async def test_create_template(self, async_client: AsyncClient):
        """Test creating a prompt template."""
        template_data = {
            "name": "Email professionnel",
            "prompt": "Redige un email professionnel pour {destinataire} concernant {sujet}",
            "category": "email",
            "icon": "mail",
        }

        response = await async_client.post(
            "/api/personalisation/templates",
            json=template_data,
        )
        assert response.status_code == 200

        data = response.json()
        assert data["name"] == template_data["name"]
        assert data["prompt"] == template_data["prompt"]
        assert data["category"] == template_data["category"]
        assert "id" in data

    @pytest.mark.asyncio
    async def test_get_template(self, async_client: AsyncClient):
        """Test getting a specific template."""
        # Create a template first
        create_response = await async_client.post(
            "/api/personalisation/templates",
            json={
                "name": "Test Template",
                "prompt": "Test prompt",
                "category": "test",
            },
        )
        template_id = create_response.json()["id"]

        # Get the template
        response = await async_client.get(
            f"/api/personalisation/templates/{template_id}"
        )
        assert response.status_code == 200
        assert response.json()["id"] == template_id

    @pytest.mark.asyncio
    async def test_update_template(self, async_client: AsyncClient):
        """Test updating a template."""
        # Create a template first
        create_response = await async_client.post(
            "/api/personalisation/templates",
            json={
                "name": "Original Name",
                "prompt": "Original prompt",
                "category": "test",
            },
        )
        template_id = create_response.json()["id"]

        # Update the template
        response = await async_client.put(
            f"/api/personalisation/templates/{template_id}",
            json={"name": "Updated Name"},
        )
        assert response.status_code == 200
        assert response.json()["name"] == "Updated Name"

    @pytest.mark.asyncio
    async def test_delete_template(self, async_client: AsyncClient):
        """Test deleting a template."""
        # Create a template first
        create_response = await async_client.post(
            "/api/personalisation/templates",
            json={
                "name": "To Delete",
                "prompt": "Delete me",
                "category": "test",
            },
        )
        template_id = create_response.json()["id"]

        # Delete the template
        response = await async_client.delete(
            f"/api/personalisation/templates/{template_id}"
        )
        assert response.status_code == 200
        assert response.json()["deleted"] is True

        # Verify it's deleted
        get_response = await async_client.get(
            f"/api/personalisation/templates/{template_id}"
        )
        assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_list_templates_by_category(self, async_client: AsyncClient):
        """Test filtering templates by category."""
        # Create templates in different categories
        await async_client.post(
            "/api/personalisation/templates",
            json={"name": "Email 1", "prompt": "...", "category": "email"},
        )
        await async_client.post(
            "/api/personalisation/templates",
            json={"name": "Doc 1", "prompt": "...", "category": "document"},
        )

        # Filter by category
        response = await async_client.get(
            "/api/personalisation/templates?category=email"
        )
        assert response.status_code == 200

        templates = response.json()
        for t in templates:
            assert t["category"] == "email"


class TestLLMBehavior:
    """Tests for US-PERS-04: LLM behavior customization."""

    @pytest.mark.asyncio
    async def test_get_llm_behavior_defaults(self, async_client: AsyncClient):
        """Test getting default LLM behavior."""
        response = await async_client.get("/api/personalisation/llm-behavior")
        assert response.status_code == 200

        data = response.json()
        assert "custom_system_prompt" in data
        assert "response_style" in data
        assert "language" in data
        assert data["use_custom_system_prompt"] is False

    @pytest.mark.asyncio
    async def test_set_llm_behavior(self, async_client: AsyncClient):
        """Test setting LLM behavior."""
        settings = {
            "custom_system_prompt": "Tu es un expert en marketing.",
            "use_custom_system_prompt": True,
            "response_style": "concise",
            "language": "french",
            "include_memory_context": True,
            "max_history_messages": 30,
        }

        response = await async_client.post(
            "/api/personalisation/llm-behavior",
            json=settings,
        )
        assert response.status_code == 200

        data = response.json()
        assert data["custom_system_prompt"] == settings["custom_system_prompt"]
        assert data["use_custom_system_prompt"] is True
        assert data["response_style"] == "concise"

    @pytest.mark.asyncio
    async def test_llm_behavior_persists(self, async_client: AsyncClient):
        """Test that LLM behavior settings persist."""
        # Set custom settings
        await async_client.post(
            "/api/personalisation/llm-behavior",
            json={
                "custom_system_prompt": "Test prompt",
                "use_custom_system_prompt": True,
                "response_style": "creative",
                "language": "english",
                "include_memory_context": False,
                "max_history_messages": 20,
            },
        )

        # Retrieve and verify
        response = await async_client.get("/api/personalisation/llm-behavior")
        data = response.json()
        assert data["custom_system_prompt"] == "Test prompt"
        assert data["response_style"] == "creative"


class TestFeatureVisibility:
    """Tests for US-PERS-05: Feature visibility."""

    @pytest.mark.asyncio
    async def test_get_feature_visibility_defaults(self, async_client: AsyncClient):
        """Test getting default feature visibility."""
        response = await async_client.get("/api/personalisation/features")
        assert response.status_code == 200

        data = response.json()
        # All features should be visible by default
        assert data["show_board"] is True
        assert data["show_calculators"] is True
        assert data["show_image_generation"] is True
        assert data["show_voice_input"] is True
        assert data["show_file_browser"] is True
        assert data["show_mcp_tools"] is True
        assert data["show_guided_prompts"] is True

    @pytest.mark.asyncio
    async def test_set_feature_visibility(self, async_client: AsyncClient):
        """Test setting feature visibility."""
        settings = {
            "show_board": True,
            "show_calculators": False,
            "show_image_generation": False,
            "show_voice_input": True,
            "show_file_browser": True,
            "show_mcp_tools": False,
            "show_guided_prompts": True,
            "show_entity_suggestions": False,
        }

        response = await async_client.post(
            "/api/personalisation/features",
            json=settings,
        )
        assert response.status_code == 200

        data = response.json()
        assert data["show_calculators"] is False
        assert data["show_image_generation"] is False
        assert data["show_mcp_tools"] is False

    @pytest.mark.asyncio
    async def test_feature_visibility_persists(self, async_client: AsyncClient):
        """Test that feature visibility settings persist."""
        # Set custom visibility
        await async_client.post(
            "/api/personalisation/features",
            json={
                "show_board": False,
                "show_calculators": True,
                "show_image_generation": True,
                "show_voice_input": False,
                "show_file_browser": True,
                "show_mcp_tools": True,
                "show_guided_prompts": False,
                "show_entity_suggestions": True,
            },
        )

        # Retrieve and verify
        response = await async_client.get("/api/personalisation/features")
        data = response.json()
        assert data["show_board"] is False
        assert data["show_voice_input"] is False
        assert data["show_guided_prompts"] is False


class TestPersonalisationStatus:
    """Tests for combined personalisation status."""

    @pytest.mark.asyncio
    async def test_get_status(self, async_client: AsyncClient):
        """Test getting combined personalisation status."""
        response = await async_client.get("/api/personalisation/status")
        assert response.status_code == 200

        data = response.json()
        assert "templates_count" in data
        assert "templates_by_category" in data
        assert "llm_behavior" in data
        assert "feature_visibility" in data
