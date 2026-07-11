"""
THÉRÈSE v2 - Variables Router (chantier 4 Variables V1, design V4 11/07/2026).

CRUD des variables utilisateur. Sémantique anti-destruction : POST refuse
d'écraser (409), PUT remplace explicitement. La validation métier (noms,
bornes, invariant kind/value, filtre sécurité des valeurs) vit dans
variables_service - point unique partagé avec les actions du chat.
"""

import logging

from app.models.database import get_session
from app.models.entities import Variable
from app.services.variables_service import (
    VariableError,
    create_variable,
    delete_variable,
    get_variable,
    list_variables,
    replace_variable,
)
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlmodel.ext.asyncio.session import AsyncSession

logger = logging.getLogger(__name__)
router = APIRouter()


class VariableCreateBody(BaseModel):
    name: str = Field(max_length=64)
    kind: str = Field(default="text")
    value: str | list[str] = ""
    description: str | None = Field(default=None, max_length=300)


class VariableReplaceBody(BaseModel):
    value: str | list[str]


class VariableResponse(BaseModel):
    name: str
    kind: str
    value: str | list[str]
    description: str | None = None
    updated_at: str


def _to_response(variable: Variable) -> VariableResponse:
    return VariableResponse(
        name=variable.name,
        kind=variable.kind,
        value=variable.parsed_value,
        description=variable.description,
        updated_at=variable.updated_at.isoformat(),
    )


@router.get("", response_model=list[VariableResponse])
async def list_all(
    session: AsyncSession = Depends(get_session),
) -> list[VariableResponse]:
    return [_to_response(v) for v in await list_variables(session)]


@router.post("", response_model=VariableResponse)
async def create(
    body: VariableCreateBody,
    session: AsyncSession = Depends(get_session),
) -> VariableResponse:
    try:
        variable = await create_variable(
            session, body.name, body.kind, body.value, body.description
        )
    except VariableError as e:
        status = 409 if "existe déjà" in str(e) else 422
        raise HTTPException(status_code=status, detail=str(e)) from e
    return _to_response(variable)


@router.put("/{name}", response_model=VariableResponse)
async def replace(
    name: str,
    body: VariableReplaceBody,
    session: AsyncSession = Depends(get_session),
) -> VariableResponse:
    try:
        variable = await replace_variable(session, name, body.value)
    except VariableError as e:
        status = 404 if "existe pas" in str(e) else 422
        raise HTTPException(status_code=status, detail=str(e)) from e
    return _to_response(variable)


@router.delete("/{name}")
async def remove(
    name: str,
    session: AsyncSession = Depends(get_session),
) -> dict[str, str]:
    if await get_variable(session, name) is None:
        raise HTTPException(status_code=404, detail=f"Variable « {name} » introuvable.")
    try:
        await delete_variable(session, name)
    except VariableError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
    return {"status": "deleted", "name": name}


class PreviewBody(BaseModel):
    text: str = Field(max_length=100_000)


class PreviewResponse(BaseModel):
    resolved: str
    unknown: list[str]
    errors: list[str]
    variables_revision: str


@router.post("/preview", response_model=PreviewResponse)
async def preview(
    body: PreviewBody,
    session: AsyncSession = Depends(get_session),
) -> PreviewResponse:
    """Aperçu exact de la résolution (MÊME fonction que l'envoi, zéro effet
    de bord). Une erreur de borne est rapportée, pas levée : l'utilisateur
    la voit avant d'envoyer."""
    from app.services.variables_service import resolve_message, variables_revision

    errors: list[str] = []
    unknown: list[str] = []
    resolved = body.text
    try:
        resolved, unknown = await resolve_message(session, body.text)
    except VariableError as e:
        errors.append(str(e))
    return PreviewResponse(
        resolved=resolved,
        unknown=unknown,
        errors=errors,
        variables_revision=await variables_revision(session),
    )
