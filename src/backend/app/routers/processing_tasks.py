"""Routes des traitements longs (0.46).

`/api/processing-tasks`, PAS `/api/tasks` : « tâches » est pris par les
todos métier (challenge de design, finding bloquant n°1).
"""
import logging
from typing import Any

from app.models.processing import EtatTache
from app.services import traitements
from fastapi import APIRouter, HTTPException

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("")
async def lister(actives: bool | None = None, limit: int = 50) -> dict[str, Any]:
    return {"traitements": await traitements.lister(actives=actives, limit=limit)}


@router.post("/{task_id}/cancel")
async def annuler(task_id: str) -> dict[str, Any]:
    resultat = await traitements.demander_arret(task_id)
    if resultat is None:
        raise HTTPException(status_code=404, detail="Traitement inconnu.")
    if resultat.state in EtatTache.terminaux() and resultat.resultat == "unavailable":
        raise HTTPException(
            status_code=409, detail=f"Ce traitement est déjà terminé ({resultat.state})."
        )
    return {
        "state": resultat.state,
        "resultat": resultat.resultat,
        "transmise": resultat.transmise,
    }
