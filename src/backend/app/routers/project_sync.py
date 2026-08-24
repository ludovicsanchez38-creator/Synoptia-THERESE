"""Routes de project.sync (0.45) : racine, plan, apply, journal.

Le routeur est une peau fine : toute la logique vit dans
`services/project_sync_service.py` (design V2.1). Correspondance d'erreurs :
- ErreurRacine -> 400 (la demande est mauvaise) ;
- racine non rattachée -> 404 ;
- ErreurDeScan -> 422 fail-closed avec cause lisible, JAMAIS un plan partiel ;
- OperationRefusee -> 409 (apply en cours, plan caduc ou non-dernier).
"""
import logging

from app.services import project_sync_service as svc
from app.services.project_sync import ErreurDeScan
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter()


class RacineRequest(BaseModel):
    chemin: str


class ApplyRequest(BaseModel):
    plan_id: str


def _plan_en_dict(plan, operations=None) -> dict:
    corps = {
        "id": plan.id,
        "etat": plan.etat,
        "generation_racine": plan.generation_racine,
        "nb_indexer": plan.nb_indexer,
        "nb_reindexer": plan.nb_reindexer,
        "nb_retirer": plan.nb_retirer,
        "nb_conflits": plan.nb_conflits,
        "nb_inchanges": plan.nb_inchanges,
        "created_at": plan.created_at.isoformat(),
    }
    if operations is not None:
        corps["operations"] = [_operation_en_dict(o) for o in operations]
    return corps


def _operation_en_dict(operation) -> dict:
    return {
        "id": operation.id,
        "type": operation.type,
        "chemin": operation.chemin,
        "etat": operation.etat,
        "erreur": operation.erreur,
        "attempt_count": operation.attempt_count,
        "last_attempt_at": (
            operation.last_attempt_at.isoformat()
            if operation.last_attempt_at else None
        ),
    }


@router.put("/{project_id}/sync/racine")
async def definir_racine(project_id: str, request: RacineRequest) -> dict:
    try:
        root = await svc.definir_racine(project_id, request.chemin)
    except svc.ErreurRacine as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {
        "racine": root.racine,
        "generation": root.generation,
    }


@router.delete("/{project_id}/sync/racine")
async def retirer_racine(project_id: str) -> dict:
    """Délie la racine. Ne retire RIEN de l'index : ça, c'est un plan."""
    await svc.retirer_racine(project_id)
    return {"deliee": True}


@router.post("/{project_id}/sync/plan")
async def preparer_plan(project_id: str) -> dict:
    try:
        plan = await svc.preparer_plan(project_id)
    except svc.ErreurRacine as e:
        raise HTTPException(status_code=404, detail=str(e))
    except svc.OperationRefusee as e:
        raise HTTPException(status_code=409, detail=str(e))
    except ErreurDeScan as e:
        raise HTTPException(
            status_code=422,
            detail=f"Aucun plan produit : {e}",
        )
    operations = await svc.lire_operations(plan.id)
    return _plan_en_dict(plan, operations)


@router.post("/{project_id}/sync/apply", status_code=202)
async def appliquer(project_id: str, request: ApplyRequest) -> dict:
    # Refus AVANT de lancer la tâche de fond : un 202 ne doit jamais couvrir
    # un plan caduc ou un apply déjà en cours.
    plan = await svc.lire_plan(request.plan_id)
    if plan is None or plan.project_id != project_id:
        raise HTTPException(status_code=404, detail="Plan inconnu pour ce projet.")
    from app.models.entities_sync import EtatPlan

    if plan.etat not in (
        EtatPlan.PROPOSE, EtatPlan.EN_COURS, EtatPlan.APPLIQUE_PARTIEL
    ):
        raise HTTPException(
            status_code=409, detail=f"Ce plan n'est plus applicable ({plan.etat})."
        )
    if svc._verrou(project_id).locked():
        raise HTTPException(
            status_code=409, detail="Une synchronisation est déjà en cours."
        )

    svc.lancer_apply(project_id, request.plan_id)
    return {"lance": True, "plan_id": request.plan_id}


@router.get("/{project_id}/sync")
async def etat(project_id: str) -> dict:
    etat_courant = await svc.etat_sync(project_id)
    plan = etat_courant["dernier_plan"]
    return {
        "racine": etat_courant["racine"],
        "generation": etat_courant["generation"],
        "dernier_plan": _plan_en_dict(plan) if plan else None,
    }


@router.get("/{project_id}/sync/journal")
async def journal(project_id: str, page: int = 0) -> dict:
    etat_courant = await svc.etat_sync(project_id)
    plan = etat_courant["dernier_plan"]
    if plan is None:
        return {"operations": [], "page": page}
    operations = await svc.lire_operations(plan.id)
    operations.sort(key=lambda o: o.created_at, reverse=True)
    taille = 50
    tranche = operations[page * taille:(page + 1) * taille]
    return {
        "operations": [_operation_en_dict(o) for o in tranche],
        "page": page,
        "total": len(operations),
    }
