"""
THÉRÈSE v2 - Board de Décision - Router

API endpoints pour le board de décision stratégique.
"""

import asyncio
import json
import logging
from collections.abc import AsyncIterator, Awaitable, Callable

from app.models.board import (
    ADVISOR_CONFIG,
    AdvisorInfo,
    AdvisorRole,
    BoardDecisionResponse,
    BoardDeliberationChunk,
    BoardRequest,
)
from app.models.database import get_session, get_session_context
from app.services.board import BoardService
from app.services.traitements import TraitementHandle
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

# Second panel de revue : les nettoyages après déconnexion partent dans des
# tâches DÉTACHÉES (l'annulation level-triggered d'anyio coupe tout await
# du bloc except du générateur). Référence forte obligatoire.
_nettoyages_en_cours: set["asyncio.Task[None]"] = set()

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


async def _clore_apres_deconnexion(
    porteur: "asyncio.Task[None]",
    board_service: BoardService,
    handle: TraitementHandle | None,
    decision_sauvee: "Callable[[], Awaitable[bool]]",
) -> None:
    """Clôture d'une délibération dont le client a disparu - exécutée hors
    du scope annulé : attend la fin réelle du porteur ET de la persistance
    protégée avant de trancher done/cancelled."""
    from app.models.processing import EtatTache

    await asyncio.gather(porteur, return_exceptions=True)
    persistance = board_service._persistance_en_cours
    if persistance is not None:
        await asyncio.gather(persistance, return_exceptions=True)
    if handle is None:
        return
    try:
        if await decision_sauvee():
            await handle.terminer(EtatTache.DONE)
        else:
            await handle.terminer(EtatTache.CANCELLED)
    except Exception:
        logger.warning(
            "Clôture après déconnexion impossible pour le Board",
            exc_info=True,
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

    from uuid import uuid4

    from app.models.processing import EtatTache
    from app.services import task_registry, traitements

    # 0.47 : le decision_id est préalloué ICI - entity_id du traitement posé
    # dès la création, pas de rattachement après coup.
    decision_id = str(uuid4())
    handle = None
    try:
        handle = await traitements.creer_traitement(
            type="board",
            label=request.question[:80],
            entity_id=decision_id,
        )
    except Exception:
        logger.warning(
            "Suivi indisponible pour la délibération du Board", exc_info=True
        )

    def _sse(data: dict[str, object]) -> str:
        return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"

    async def _decision_sauvee() -> bool:
        from app.models.entities import BoardDecisionDB
        from sqlmodel import select

        async with get_session_context() as session:
            resultat = await session.execute(
                select(BoardDecisionDB).where(BoardDecisionDB.id == decision_id)
            )
            return resultat.scalars().first() is not None

    async def generate() -> AsyncIterator[str]:
        # La garantie d'arrêt GLOBALE vient de l'annulation de la tâche
        # PORTEUSE : le finally du service ne couvre que la branche cloud
        # parallèle (ni recherche web, ni mode souverain, ni synthèse).
        file_evenements: asyncio.Queue[BoardDeliberationChunk | None] = (
            asyncio.Queue()
        )

        async with get_session_context() as session:
            board_service = BoardService(session)

            async def porteur() -> None:
                try:
                    async for chunk in board_service.deliberate(
                        request,
                        decision_id=decision_id,
                        annulation_demandee=(
                            handle.annulation_demandee if handle else None
                        ),
                    ):
                        await file_evenements.put(chunk)
                finally:
                    file_evenements.put_nowait(None)

            tache = asyncio.create_task(porteur())

            if handle is not None:
                try:
                    await handle.demarrer()
                    await handle.lier_adaptateur(
                        task_registry.AnnulationParTacheAsyncio(tache)
                    )
                except traitements.AnnuleAvantDemarrage:
                    # demander_arret a déjà posé CANCELLED durable.
                    tache.cancel()
                    await asyncio.gather(tache, return_exceptions=True)
                    yield _sse({"type": "cancelled", "content": ""})
                    return
                except Exception as e:
                    tache.cancel()
                    await asyncio.gather(tache, return_exceptions=True)
                    await handle.terminer(EtatTache.FAILED, error=str(e)[:200])
                    yield _sse({"type": "error", "content": str(e)})
                    return

            # Premier événement : l'identité du traitement - sans elle,
            # aucun bouton Annuler ne peut viser le chemin canonique.
            yield _sse({"type": "task", "content": handle.id if handle else ""})

            try:
                while True:
                    chunk = await file_evenements.get()
                    if chunk is None:
                        break
                    yield _sse(chunk.model_dump())
                await asyncio.gather(tache, return_exceptions=True)

                if tache.cancelled():
                    # Revue jalon (F3) : attendre la persistance PROTÉGÉE
                    # avant de trancher - un commit lent sous shield aboutit
                    # après l'annulation de la porteuse.
                    persistance = board_service._persistance_en_cours
                    if persistance is not None:
                        await asyncio.gather(
                            persistance, return_exceptions=True
                        )
                    if await _decision_sauvee():
                        # Le commit a gagné la course : la décision existe,
                        # un cancel_requested tardif se résout en done
                        # (contrat 0.46) - et le client doit l'apprendre.
                        if handle is not None:
                            await handle.terminer(EtatTache.DONE)
                        yield _sse({"type": "done", "content": decision_id})
                    else:
                        if handle is not None:
                            await handle.terminer(EtatTache.CANCELLED)
                        yield _sse({"type": "cancelled", "content": ""})
                elif tache.exception() is not None:
                    erreur = tache.exception()
                    logger.error("Board deliberation error", exc_info=erreur)
                    if await _decision_sauvee():
                        # Passe 3 (P3-7) : le commit a abouti avant la panne
                        # (ex. vérification en échec) - done gagne, le
                        # client doit apprendre que sa décision existe.
                        if handle is not None:
                            await handle.terminer(EtatTache.DONE)
                        yield _sse({"type": "done", "content": decision_id})
                    else:
                        if handle is not None:
                            await handle.terminer(
                                EtatTache.FAILED, error=str(erreur)[:200]
                            )
                        yield _sse({"type": "error", "content": str(erreur)})
                else:
                    if handle is not None:
                        await handle.progresser(progress=1.0)
                        await handle.terminer(EtatTache.DONE)
            except (GeneratorExit, asyncio.CancelledError):
                # Déconnexion du client : pas de partiel - une décision à
                # moitié délibérée ne se sauve pas. Si le commit avait déjà
                # eu lieu, done reste la vérité.
                #
                # Second panel de revue : sous uvicorn/Starlette, cette
                # annulation est LEVEL-TRIGGERED (re-livrée à chaque await
                # de ce bloc). Tout nettoyage attendu ICI serait coupé et
                # la ligne resterait running à jamais : il part donc dans
                # une tâche détachée, insensible au scope annulé.
                tache.cancel()
                nettoyage = asyncio.create_task(
                    _clore_apres_deconnexion(
                        tache, board_service, handle, _decision_sauvee
                    )
                )
                _nettoyages_en_cours.add(nettoyage)
                nettoyage.add_done_callback(_nettoyages_en_cours.discard)
                raise

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
            mode=d.mode,
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
