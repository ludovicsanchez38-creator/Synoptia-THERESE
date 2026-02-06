"""
THÉRÈSE v2 - Schemas Skills

Request/Response models pour l'exécution de skills (génération de documents).
"""

from pydantic import BaseModel, Field


class ExecuteSkillRequest(BaseModel):
    """Requête pour exécuter un skill."""

    prompt: str = Field(
        ..., description="Prompt utilisateur décrivant le document à générer"
    )
    title: str | None = Field(None, description="Titre du document (optionnel)")
    template: str = Field(default="synoptia-dark", description="Style/template")
    context: dict = Field(default_factory=dict, description="Contexte additionnel")


class SkillInfo(BaseModel):
    """Informations sur un skill."""

    skill_id: str
    name: str
    description: str
    format: str
