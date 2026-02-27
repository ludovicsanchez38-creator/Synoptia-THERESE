"""
THÉRÈSE V3 - Commands Router Unifié

API /api/v3/commands - Point d'entrée unique pour toutes les commandes.
"""

import logging

from app.models.command import (
    CommandDefinitionResponse,
    CreateUserCommandRequest,
    GenerateTemplateRequest,
    UpdateUserCommandRequest,
)
from app.services.command_registry import get_command_registry
from fastapi import APIRouter, HTTPException, Query

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("", response_model=list[CommandDefinitionResponse])
async def list_commands(
    category: str | None = Query(None, description="Filtrer par catégorie"),
    show_on_home: bool | None = Query(None, description="Filtrer commandes affichées sur l'accueil"),
    show_in_slash: bool | None = Query(None, description="Filtrer commandes dans le menu /"),
    source: str | None = Query(None, description="Filtrer par source (builtin, skill, user, mcp)"),
):
    """Liste toutes les commandes (avec filtres optionnels)."""
    registry = get_command_registry()
    commands = registry.list(
        category=category,
        show_on_home=show_on_home,
        show_in_slash=show_in_slash,
        source=source,
    )
    return [CommandDefinitionResponse(**cmd.model_dump()) for cmd in commands]


@router.get("/{command_id}", response_model=CommandDefinitionResponse)
async def get_command(command_id: str):
    """Récupère une commande par son ID."""
    registry = get_command_registry()
    cmd = registry.get(command_id)
    if not cmd:
        raise HTTPException(status_code=404, detail=f"Commande '{command_id}' introuvable")
    return CommandDefinitionResponse(**cmd.model_dump())


@router.get("/{command_id}/schema")
async def get_command_schema(command_id: str):
    """Récupère le schéma de formulaire d'une commande (si skill_id)."""
    registry = get_command_registry()
    cmd = registry.get(command_id)
    if not cmd:
        raise HTTPException(status_code=404, detail=f"Commande '{command_id}' introuvable")

    if not cmd.skill_id:
        raise HTTPException(status_code=400, detail="Cette commande n'a pas de skill associé")

    from app.services.skills.registry import get_skills_registry

    skills_registry = get_skills_registry()
    skill = skills_registry.get(cmd.skill_id)
    if not skill:
        raise HTTPException(status_code=404, detail=f"Skill '{cmd.skill_id}' introuvable")

    # Récupérer le schéma d'inputs du skill
    schema = {}
    if hasattr(skill, "get_input_schema"):
        schema = skill.get_input_schema()

    return {
        "command_id": command_id,
        "skill_id": cmd.skill_id,
        "output_type": skill.output_type.value if hasattr(skill, "output_type") else "text",
        "schema": schema,
    }


@router.post("/user", response_model=CommandDefinitionResponse, status_code=201)
async def create_user_command(request: CreateUserCommandRequest):
    """Crée une nouvelle commande utilisateur."""
    registry = get_command_registry()
    try:
        cmd = await registry.create_user_command(
            name=request.name,
            description=request.description,
            icon=request.icon,
            category=request.category,
            prompt_template=request.prompt_template,
            show_on_home=request.show_on_home,
            show_in_slash=request.show_in_slash,
        )
        return CommandDefinitionResponse(**cmd.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.put("/user/{command_id}", response_model=CommandDefinitionResponse)
async def update_user_command(command_id: str, request: UpdateUserCommandRequest):
    """Met à jour une commande utilisateur."""
    registry = get_command_registry()
    cmd = await registry.update_user_command(
        command_id=command_id,
        name=request.name,
        description=request.description,
        icon=request.icon,
        category=request.category,
        prompt_template=request.prompt_template,
        show_on_home=request.show_on_home,
        show_in_slash=request.show_in_slash,
    )
    if not cmd:
        raise HTTPException(status_code=404, detail=f"Commande '{command_id}' introuvable ou non modifiable")
    return CommandDefinitionResponse(**cmd.model_dump())


@router.delete("/user/{command_id}")
async def delete_user_command(command_id: str):
    """Supprime une commande utilisateur."""
    registry = get_command_registry()
    deleted = await registry.delete_user_command(command_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Commande '{command_id}' introuvable ou non supprimable")
    return {"message": f"Commande '{command_id}' supprimée"}


@router.post("/generate-template")
async def generate_template(request: GenerateTemplateRequest):
    """RFC : Génère un template de commande depuis un brief (via LLM)."""
    from app.services.llm import get_llm_service

    llm = get_llm_service()

    system_prompt = (
        "Tu es un expert en création de prompts et de commandes pour THÉRÈSE, "
        "une assistante IA pour entrepreneurs. "
        "L'utilisateur te donne un brief décrivant ce que sa commande doit faire. "
        "Tu dois générer un template de commande au format JSON avec les champs : "
        "name (slug court), description (1 phrase), icon (un seul emoji), "
        "category (production/analyse/organisation), "
        "prompt_template (template avec des {{placeholders}} entre doubles accolades). "
        "Réponds UNIQUEMENT avec le JSON, sans markdown ni explication."
    )

    # Construire les messages pour le LLM
    messages = []
    if request.context:
        for msg in request.context:
            messages.append({"role": msg.get("role", "user"), "content": msg.get("content", "")})

    messages.append({"role": "user", "content": request.brief})

    try:
        response = await llm.generate(
            messages=messages,
            system_prompt=system_prompt,
            max_tokens=500,
        )

        # Parser le JSON de la réponse
        import json
        content = response.content.strip()
        # Nettoyer les backticks markdown si présents
        if content.startswith("```"):
            content = content.split("\n", 1)[1] if "\n" in content else content[3:]
            content = content.rsplit("```", 1)[0]
        template = json.loads(content)

        return {
            "name": template.get("name", ""),
            "description": template.get("description", ""),
            "icon": template.get("icon", ""),
            "category": template.get("category", "production"),
            "prompt_template": template.get("prompt_template", ""),
        }
    except Exception as e:
        logger.error(f"Erreur génération template : {e}")
        raise HTTPException(status_code=500, detail=f"Erreur lors de la génération du template : {e}")
