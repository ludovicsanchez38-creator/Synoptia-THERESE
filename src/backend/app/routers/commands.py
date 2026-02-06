"""
THERESE v2 - User Commands Router

Endpoints CRUD pour les commandes utilisateur personnalisees.
"""

import logging

from app.models.schemas_commands import (
    CommandResponse,
    CreateCommandRequest,
    UpdateCommandRequest,
)
from app.services.user_commands import UserCommandsService
from fastapi import APIRouter, HTTPException

logger = logging.getLogger(__name__)
router = APIRouter()


# --- Endpoints ---

@router.get("/user", response_model=list[CommandResponse])
async def list_user_commands():
    """Liste toutes les commandes utilisateur."""
    service = UserCommandsService.get_instance()
    commands = service.list_commands()
    return [CommandResponse(**cmd.to_dict()) for cmd in commands]


@router.get("/user/{name}", response_model=CommandResponse)
async def get_user_command(name: str):
    """Recupere une commande utilisateur par son nom."""
    service = UserCommandsService.get_instance()
    cmd = service.get_command(name)
    if not cmd:
        raise HTTPException(status_code=404, detail=f"Commande '{name}' introuvable")
    return CommandResponse(**cmd.to_dict())


@router.post("/user", response_model=CommandResponse, status_code=201)
async def create_user_command(request: CreateCommandRequest):
    """Cree une nouvelle commande utilisateur."""
    service = UserCommandsService.get_instance()
    try:
        cmd = service.create_command(
            name=request.name,
            description=request.description,
            category=request.category,
            icon=request.icon,
            show_on_home=request.show_on_home,
            content=request.content,
        )
        return CommandResponse(**cmd.to_dict())
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.put("/user/{name}", response_model=CommandResponse)
async def update_user_command(name: str, request: UpdateCommandRequest):
    """Met a jour une commande utilisateur."""
    service = UserCommandsService.get_instance()
    cmd = service.update_command(
        name=name,
        description=request.description,
        category=request.category,
        icon=request.icon,
        show_on_home=request.show_on_home,
        content=request.content,
    )
    if not cmd:
        raise HTTPException(status_code=404, detail=f"Commande '{name}' introuvable")
    return CommandResponse(**cmd.to_dict())


@router.delete("/user/{name}")
async def delete_user_command(name: str):
    """Supprime une commande utilisateur."""
    service = UserCommandsService.get_instance()
    deleted = service.delete_command(name)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Commande '{name}' introuvable")
    return {"message": f"Commande '{name}' supprimee"}
