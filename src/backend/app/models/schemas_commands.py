"""
THÉRÈSE v2 - Schemas Commands

Request/Response models pour les commandes utilisateur personnalisées.
"""

from pydantic import BaseModel, Field


class CreateCommandRequest(BaseModel):
    """Create user command request."""

    name: str = Field(..., min_length=1, max_length=50, description="Slug de la commande")
    description: str = Field("", max_length=200)
    category: str = Field("general", max_length=50)
    icon: str = Field("", max_length=10)
    show_on_home: bool = False
    content: str = Field("", description="Contenu/prompt de la commande")


class UpdateCommandRequest(BaseModel):
    """Update user command request."""

    description: str | None = None
    category: str | None = None
    icon: str | None = None
    show_on_home: bool | None = None
    content: str | None = None


class CommandResponse(BaseModel):
    """Command response."""

    name: str
    description: str
    category: str
    icon: str
    show_on_home: bool
    content: str
    created_at: str | None = None
    updated_at: str | None = None
