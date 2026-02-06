"""
THÉRÈSE v2 - Schemas Personnalisation

Request/Response models pour les préférences de personnalisation.
"""

from datetime import datetime

from pydantic import BaseModel

# ============================================================
# Prompt Templates (US-PERS-02)
# ============================================================


class PromptTemplateCreate(BaseModel):
    """Create prompt template request."""

    name: str
    prompt: str
    category: str = "general"
    icon: str | None = None


class PromptTemplateUpdate(BaseModel):
    """Update prompt template request."""

    name: str | None = None
    prompt: str | None = None
    category: str | None = None
    icon: str | None = None


class PromptTemplateResponse(BaseModel):
    """Prompt template response."""

    id: str
    name: str
    prompt: str
    category: str
    icon: str | None
    created_at: datetime
    updated_at: datetime


# ============================================================
# LLM Behavior (US-PERS-04)
# ============================================================


class LLMBehaviorSettings(BaseModel):
    """LLM behavior configuration (US-PERS-04)."""

    custom_system_prompt: str = ""
    use_custom_system_prompt: bool = False
    response_style: str = "detailed"  # concise, detailed, creative
    language: str = "french"  # french, english, auto
    include_memory_context: bool = True
    max_history_messages: int = 50


# ============================================================
# Feature Visibility (US-PERS-05)
# ============================================================


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
