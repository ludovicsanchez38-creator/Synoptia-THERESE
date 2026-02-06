"""
THÉRÈSE v2 - Image Generation Service

Supports GPT Image 1.5 (OpenAI) and Nano Banana Pro (Google Gemini).
"""

import base64
import logging
import os
import uuid
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Literal

logger = logging.getLogger(__name__)


def _get_api_key_from_db(provider: str) -> str | None:
    """
    Load API key from database (Preferences table).
    Falls back to environment variable if DB not available.
    """
    try:
        # Import here to avoid circular imports
        from app.config import settings
        from sqlalchemy import create_engine, text

        engine = create_engine(f"sqlite:///{settings.db_path}")
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT value FROM preferences WHERE key = :key"),
                {"key": f"{provider}_api_key"}
            )
            row = result.fetchone()
            if row:
                return row[0]
    except Exception as e:
        logger.debug(f"Could not load {provider} API key from DB: {e}")

    return None


class ImageProvider(str, Enum):
    """Supported image generation providers."""

    OPENAI = "gpt-image-1.5"
    GEMINI = "nanobanan-pro"


@dataclass
class ImageConfig:
    """Image generation configuration."""

    provider: ImageProvider
    # OpenAI settings
    size: Literal["1024x1024", "1536x1024", "1024x1536"] = "1024x1024"
    quality: Literal["low", "medium", "high"] = "high"
    # Gemini settings
    aspect_ratio: str = "1:1"
    image_size: Literal["1K", "2K", "4K"] = "2K"


@dataclass
class GeneratedImage:
    """Generated image result."""

    id: str
    provider: str
    file_path: Path
    file_name: str
    file_size: int
    mime_type: str
    created_at: str
    prompt: str
    download_url: str | None = None


class ImageGeneratorService:
    """Service for generating images with multiple providers."""

    def __init__(self, output_dir: Path | None = None):
        """Initialize image generator."""
        self.output_dir = output_dir or Path.home() / ".therese" / "images"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    async def generate(
        self,
        prompt: str,
        provider: ImageProvider = ImageProvider.OPENAI,
        config: ImageConfig | None = None,
        reference_image_path: str | None = None,
    ) -> GeneratedImage:
        """
        Generate an image from a prompt.

        Args:
            prompt: Text description of the image to generate
            provider: Which provider to use
            config: Generation configuration
            reference_image_path: Optional path to reference image

        Returns:
            GeneratedImage with file info
        """
        if config is None:
            config = ImageConfig(provider=provider)

        if provider == ImageProvider.OPENAI:
            return await self._generate_openai(prompt, config, reference_image_path)
        elif provider == ImageProvider.GEMINI:
            return await self._generate_gemini(prompt, config, reference_image_path)
        else:
            raise ValueError(f"Unsupported provider: {provider}")

    async def _generate_openai(
        self,
        prompt: str,
        config: ImageConfig,
        reference_image_path: str | None = None,
    ) -> GeneratedImage:
        """Generate image with OpenAI GPT Image 1.5."""
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError("openai package required. Install with: pip install openai")

        # Try image-specific key first, then fallback to general OpenAI key
        api_key = (
            os.getenv("OPENAI_IMAGE_API_KEY")
            or _get_api_key_from_db("openai_image")
            or os.getenv("OPENAI_API_KEY")
            or _get_api_key_from_db("openai")
        )
        if not api_key:
            raise ValueError("Clé API OpenAI (Image) non configurée. Ajoutez-la dans Paramètres > LLM > Génération d'images.")

        client = OpenAI(api_key=api_key)

        try:
            if reference_image_path and Path(reference_image_path).exists():
                # Edit mode with reference image
                with open(reference_image_path, "rb") as ref_file:
                    result = client.images.edit(
                        model="gpt-image-1.5",
                        image=ref_file,
                        prompt=prompt,
                        size=config.size,
                        quality=config.quality,
                        input_fidelity="high",  # Crucial for face preservation
                    )
            else:
                # Generation mode without reference
                # Note: gpt-image-1.5 n'accepte plus response_format, retourne URL par défaut
                result = client.images.generate(
                    model="gpt-image-1.5",
                    prompt=prompt,
                    size=config.size,
                    quality=config.quality,
                )

            # Get image data
            if hasattr(result.data[0], "b64_json") and result.data[0].b64_json:
                image_bytes = base64.b64decode(result.data[0].b64_json)
            elif hasattr(result.data[0], "url") and result.data[0].url:
                # Download from URL if b64 not available
                from app.services.http_client import get_http_client

                http_client = await get_http_client()
                resp = await http_client.get(result.data[0].url)
                image_bytes = resp.content
            else:
                raise ValueError("No image data in response")

            return self._save_image(
                image_bytes=image_bytes,
                provider=ImageProvider.OPENAI.value,
                prompt=prompt,
                extension="png",
            )

        except Exception as e:
            logger.error(f"OpenAI image generation error: {e}")
            raise

    async def _generate_gemini(
        self,
        prompt: str,
        config: ImageConfig,
        reference_image_path: str | None = None,
    ) -> GeneratedImage:
        """Generate image with Google Gemini 3 Pro Image."""
        try:
            from google import genai
            from google.genai import types
        except ImportError:
            raise ImportError("google-genai package required. Install with: pip install google-genai")

        # Try image-specific key first, then fallback to general Gemini key
        api_key = (
            os.getenv("GEMINI_IMAGE_API_KEY")
            or _get_api_key_from_db("gemini_image")
            or os.getenv("GEMINI_API_KEY")
            or os.getenv("GOOGLE_API_KEY")
            or _get_api_key_from_db("gemini")
        )
        if not api_key:
            raise ValueError("Clé API Gemini (Image) non configurée. Ajoutez-la dans Paramètres > LLM > Génération d'images.")

        client = genai.Client(api_key=api_key)

        try:
            # Build content list
            contents = [prompt]

            # Add reference image if provided
            if reference_image_path and Path(reference_image_path).exists():
                from PIL import Image

                ref_image = Image.open(reference_image_path)
                contents.append(ref_image)

            # Generate image
            response = client.models.generate_content(
                model="gemini-3-pro-image-preview",
                contents=contents,
                config=types.GenerateContentConfig(
                    response_modalities=["TEXT", "IMAGE"],
                    image_config=types.ImageConfig(
                        aspect_ratio=config.aspect_ratio,
                        image_size=config.image_size,
                    ),
                ),
            )

            # Extract image from response
            image_bytes = None
            for part in response.candidates[0].content.parts:
                if hasattr(part, "inline_data") and part.inline_data:
                    image_bytes = part.inline_data.data
                    break

            if not image_bytes:
                raise ValueError("No image data in Gemini response")

            return self._save_image(
                image_bytes=image_bytes,
                provider=ImageProvider.GEMINI.value,
                prompt=prompt,
                extension="png",
            )

        except Exception as e:
            logger.error(f"Gemini image generation error: {e}")
            raise

    def _save_image(
        self,
        image_bytes: bytes,
        provider: str,
        prompt: str,
        extension: str = "png",
    ) -> GeneratedImage:
        """Save generated image to disk."""
        # Generate unique ID and filename
        image_id = str(uuid.uuid4())[:8]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = f"therese_{timestamp}_{image_id}.{extension}"
        file_path = self.output_dir / file_name

        # Write image
        file_path.write_bytes(image_bytes)
        file_size = file_path.stat().st_size

        logger.info(f"Image saved: {file_path} ({file_size} bytes)")

        return GeneratedImage(
            id=image_id,
            provider=provider,
            file_path=file_path,
            file_name=file_name,
            file_size=file_size,
            mime_type=f"image/{extension}",
            created_at=datetime.now().isoformat(),
            prompt=prompt,
        )

    def get_image(self, image_id: str) -> GeneratedImage | None:
        """Get a previously generated image by ID."""
        for file_path in self.output_dir.glob(f"*_{image_id}.*"):
            if file_path.is_file():
                return GeneratedImage(
                    id=image_id,
                    provider="unknown",
                    file_path=file_path,
                    file_name=file_path.name,
                    file_size=file_path.stat().st_size,
                    mime_type=f"image/{file_path.suffix[1:]}",
                    created_at=datetime.fromtimestamp(file_path.stat().st_mtime).isoformat(),
                    prompt="",
                )
        return None

    def list_images(self, limit: int = 50) -> list[GeneratedImage]:
        """List generated images."""
        images = []
        for file_path in sorted(self.output_dir.glob("therese_*.*"), reverse=True)[:limit]:
            if file_path.is_file():
                # Extract ID from filename
                parts = file_path.stem.split("_")
                image_id = parts[-1] if len(parts) > 2 else file_path.stem

                images.append(
                    GeneratedImage(
                        id=image_id,
                        provider="unknown",
                        file_path=file_path,
                        file_name=file_path.name,
                        file_size=file_path.stat().st_size,
                        mime_type=f"image/{file_path.suffix[1:]}",
                        created_at=datetime.fromtimestamp(file_path.stat().st_mtime).isoformat(),
                        prompt="",
                    )
                )
        return images


# Global instance
_image_service: ImageGeneratorService | None = None


def get_image_service() -> ImageGeneratorService:
    """Get global image generator service instance."""
    global _image_service
    if _image_service is None:
        _image_service = ImageGeneratorService()
    return _image_service
