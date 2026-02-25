"""
THÉRÈSE v2 - Installed Tools Router

API endpoints pour gérer les outils installés.
"""

import logging
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.skills.registry import get_skills_registry
from app.services.skills.tool_installer import get_tool_installer

logger = logging.getLogger(__name__)
router = APIRouter()


# --- Schemas ---


class ToolInstallRequest(BaseModel):
    """Requête d'installation d'un outil."""
    tool_id: str = Field(..., description="Identifiant unique (slug)")
    name: str = Field(..., description="Nom de l'outil")
    description: str = Field(default="", description="Description")
    output_format: str = Field(..., description="Format de sortie (xlsx, docx, pptx)")
    code: str = Field(..., description="Script Python à installer")
    inputs: list[dict[str, Any]] = Field(default_factory=list, description="Schema des entrées")
    test_input: dict[str, Any] = Field(default_factory=dict, description="Données de test")
    model: str | None = Field(None, description="Modèle source (informatif)")


class ToolInstallResponse(BaseModel):
    """Réponse d'installation."""
    success: bool
    tool_id: str | None = None
    tool_dir: str | None = None
    error: str | None = None
    attempts: int = 0


class ToolTestResponse(BaseModel):
    """Réponse de test."""
    success: bool
    message: str


# --- Endpoints ---


@router.get("")
async def list_tools() -> list[dict[str, Any]]:
    """Liste les outils installés."""
    from app.services.skills.installed_tool import InstalledToolSkill

    registry = get_skills_registry()
    tools = []
    for skill in registry._skills.values():
        if isinstance(skill, InstalledToolSkill):
            tools.append(skill.to_dict())
    return tools


@router.post("/install")
async def install_tool(request: ToolInstallRequest) -> ToolInstallResponse:
    """
    Installe un nouvel outil.

    Valide le code dans le sandbox puis l'installe dans ~/.therese/tools/.
    """
    installer = get_tool_installer()

    result = await installer.install_tool(
        tool_id=request.tool_id,
        name=request.name,
        description=request.description,
        output_format=request.output_format,
        code=request.code,
        inputs=request.inputs,
        test_input=request.test_input,
        model=request.model,
    )

    if result.success:
        # Re-découvrir les outils pour charger le nouveau
        registry = get_skills_registry()
        registry.discover_installed_tools()

    return ToolInstallResponse(
        success=result.success,
        tool_id=result.tool_id,
        tool_dir=result.tool_dir,
        error=result.error,
        attempts=result.attempts,
    )


@router.get("/{tool_id}/manifest")
async def get_tool_manifest(tool_id: str) -> dict[str, Any]:
    """Voir le manifest d'un outil."""
    from app.services.skills.installed_tool import InstalledToolSkill

    registry = get_skills_registry()
    skill = registry.get(f"tool:{tool_id}")

    if not skill or not isinstance(skill, InstalledToolSkill):
        raise HTTPException(status_code=404, detail=f"Outil '{tool_id}' non trouvé")

    return skill.manifest


@router.post("/{tool_id}/test")
async def test_tool(
    tool_id: str,
    test_input: dict[str, Any] | None = None,
) -> ToolTestResponse:
    """Re-teste un outil existant."""
    installer = get_tool_installer()
    success, message = await installer.test_tool(tool_id, test_input)
    return ToolTestResponse(success=success, message=message)


@router.delete("/{tool_id}")
async def delete_tool(tool_id: str) -> dict[str, Any]:
    """Désinstalle un outil."""
    installer = get_tool_installer()
    deleted = await installer.uninstall_tool(tool_id)

    if not deleted:
        raise HTTPException(status_code=404, detail=f"Outil '{tool_id}' non trouvé")

    # Retirer du registry
    registry = get_skills_registry()
    skill_id = f"tool:{tool_id}"
    if skill_id in registry._skills:
        del registry._skills[skill_id]

    return {"success": True, "message": f"Outil {tool_id} désinstallé"}
