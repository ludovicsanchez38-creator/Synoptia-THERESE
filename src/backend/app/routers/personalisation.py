"""
THERESE v2 - Personalisation Router

API endpoints for user personalisation preferences.
US-PERS-01 to US-PERS-05.
"""

import json
import logging
from datetime import UTC, datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.database import get_session
from app.models.entities import Preference, PromptTemplate

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================
# Schemas
# ============================================================


class PromptTemplateCreate(BaseModel):
    """Create prompt template request."""
    name: str
    prompt: str
    category: str = "general"
    icon: Optional[str] = None


class PromptTemplateUpdate(BaseModel):
    """Update prompt template request."""
    name: Optional[str] = None
    prompt: Optional[str] = None
    category: Optional[str] = None
    icon: Optional[str] = None


class PromptTemplateResponse(BaseModel):
    """Prompt template response."""
    id: str
    name: str
    prompt: str
    category: str
    icon: Optional[str]
    created_at: datetime
    updated_at: datetime


class LLMBehaviorSettings(BaseModel):
    """LLM behavior configuration (US-PERS-04)."""
    custom_system_prompt: str = ""
    use_custom_system_prompt: bool = False
    response_style: str = "detailed"  # concise, detailed, creative
    language: str = "french"  # french, english, auto
    include_memory_context: bool = True
    max_history_messages: int = 50


class FeatureVisibilitySettings(BaseModel):
    """Feature visibility configuration (US-PERS-05)."""
    show_board: bool = True
    show_calculators: bool = True
    show_image_generation: bool = True
    show_voice_input: bool = True
    show_file_browser: bool = True
    show_mcp_tools: bool = True
    show_guided_prompts: bool = True
    show_entity_suggestions: bool = True


# ============================================================
# US-PERS-02: Prompt Templates
# ============================================================


@router.get("/templates", response_model=list[PromptTemplateResponse])
async def list_prompt_templates(
    category: Optional[str] = None,
    session: AsyncSession = Depends(get_session),
):
    """List all prompt templates, optionally filtered by category."""
    query = select(PromptTemplate).order_by(PromptTemplate.created_at.desc())
    if category:
        query = query.where(PromptTemplate.category == category)

    result = await session.execute(query)
    templates = result.scalars().all()

    return [
        PromptTemplateResponse(
            id=t.id,
            name=t.name,
            prompt=t.prompt,
            category=t.category,
            icon=t.icon,
            created_at=t.created_at,
            updated_at=t.updated_at,
        )
        for t in templates
    ]


@router.post("/templates", response_model=PromptTemplateResponse)
async def create_prompt_template(
    request: PromptTemplateCreate,
    session: AsyncSession = Depends(get_session),
):
    """Create a new prompt template."""
    template = PromptTemplate(
        name=request.name,
        prompt=request.prompt,
        category=request.category,
        icon=request.icon,
    )
    session.add(template)
    await session.commit()
    await session.refresh(template)

    return PromptTemplateResponse(
        id=template.id,
        name=template.name,
        prompt=template.prompt,
        category=template.category,
        icon=template.icon,
        created_at=template.created_at,
        updated_at=template.updated_at,
    )


@router.get("/templates/{template_id}", response_model=PromptTemplateResponse)
async def get_prompt_template(
    template_id: str,
    session: AsyncSession = Depends(get_session),
):
    """Get a specific prompt template."""
    result = await session.execute(
        select(PromptTemplate).where(PromptTemplate.id == template_id)
    )
    template = result.scalar_one_or_none()

    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    return PromptTemplateResponse(
        id=template.id,
        name=template.name,
        prompt=template.prompt,
        category=template.category,
        icon=template.icon,
        created_at=template.created_at,
        updated_at=template.updated_at,
    )


@router.put("/templates/{template_id}", response_model=PromptTemplateResponse)
async def update_prompt_template(
    template_id: str,
    request: PromptTemplateUpdate,
    session: AsyncSession = Depends(get_session),
):
    """Update a prompt template."""
    result = await session.execute(
        select(PromptTemplate).where(PromptTemplate.id == template_id)
    )
    template = result.scalar_one_or_none()

    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    if request.name is not None:
        template.name = request.name
    if request.prompt is not None:
        template.prompt = request.prompt
    if request.category is not None:
        template.category = request.category
    if request.icon is not None:
        template.icon = request.icon

    template.updated_at = datetime.now(UTC)
    await session.commit()
    await session.refresh(template)

    return PromptTemplateResponse(
        id=template.id,
        name=template.name,
        prompt=template.prompt,
        category=template.category,
        icon=template.icon,
        created_at=template.created_at,
        updated_at=template.updated_at,
    )


@router.delete("/templates/{template_id}")
async def delete_prompt_template(
    template_id: str,
    session: AsyncSession = Depends(get_session),
):
    """Delete a prompt template."""
    result = await session.execute(
        select(PromptTemplate).where(PromptTemplate.id == template_id)
    )
    template = result.scalar_one_or_none()

    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    await session.delete(template)
    await session.commit()

    return {"deleted": True, "id": template_id}


# ============================================================
# US-PERS-04: LLM Behavior Settings
# ============================================================


@router.get("/llm-behavior", response_model=LLMBehaviorSettings)
async def get_llm_behavior(
    session: AsyncSession = Depends(get_session),
):
    """Get LLM behavior settings."""
    result = await session.execute(
        select(Preference).where(Preference.key == "llm_behavior")
    )
    pref = result.scalar_one_or_none()

    if pref:
        try:
            data = json.loads(pref.value)
            return LLMBehaviorSettings(**data)
        except (json.JSONDecodeError, TypeError):
            pass

    return LLMBehaviorSettings()


@router.post("/llm-behavior", response_model=LLMBehaviorSettings)
async def set_llm_behavior(
    settings: LLMBehaviorSettings,
    session: AsyncSession = Depends(get_session),
):
    """Set LLM behavior settings."""
    result = await session.execute(
        select(Preference).where(Preference.key == "llm_behavior")
    )
    pref = result.scalar_one_or_none()

    value = json.dumps(settings.model_dump())

    if pref:
        pref.value = value
        pref.updated_at = datetime.now(UTC)
    else:
        pref = Preference(
            key="llm_behavior",
            value=value,
            category="llm",
        )
        session.add(pref)

    await session.commit()
    return settings


# ============================================================
# US-PERS-05: Feature Visibility Settings
# ============================================================


@router.get("/features", response_model=FeatureVisibilitySettings)
async def get_feature_visibility(
    session: AsyncSession = Depends(get_session),
):
    """Get feature visibility settings."""
    result = await session.execute(
        select(Preference).where(Preference.key == "feature_visibility")
    )
    pref = result.scalar_one_or_none()

    if pref:
        try:
            data = json.loads(pref.value)
            return FeatureVisibilitySettings(**data)
        except (json.JSONDecodeError, TypeError):
            pass

    return FeatureVisibilitySettings()


@router.post("/features", response_model=FeatureVisibilitySettings)
async def set_feature_visibility(
    settings: FeatureVisibilitySettings,
    session: AsyncSession = Depends(get_session),
):
    """Set feature visibility settings."""
    result = await session.execute(
        select(Preference).where(Preference.key == "feature_visibility")
    )
    pref = result.scalar_one_or_none()

    value = json.dumps(settings.model_dump())

    if pref:
        pref.value = value
        pref.updated_at = datetime.now(UTC)
    else:
        pref = Preference(
            key="feature_visibility",
            value=value,
            category="ui",
        )
        session.add(pref)

    await session.commit()
    return settings


# ============================================================
# Combined Personalisation Status
# ============================================================


@router.get("/status")
async def get_personalisation_status(
    session: AsyncSession = Depends(get_session),
):
    """Get combined personalisation status."""
    # Get templates count
    templates_result = await session.execute(
        select(PromptTemplate)
    )
    templates = templates_result.scalars().all()

    # Get LLM behavior
    llm_result = await session.execute(
        select(Preference).where(Preference.key == "llm_behavior")
    )
    llm_pref = llm_result.scalar_one_or_none()
    llm_behavior = LLMBehaviorSettings()
    if llm_pref:
        try:
            llm_behavior = LLMBehaviorSettings(**json.loads(llm_pref.value))
        except (json.JSONDecodeError, TypeError):
            pass

    # Get feature visibility
    features_result = await session.execute(
        select(Preference).where(Preference.key == "feature_visibility")
    )
    features_pref = features_result.scalar_one_or_none()
    feature_visibility = FeatureVisibilitySettings()
    if features_pref:
        try:
            feature_visibility = FeatureVisibilitySettings(**json.loads(features_pref.value))
        except (json.JSONDecodeError, TypeError):
            pass

    return {
        "templates_count": len(templates),
        "templates_by_category": _count_by_category(templates),
        "llm_behavior": llm_behavior.model_dump(),
        "feature_visibility": feature_visibility.model_dump(),
    }


def _count_by_category(templates: list[PromptTemplate]) -> dict[str, int]:
    """Count templates by category."""
    counts: dict[str, int] = {}
    for t in templates:
        counts[t.category] = counts.get(t.category, 0) + 1
    return counts
