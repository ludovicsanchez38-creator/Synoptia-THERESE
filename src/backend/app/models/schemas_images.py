"""
THÉRÈSE v2 - Schemas Images

Request/Response models pour la génération d'images.
"""

from typing import Literal

from pydantic import BaseModel


class ImageGenerateRequest(BaseModel):
    """Request to generate an image."""

    prompt: str
    provider: Literal["gpt-image-1.5", "nanobanan-pro"] = "gpt-image-1.5"
    # Options OpenAI
    size: Literal["1024x1024", "1536x1024", "1024x1536"] = "1024x1024"
    quality: Literal["low", "medium", "high"] = "high"
    # Options Gemini
    aspect_ratio: str = "1:1"
    image_size: Literal["1K", "2K", "4K"] = "2K"


class ImageResponse(BaseModel):
    """Response with generated image info."""

    id: str
    provider: str
    file_name: str
    file_size: int
    mime_type: str
    created_at: str
    prompt: str
    download_url: str


class ImageListResponse(BaseModel):
    """Response with list of images."""

    images: list[ImageResponse]
    total: int


class ImageProviderStatus(BaseModel):
    """Status of image generation providers."""

    openai_available: bool
    gemini_available: bool
    active_provider: str | None
