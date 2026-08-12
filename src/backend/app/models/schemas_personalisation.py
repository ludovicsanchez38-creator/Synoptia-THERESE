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
    """LLM behavior configuration (US-PERS-04).

    BUG-164 : `language` a été retiré. Il était stocké par les routes
    `/api/personalisation/llm-behavior`, lu par AUCUN code, et affiché par
    AUCUN écran. Un réglage qu'on enregistre sans jamais le consulter fait
    croire au prochain développeur que la langue est déjà configurable, et à
    qui explore l'API qu'il peut la régler. La langue est désormais imposée
    dans le prompt système, sur les deux points de passage vers un modèle
    (`LLMService.LANGUE_BLOCK`).

    Les cinq champs restants sont dans le même état — stockés, jamais lus,
    sans écran. Ils sont conservés faute d'avoir été instruits : les retirer
    demande de décider s'il faut les brancher ou les supprimer, ce qui dépasse
    un correctif de bug.
    """

    custom_system_prompt: str = ""
    use_custom_system_prompt: bool = False
    response_style: str = "detailed"  # concise, detailed, creative
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
