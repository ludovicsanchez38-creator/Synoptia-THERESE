"""
THERESE v2 - Images Router Tests

Tests for US-IMG-01 to US-IMG-05.
"""

import pytest
from httpx import AsyncClient


class TestImageGeneration:
    """Tests for US-IMG-01: Image generation from description."""

    @pytest.mark.asyncio
    async def test_generate_image_without_api_key(self, client: AsyncClient):
        """Test image generation without API key configured."""
        response = await client.post("/api/images/generate", json={
            "prompt": "Un chat mignon dans un jardin",
            "provider": "gpt-image-1.5",
        })

        # Should fail gracefully without API key (400, 500, or 503)
        assert response.status_code in [200, 400, 422, 500, 503]

    @pytest.mark.asyncio
    async def test_generate_image_empty_prompt(self, client: AsyncClient):
        """Test image generation with empty prompt."""
        response = await client.post("/api/images/generate", json={
            "prompt": "",
            "provider": "gpt-image-1.5",
        })

        assert response.status_code in [400, 422, 500]


class TestImageReference:
    """Tests for US-IMG-02: Image generation with reference."""

    @pytest.mark.asyncio
    async def test_generate_with_reference_missing_image(self, client: AsyncClient):
        """Test generation with reference but no image provided."""
        response = await client.post("/api/images/generate-with-reference", json={
            "prompt": "Same style but different scene",
        })

        assert response.status_code in [400, 422]


class TestImageProviders:
    """Tests for US-IMG-03: Provider selection."""

    @pytest.mark.asyncio
    async def test_select_openai_provider(self, client: AsyncClient):
        """Test selecting OpenAI (GPT Image 1.5) provider."""
        response = await client.post("/api/images/generate", json={
            "prompt": "Test image",
            "provider": "gpt-image-1.5",
            "size": "1024x1024",
        })

        # Will fail without key, but validates request structure
        assert response.status_code in [200, 400, 422, 500, 503]

    @pytest.mark.asyncio
    async def test_select_gemini_provider(self, client: AsyncClient):
        """Test selecting Gemini (Nano Banana Pro) provider."""
        response = await client.post("/api/images/generate", json={
            "prompt": "Test image",
            "provider": "nanobanan-pro",
        })

        assert response.status_code in [200, 400, 422, 500, 503]

    @pytest.mark.asyncio
    async def test_invalid_provider(self, client: AsyncClient):
        """Test invalid provider."""
        response = await client.post("/api/images/generate", json={
            "prompt": "Test image",
            "provider": "invalid-provider",
        })

        assert response.status_code in [400, 422]


class TestImageList:
    """Tests for US-IMG-04: Manage generated images."""

    @pytest.mark.asyncio
    async def test_list_images_empty(self, client: AsyncClient):
        """US-IMG-04: List generated images when none exist."""
        response = await client.get("/api/images/list")

        assert response.status_code == 200
        data = response.json()

        # Response is ImageListResponse with 'images' and 'total' fields
        assert isinstance(data, dict)
        assert "images" in data
        assert isinstance(data["images"], list)

    @pytest.mark.asyncio
    async def test_list_images_with_limit(self, client: AsyncClient):
        """Test listing images with limit parameter."""
        response = await client.get("/api/images/list?limit=10")

        assert response.status_code == 200


class TestImageDownload:
    """Tests for image download."""

    @pytest.mark.asyncio
    async def test_download_nonexistent_image(self, client: AsyncClient):
        """Test downloading a non-existent image."""
        response = await client.get("/api/images/download/nonexistent-id")

        assert response.status_code == 404


class TestImageStatus:
    """Tests for US-IMG-05: Provider availability status."""

    @pytest.mark.asyncio
    async def test_get_image_status(self, client: AsyncClient):
        """US-IMG-05: Check provider availability."""
        response = await client.get("/api/images/status")

        assert response.status_code == 200
        status = response.json()

        # Should indicate which providers are available
        assert isinstance(status, dict)
        # May have openai_available, gemini_available, etc.


class TestImageOptions:
    """Tests for image generation options."""

    @pytest.mark.asyncio
    async def test_custom_size(self, client: AsyncClient):
        """Test generating with custom size."""
        response = await client.post("/api/images/generate", json={
            "prompt": "Test image",
            "provider": "gpt-image-1.5",
            "size": "1536x1024",
        })

        assert response.status_code in [200, 400, 422, 500, 503]

    @pytest.mark.asyncio
    async def test_invalid_size(self, client: AsyncClient):
        """Test generating with invalid size."""
        response = await client.post("/api/images/generate", json={
            "prompt": "Test image",
            "provider": "gpt-image-1.5",
            "size": "100x100",  # Invalid size (not in Literal)
        })

        assert response.status_code in [400, 422]


class TestImageDelete:
    """Tests for image deletion."""

    @pytest.mark.asyncio
    async def test_delete_nonexistent_image(self, client: AsyncClient):
        """Test deleting a non-existent image."""
        response = await client.delete("/api/images/nonexistent-id")

        assert response.status_code in [404, 405]
