"""
Les prestations : ce que Ludo vend a quelqu'un (tranche C du 29/08).

Aucune extraction automatique depuis les notes. Une prestation nee d'un
analyseur qui choisit entre FORGER et PROPULSER, ce serait l'application qui
affirme une offre que personne n'a validee. Ludo les pose, ou elles n'existent
pas.
"""

from datetime import UTC, date, datetime
from typing import Any

from app.models.database import get_session
from app.models.entities import (
    PHASES_DE_PRESTATION,
    STATUTS_DE_FINANCEMENT,
    Contact,
    Prestation,
)
from app.services.echeances import echeance_de_suivi
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

router = APIRouter(prefix="/api/prestations", tags=["prestations"])

# Les phases vivent dans le domaine (`entities`), pas ici : le contrat de
# lecture des fiches les utilise aussi, et un routeur ne doit pas etre importe
# par un service.
PHASES = PHASES_DE_PRESTATION


class PrestationCreee(BaseModel):
    contact_id: str
    intitule: str
    montant_ht: float | None = None
    phase: str = "piste"
    financeur: str | None = None
    statut_financement: str | None = None
    fin_le: date | None = None


class PrestationModifiee(BaseModel):
    intitule: str | None = None
    montant_ht: float | None = None
    phase: str | None = None
    financeur: str | None = None
    statut_financement: str | None = None
    fin_le: date | None = None


def _rendre(p: Prestation) -> dict[str, Any]:
    return {
        "id": p.id,
        "contact_id": p.contact_id,
        "intitule": p.intitule,
        "montant_ht": p.montant_ht,
        "phase": p.phase,
        "financeur": p.financeur,
        "statut_financement": p.statut_financement,
        "fin_le": p.fin_le.isoformat() if p.fin_le else None,
        # DEDUITE de la fin, jamais saisie deux fois : deux champs pour un
        # fait, c'est deux occasions de diverger. Pour un organisme de
        # formation c'est le questionnaire a froid J+90 ; pour un garagiste,
        # un rappel apres reparation. Meme mecanique, delai reglable.
        "suivi_apres_fin_le": (
            echeance_de_suivi(p.fin_le).isoformat() if p.fin_le else None
        ),
        "created_at": p.created_at.isoformat(),
        "updated_at": p.updated_at.isoformat(),
    }


def _verifier_le_financement(statut: str | None, financeur: str | None) -> None:
    """Un statut sans financeur ne dit rien : « depose » chez qui ?"""
    if statut is None:
        return
    if statut not in STATUTS_DE_FINANCEMENT:
        raise HTTPException(
            status_code=400,
            detail=f"statut_financement doit valoir l'un de : {', '.join(STATUTS_DE_FINANCEMENT)}",
        )
    if not (financeur or "").strip():
        raise HTTPException(
            status_code=400,
            detail="Un statut de financement exige de nommer le financeur",
        )


def _verifier_la_phase(phase: str | None) -> None:
    if phase is not None and phase not in PHASES:
        raise HTTPException(
            status_code=400,
            detail=f"phase doit valoir l'une de : {', '.join(PHASES)}",
        )


@router.get("")
@router.get("/")
async def lister(
    contact_id: str | None = Query(None, description="Filtrer par contact"),
    phase: str | None = Query(None, description="Filtrer par phase"),
    session: AsyncSession = Depends(get_session),
) -> list[dict[str, Any]]:
    """Les prestations, par personne. Pas de Kanban : une liste."""
    requete = select(Prestation)
    if contact_id:
        requete = requete.where(Prestation.contact_id == contact_id)
    if phase:
        requete = requete.where(Prestation.phase == phase)
    resultat = await session.execute(requete.order_by(Prestation.created_at.desc()))
    return [_rendre(p) for p in resultat.scalars().all()]


@router.post("", status_code=201)
@router.post("/", status_code=201)
async def creer(
    request: PrestationCreee,
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    _verifier_la_phase(request.phase)
    _verifier_le_financement(request.statut_financement, request.financeur)
    if not (request.intitule or "").strip():
        raise HTTPException(status_code=400, detail="Une prestation a besoin d'un intitule")
    if await session.get(Contact, request.contact_id) is None:
        raise HTTPException(status_code=404, detail="Contact introuvable")

    p = Prestation(
        contact_id=request.contact_id,
        intitule=request.intitule.strip(),
        montant_ht=request.montant_ht,
        phase=request.phase,
        financeur=request.financeur,
        statut_financement=request.statut_financement,
        fin_le=request.fin_le,
    )
    session.add(p)
    await session.commit()
    await session.refresh(p)
    return _rendre(p)


@router.patch("/{prestation_id}")
async def modifier(
    prestation_id: str,
    request: PrestationModifiee,
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    _verifier_la_phase(request.phase)
    p = await session.get(Prestation, prestation_id)
    if p is None:
        raise HTTPException(status_code=404, detail="Prestation introuvable")

    modifs = request.model_dump(exclude_unset=True)
    # Le financeur peut deja etre pose : on valide l'etat APRES fusion, sinon
    # renseigner le seul statut serait refuse a tort.
    _verifier_le_financement(
        modifs.get("statut_financement", p.statut_financement),
        modifs.get("financeur", p.financeur),
    )
    for champ, valeur in modifs.items():
        setattr(p, champ, valeur)
    p.updated_at = datetime.now(UTC)
    session.add(p)
    await session.commit()
    await session.refresh(p)
    return _rendre(p)


@router.delete("/{prestation_id}")
async def supprimer(
    prestation_id: str,
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    p = await session.get(Prestation, prestation_id)
    if p is None:
        raise HTTPException(status_code=404, detail="Prestation introuvable")
    await session.delete(p)
    await session.commit()
    return {"supprimee": prestation_id}
