"""
THERESE v2 - User Commands Router

Endpoints CRUD pour les commandes utilisateur personnalisees.
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.user_commands import UserCommandsService

logger = logging.getLogger(__name__)
router = APIRouter()


# --- Schemas ---

class CreateCommandRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=50, description="Slug de la commande")
    description: str = Field("", max_length=200)
    category: str = Field("general", max_length=50)
    icon: str = Field("", max_length=10)
    show_on_home: bool = False
    content: str = Field("", description="Contenu/prompt de la commande")


class UpdateCommandRequest(BaseModel):
    description: Optional[str] = None
    category: Optional[str] = None
    icon: Optional[str] = None
    show_on_home: Optional[bool] = None
    content: Optional[str] = None


class CommandResponse(BaseModel):
    name: str
    description: str
    category: str
    icon: str
    show_on_home: bool
    content: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


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
