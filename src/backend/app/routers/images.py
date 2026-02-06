"""
THÉRÈSE v2 - Images Router

API endpoints for image generation with GPT Image 1.5 and Nano Banana Pro.
"""

import logging
import os
from typing import Literal

from app.models.schemas_images import (
    ImageGenerateRequest,
    ImageListResponse,
    ImageProviderStatus,
    ImageResponse,
)
from app.services.image_generator import (
    ImageConfig,
    ImageProvider,
    get_image_service,
)
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/status")
async def get_image_status() -> ImageProviderStatus:
    """Check status of image generation providers."""
    openai_key = os.getenv("OPENAI_API_KEY")
    gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

    active = None
    if openai_key:
        active = "gpt-image-1.5"
    elif gemini_key:
        active = "nanobanan-pro"

    return ImageProviderStatus(
        openai_available=bool(openai_key),
        gemini_available=bool(gemini_key),
        active_provider=active,
    )


@router.post("/generate")
async def generate_image(request: ImageGenerateRequest) -> ImageResponse:
    """
    Generate an image from a text prompt.

    Supports:
    - GPT Image 1.5 (OpenAI): High quality, good for portraits
    - Nano Banana Pro (Gemini): Up to 4K, good with reference images
    """
    try:
        service = get_image_service()

        # Map string provider to enum
        provider = ImageProvider(request.provider)

        # Build config
        config = ImageConfig(
            provider=provider,
            size=request.size,
            quality=request.quality,
            aspect_ratio=request.aspect_ratio,
            image_size=request.image_size,
        )

        # Generate image
        result = await service.generate(
            prompt=request.prompt,
            provider=provider,
            config=config,
        )

        return ImageResponse(
            id=result.id,
            provider=result.provider,
            file_name=result.file_name,
            file_size=result.file_size,
            mime_type=result.mime_type,
            created_at=result.created_at,
            prompt=result.prompt,
            download_url=f"/api/images/download/{result.id}",
        )

    except ValueError as e:
        logger.error(f"Image generation config error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except ImportError as e:
        logger.error(f"Missing dependency: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Missing dependency for image generation: {e}",
        )
    except Exception as e:
        logger.error(f"Image generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Image generation failed: {e}")


@router.post("/generate-with-reference")
async def generate_with_reference(
    prompt: str = Form(...),
    provider: Literal["gpt-image-1.5", "nanobanan-pro"] = Form("gpt-image-1.5"),
    size: Literal["1024x1024", "1536x1024", "1024x1536"] = Form("1024x1024"),
    quality: Literal["low", "medium", "high"] = Form("high"),
    aspect_ratio: str = Form("1:1"),
    image_size: Literal["1K", "2K", "4K"] = Form("2K"),
    reference: UploadFile = File(...),
) -> ImageResponse:
    """
    Generate an image with a reference image.

    Upload a reference image to guide the generation.
    Particularly useful for style transfer or editing.
    """
    try:
        service = get_image_service()

        # Save uploaded reference temporarily
        temp_path = service.output_dir / f"ref_{reference.filename}"
        with open(temp_path, "wb") as f:
            content = await reference.read()
            f.write(content)

        try:
            # Map string provider to enum
            provider_enum = ImageProvider(provider)

            # Build config
            config = ImageConfig(
                provider=provider_enum,
                size=size,
                quality=quality,
                aspect_ratio=aspect_ratio,
                image_size=image_size,
            )

            # Generate with reference
            result = await service.generate(
                prompt=prompt,
                provider=provider_enum,
                config=config,
                reference_image_path=str(temp_path),
            )

            return ImageResponse(
                id=result.id,
                provider=result.provider,
                file_name=result.file_name,
                file_size=result.file_size,
                mime_type=result.mime_type,
                created_at=result.created_at,
                prompt=result.prompt,
                download_url=f"/api/images/download/{result.id}",
            )

        finally:
            # Clean up temp file
            if temp_path.exists():
                temp_path.unlink()

    except ValueError as e:
        logger.error(f"Image generation config error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Image generation with reference failed: {e}")
        raise HTTPException(status_code=500, detail=f"Image generation failed: {e}")


@router.get("/download/{image_id}")
async def download_image(image_id: str):
    """Download a generated image by ID."""
    service = get_image_service()
    image = service.get_image(image_id)

    if not image:
        raise HTTPException(status_code=404, detail="Image not found")

    return FileResponse(
        path=image.file_path,
        media_type=image.mime_type,
        filename=image.file_name,
    )


@router.get("/list")
async def list_images(limit: int = 50) -> ImageListResponse:
    """List recently generated images."""
    service = get_image_service()
    images = service.list_images(limit=limit)

    return ImageListResponse(
        images=[
            ImageResponse(
                id=img.id,
                provider=img.provider,
                file_name=img.file_name,
                file_size=img.file_size,
                mime_type=img.mime_type,
                created_at=img.created_at,
                prompt=img.prompt,
                download_url=f"/api/images/download/{img.id}",
            )
            for img in images
        ],
        total=len(images),
    )


@router.delete("/{image_id}")
async def delete_image(image_id: str) -> dict:
    """Delete a generated image."""
    service = get_image_service()
    image = service.get_image(image_id)

    if not image:
        raise HTTPException(status_code=404, detail="Image not found")

    try:
        image.file_path.unlink()
        return {"deleted": True, "id": image_id}
    except Exception as e:
        logger.error(f"Failed to delete image {image_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete image: {e}")
