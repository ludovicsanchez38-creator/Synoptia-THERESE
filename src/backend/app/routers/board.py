"""
THÉRÈSE v2 - Board de Décision - Router

API endpoints pour le board de décision stratégique.
"""

import json
import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.board import (
    AdvisorRole,
    AdvisorInfo,
    BoardRequest,
    BoardDecisionResponse,
    ADVISOR_CONFIG,
)
from app.models.database import get_session, get_session_context
from app.services.board import BoardService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/advisors", response_model=list[AdvisorInfo])
async def list_advisors():
    """
    Liste tous les conseillers disponibles.

    Returns:
        Liste des conseillers avec leurs métadonnées
    """
    return [
        AdvisorInfo(
            role=role,
            name=config["name"],
            emoji=config["emoji"],
            color=config["color"],
            personality=config["personality"],
        )
        for role, config in ADVISOR_CONFIG.items()
    ]


@router.get("/advisors/{role}", response_model=AdvisorInfo)
async def get_advisor(role: AdvisorRole):
    """
    Récupère les informations d'un conseiller.

    Args:
        role: Rôle du conseiller

    Returns:
        Informations sur le conseiller
    """
    if role not in ADVISOR_CONFIG:
        raise HTTPException(status_code=404, detail="Advisor not found")

    config = ADVISOR_CONFIG[role]
    return AdvisorInfo(
        role=role,
        name=config["name"],
        emoji=config["emoji"],
        color=config["color"],
        personality=config["personality"],
    )


@router.post("/deliberate")
async def deliberate(
    request: BoardRequest,
):
    """
    Lance une délibération du board en streaming SSE.

    Le board consulte chaque conseiller puis génère une synthèse.

    Flow:
    1. Pour chaque conseiller:
       - advisor_start: Début de la consultation
       - advisor_chunk: Chunks de texte en streaming
       - advisor_done: Fin de la consultation
    2. synthesis_start: Début de la synthèse
    3. synthesis_chunk: Synthèse en JSON
    4. done: ID de la décision sauvegardée

    Args:
        request: Question et contexte

    Returns:
        Stream SSE avec les avis et la synthèse
    """

    async def generate():
        # Create session inside generator to keep it alive during streaming
        async with get_session_context() as session:
            board_service = BoardService(session)
            try:
                async for chunk in board_service.deliberate(request):
                    data = chunk.model_dump()
                    yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
            except Exception as e:
                logger.exception("Board deliberation error")
                error_data = {"type": "error", "content": str(e)}
                yield f"data: {json.dumps(error_data)}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/decisions", response_model=list[BoardDecisionResponse])
async def list_decisions(
    limit: int = Query(default=50, ge=1, le=200),
    session: AsyncSession = Depends(get_session),
):
    """
    Liste les décisions passées.

    Args:
        limit: Nombre maximum de décisions à retourner

    Returns:
        Liste des décisions
    """
    board_service = BoardService(session)
    decisions = await board_service.list_decisions(limit=limit)

    return [
        BoardDecisionResponse(
            id=d.id,
            question=d.question,
            context=d.context,
            recommendation=d.synthesis.recommendation,
            confidence=d.synthesis.confidence,
            created_at=d.created_at,
        )
        for d in decisions
    ]


@router.get("/decisions/{decision_id}")
async def get_decision(
    decision_id: str,
    session: AsyncSession = Depends(get_session),
):
    """
    Récupère une décision complète.

    Args:
        decision_id: ID de la décision

    Returns:
        La décision avec tous les avis et la synthèse
    """
    board_service = BoardService(session)
    decision = await board_service.get_decision(decision_id)

    if not decision:
        raise HTTPException(status_code=404, detail="Decision not found")

    return decision.model_dump()


@router.delete("/decisions/{decision_id}")
async def delete_decision(
    decision_id: str,
    session: AsyncSession = Depends(get_session),
):
    """
    Supprime une décision.

    Args:
        decision_id: ID de la décision

    Returns:
        Confirmation de suppression
    """
    board_service = BoardService(session)
    deleted = await board_service.delete_decision(decision_id)

    if not deleted:
        raise HTTPException(status_code=404, detail="Decision not found")

    return {"deleted": True, "id": decision_id}
