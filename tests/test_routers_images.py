"""
THERESE v2 - Images Router Tests

Tests for US-IMG-01 to US-IMG-05.
"""
from unittest.mock import AsyncMock

import pytest
from httpx import AsyncClient

# US-018 : neutraliser les clés env - sans ça, ces tests partaient en VRAI
# appel API de génération d'image sur les machines configurées (résultat
# dépendant de l'environnement, 500 au lieu des 400/422 déterministes).
_IMAGE_ENV_KEYS = (
    "OPENAI_API_KEY", "OPENAI_IMAGE_API_KEY", "GEMINI_API_KEY",
    "GEMINI_IMAGE_API_KEY", "GOOGLE_API_KEY",
)


@pytest.fixture(autouse=True)
def _no_image_api_keys(monkeypatch):
    for key in _IMAGE_ENV_KEYS:
        monkeypatch.delenv(key, raising=False)


@pytest.fixture
def adaptateurs_images_simules(monkeypatch, tmp_path):
    from app.services.image_generator import GeneratedImage, ImageGeneratorService, ImageProvider

    def adaptateur(fournisseur):
        return AsyncMock(return_value=GeneratedImage(
            id="image-test",
            provider=fournisseur.value,
            file_path=tmp_path / "image-test.png",
            file_name="image-test.png",
            file_size=42,
            mime_type="image/png",
            created_at="2026-11-25T00:00:00Z",
            prompt="Image de contrôle",
        ))

    openai = adaptateur(ImageProvider.OPENAI)
    gemini = adaptateur(ImageProvider.GEMINI)
    monkeypatch.setattr(ImageGeneratorService, "_generate_openai", openai)
    monkeypatch.setattr(ImageGeneratorService, "_generate_gemini", gemini)
    monkeypatch.setattr(ImageGeneratorService, "_generate_fal", AsyncMock(
        side_effect=AssertionError("Un adaptateur imprévu a été choisi."),
    ))
    return openai, gemini


class TestImageGeneration:
    """Tests for US-IMG-01: Image generation from description."""

    @pytest.mark.asyncio
    async def test_generate_image_without_api_key(self, client: AsyncClient):
        """Test image generation without API key configured."""
        from app.services.consentements import enregistrer_accord
        enregistrer_accord('images', 'gpt-image-2', True, '3', [])
        response = await client.post("/api/images/generate", json={
            "prompt": "Un chat mignon dans un jardin",
            "provider": "gpt-image-2",
        })

        # Sans clé API : refus PROPRE (ValueError -> 400), jamais un 500
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_generate_image_empty_prompt(self, client: AsyncClient):
        """Test image generation with empty prompt."""
        response = await client.post("/api/images/generate", json={
            "prompt": "",
            "provider": "gpt-image-2",
        })

        assert response.status_code in [400, 422]


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
    async def test_select_openai_provider(self, client: AsyncClient, adaptateurs_images_simules):
        from app.services.consentements import enregistrer_accord
        from app.services.image_generator import ImageConfig, ImageProvider

        openai, gemini = adaptateurs_images_simules
        enregistrer_accord("images", "gpt-image-2", True, "3", [])
        response = await client.post("/api/images/generate", json={
            "prompt": "Image de contrôle",
            "provider": "gpt-image-2",
            "size": "1536x1024",
        })

        assert response.status_code == 200, response.text
        assert response.json()["provider"] == "gpt-image-2"
        assert response.json()["download_url"] == "/api/images/download/image-test"
        openai.assert_awaited_once_with(
            "Image de contrôle", ImageConfig(provider=ImageProvider.OPENAI, size="1536x1024"), None,
        )
        gemini.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_select_gemini_provider(self, client: AsyncClient, adaptateurs_images_simules):
        from app.services.consentements import enregistrer_accord
        from app.services.image_generator import ImageConfig, ImageProvider

        openai, gemini = adaptateurs_images_simules
        enregistrer_accord("images", "nanobanan-pro", True, "3", [])
        response = await client.post("/api/images/generate", json={
            "prompt": "Image de contrôle",
            "provider": "nanobanan-pro",
            "aspect_ratio": "16:9",
            "image_size": "4K",
        })

        assert response.status_code == 200, response.text
        assert response.json()["provider"] == "nanobanan-pro"
        assert response.json()["mime_type"] == "image/png"
        gemini.assert_awaited_once_with(
            "Image de contrôle", ImageConfig(provider=ImageProvider.GEMINI, aspect_ratio="16:9", image_size="4K"), None,
        )
        openai.assert_not_awaited()

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
        from app.services.consentements import enregistrer_accord
        enregistrer_accord('images', 'gpt-image-2', True, '3', [])
        response = await client.post("/api/images/generate", json={
            "prompt": "Test image",
            "provider": "gpt-image-2",
            "size": "1536x1024",
        })

        assert response.status_code in [200, 400, 422, 503]

    @pytest.mark.asyncio
    async def test_invalid_size(self, client: AsyncClient):
        """Test generating with invalid size."""
        response = await client.post("/api/images/generate", json={
            "prompt": "Test image",
            "provider": "gpt-image-2",
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
