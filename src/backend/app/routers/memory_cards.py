"""Gestion locale des fiches ; aucune création manuelle dans l'écran."""
from typing import Any, Literal

from app.models.database import get_session_context
from app.models.entities import Contact, MemoryCard, Project
from app.services import memory_cards as service
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from sqlmodel import select

router = APIRouter(prefix='/cards', tags=['mémoire'])


class Version(BaseModel):
    version: int = Field(ge=1)


class Correction(Version):
    title: str | None = Field(default=None, min_length=1, max_length=120)
    content: str | None = Field(default=None, min_length=1, max_length=1200)
    reason: str | None = Field(default=None, max_length=600)
    kind: Literal['preference', 'fait', 'decision', 'correction'] | None = None
    state: Literal['active', 'archivee'] | None = None


async def presenter_localement(session: Any, f: MemoryCard) -> dict[str, Any]:
    resultat = service.presenter(f)
    projet = await session.get(Project, f.scope_id or f.project_id) if f.scope_id or f.project_id else None
    contact = await session.get(Contact, f.contact_id) if f.contact_id else None
    return resultat | {'scope_name': projet.name if projet else 'Général',
                       'contact_name': contact.display_name if contact else None,
                       'source_deleted': f.author == 'therese' and not (f.message_id and f.conversation_id)}


@router.get('')
async def lister(query: str = '', kind: Literal['preference', 'fait', 'decision', 'correction'] | None = None,
                 state: Literal['active', 'archivee'] = 'active',
                 scope: Literal['global', 'project'] | None = None, scope_id: str | None = None,
                 offset: int = Query(default=0, ge=0), limit: int = Query(default=25, ge=1, le=100)) -> dict[str, Any]:
    resultat = await service.lister(query=query, kind=kind, state=state, scope=scope,
                                    scope_id=scope_id, offset=offset, limit=limit)
    async with get_session_context() as session:
        resultat['items'] = [await presenter_localement(session, f) for identifiant in [f['id'] for f in resultat['items']]
                             if (f := await session.get(MemoryCard, identifiant)) is not None]
    return resultat


@router.get('/scopes')
async def portees() -> list[dict[str, str]]:
    async with get_session_context() as session:
        projets = (await session.execute(select(Project).order_by(Project.name))).scalars().all()
        return [{'id': p.id, 'name': p.name} for p in projets]


@router.get('/{card_id}')
async def lire(card_id: str) -> dict[str, Any]:
    async with get_session_context() as session:
        fiche = await session.get(MemoryCard, card_id)
        if not fiche:
            raise HTTPException(404, 'Fiche effacée')
        return await presenter_localement(session, fiche)


@router.patch('/{card_id}')
async def corriger(card_id: str, correction: Correction) -> dict[str, Any]:
    try:
        await service.ecrire(correction.model_dump(exclude_unset=True) | {'id': card_id})
    except service.RefusMemoire as refus:
        raise HTTPException(refus.status, str(refus)) from None
    return await lire(card_id)


@router.post('/{card_id}/release')
async def rendre_la_main(card_id: str, version: Version) -> dict[str, Any]:
    try:
        await service.rendre_la_main(card_id, version.version)
    except service.RefusMemoire as refus:
        raise HTTPException(refus.status, str(refus)) from None
    return await lire(card_id)


@router.delete('/{card_id}')
async def effacer(card_id: str, version: int = Query(ge=1)) -> dict[str, bool]:
    try:
        await service.effacer(card_id, version)
    except service.RefusMemoire as refus:
        raise HTTPException(refus.status, str(refus)) from None
    return {'success': True}
