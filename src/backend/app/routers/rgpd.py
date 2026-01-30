"""
THÉRÈSE v2 - RGPD Router

Endpoints pour la conformité RGPD :
- Export des données (droit de portabilité)
- Anonymisation (droit à l'oubli)
- Renouvellement du consentement
- Statistiques RGPD
"""

import logging
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.database import get_session
from app.models.entities import Contact, Activity, Project, Task, Deliverable
from app.models.schemas import (
    RGPDExportResponse,
    RGPDAnonymizeRequest,
    RGPDAnonymizeResponse,
    RGPDRenewConsentResponse,
    RGPDStatsResponse,
    RGPDUpdateRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["rgpd"])


# ============================================================
# RGPD Export (Droit de portabilité - Art. 20)
# ============================================================


@router.get("/export/{contact_id}", response_model=RGPDExportResponse)
async def export_contact_data(
    contact_id: str,
    session: AsyncSession = Depends(get_session),
):
    """
    Exporte toutes les données d'un contact (droit de portabilité RGPD).

    Retourne un JSON avec :
    - Données du contact
    - Historique des activités
    - Projets associés
    - Tâches associées
    """
    # Get contact
    result = await session.execute(
        select(Contact).where(Contact.id == contact_id)
    )
    contact = result.scalar_one_or_none()

    if not contact:
        raise HTTPException(status_code=404, detail="Contact non trouvé")

    # Get activities
    result = await session.execute(
        select(Activity).where(Activity.contact_id == contact_id)
    )
    activities = result.scalars().all()

    # Get projects
    result = await session.execute(
        select(Project).where(Project.contact_id == contact_id)
    )
    projects = result.scalars().all()

    # Get tasks (via projects)
    project_ids = [p.id for p in projects]
    tasks = []
    if project_ids:
        result = await session.execute(
            select(Task).where(Task.project_id.in_(project_ids))
        )
        tasks = result.scalars().all()

    # Build export
    contact_data = {
        "id": contact.id,
        "first_name": contact.first_name,
        "last_name": contact.last_name,
        "company": contact.company,
        "email": contact.email,
        "phone": contact.phone,
        "notes": contact.notes,
        "tags": contact.tags,
        "stage": contact.stage,
        "score": contact.score,
        "source": contact.source,
        "created_at": contact.created_at.isoformat() if contact.created_at else None,
        "last_interaction": contact.last_interaction.isoformat() if contact.last_interaction else None,
        "rgpd_base_legale": contact.rgpd_base_legale,
        "rgpd_date_collecte": contact.rgpd_date_collecte.isoformat() if contact.rgpd_date_collecte else None,
        "rgpd_date_expiration": contact.rgpd_date_expiration.isoformat() if contact.rgpd_date_expiration else None,
        "rgpd_consentement": contact.rgpd_consentement,
    }

    activities_data = [
        {
            "id": a.id,
            "type": a.type,
            "title": a.title,
            "description": a.description,
            "created_at": a.created_at.isoformat() if a.created_at else None,
        }
        for a in activities
    ]

    projects_data = [
        {
            "id": p.id,
            "name": p.name,
            "description": p.description,
            "status": p.status,
            "budget": p.budget,
            "created_at": p.created_at.isoformat() if p.created_at else None,
        }
        for p in projects
    ]

    tasks_data = [
        {
            "id": t.id,
            "title": t.title,
            "description": t.description,
            "status": t.status,
            "priority": t.priority,
            "due_date": t.due_date.isoformat() if t.due_date else None,
            "created_at": t.created_at.isoformat() if t.created_at else None,
        }
        for t in tasks
    ]

    logger.info(f"RGPD export for contact {contact_id}")

    return RGPDExportResponse(
        contact=contact_data,
        activities=activities_data,
        projects=projects_data,
        tasks=tasks_data,
        exported_at=datetime.utcnow(),
    )


# ============================================================
# RGPD Anonymisation (Droit à l'oubli - Art. 17)
# ============================================================


@router.post("/anonymize/{contact_id}", response_model=RGPDAnonymizeResponse)
async def anonymize_contact(
    contact_id: str,
    request: RGPDAnonymizeRequest,
    session: AsyncSession = Depends(get_session),
):
    """
    Anonymise un contact (droit à l'oubli RGPD).

    - Remplace les données personnelles par [ANONYMISÉ]
    - Supprime email, téléphone
    - Passe le stage en "archive"
    - Supprime les activités et tâches liées
    - Log l'action avec la raison
    """
    result = await session.execute(
        select(Contact).where(Contact.id == contact_id)
    )
    contact = result.scalar_one_or_none()

    if not contact:
        raise HTTPException(status_code=404, detail="Contact non trouvé")

    old_name = f"{contact.first_name or ''} {contact.last_name or ''}".strip()

    # Anonymize contact data
    contact.first_name = "[ANONYMISÉ]"
    contact.last_name = None
    contact.email = None
    contact.phone = None
    contact.notes = None
    contact.tags = None
    contact.company = "[ANONYMISÉ]"
    contact.stage = "archive"
    contact.extra_data = None
    contact.updated_at = datetime.utcnow()

    # Delete activities
    result = await session.execute(
        select(Activity).where(Activity.contact_id == contact_id)
    )
    activities = result.scalars().all()
    for activity in activities:
        await session.delete(activity)

    # Delete tasks and projects linked to contact
    result = await session.execute(
        select(Project).where(Project.contact_id == contact_id)
    )
    projects = result.scalars().all()
    for project in projects:
        # Delete tasks of this project
        result = await session.execute(
            select(Task).where(Task.project_id == project.id)
        )
        tasks = result.scalars().all()
        for task in tasks:
            await session.delete(task)
        # Delete deliverables of this project
        result = await session.execute(
            select(Deliverable).where(Deliverable.project_id == project.id)
        )
        deliverables = result.scalars().all()
        for deliv in deliverables:
            await session.delete(deliv)
        # Delete project
        await session.delete(project)

    # Log anonymization activity
    anonymization_log = Activity(
        contact_id=contact_id,
        type="rgpd_anonymization",
        title="Contact anonymisé",
        description=f"Raison: {request.reason}. Ancien nom: {old_name}",
    )
    session.add(anonymization_log)

    await session.commit()

    logger.info(f"RGPD anonymization for contact {contact_id}: {request.reason}")

    return RGPDAnonymizeResponse(
        success=True,
        message=f"Contact anonymisé avec succès. Raison: {request.reason}",
        contact_id=contact_id,
    )


# ============================================================
# RGPD Renouvellement Consentement
# ============================================================


@router.post("/renew-consent/{contact_id}", response_model=RGPDRenewConsentResponse)
async def renew_consent(
    contact_id: str,
    session: AsyncSession = Depends(get_session),
):
    """
    Renouvelle le consentement RGPD d'un contact.

    - Met à jour la date de collecte à aujourd'hui
    - Calcule nouvelle date d'expiration (+3 ans)
    - Passe rgpd_consentement à True
    - Définit la base légale comme "consentement"
    """
    result = await session.execute(
        select(Contact).where(Contact.id == contact_id)
    )
    contact = result.scalar_one_or_none()

    if not contact:
        raise HTTPException(status_code=404, detail="Contact non trouvé")

    now = datetime.utcnow()
    new_expiration = now + timedelta(days=3 * 365)  # 3 ans

    contact.rgpd_base_legale = "consentement"
    contact.rgpd_date_collecte = now
    contact.rgpd_date_expiration = new_expiration
    contact.rgpd_consentement = True
    contact.updated_at = now

    # Log activity
    activity = Activity(
        contact_id=contact_id,
        type="rgpd_consent_renewal",
        title="Consentement RGPD renouvelé",
        description=f"Nouvelle expiration: {new_expiration.strftime('%d/%m/%Y')}",
    )
    session.add(activity)

    await session.commit()

    logger.info(f"RGPD consent renewed for contact {contact_id}")

    return RGPDRenewConsentResponse(
        success=True,
        message="Consentement renouvelé avec succès",
        new_expiration=new_expiration,
    )


# ============================================================
# RGPD Update (mise à jour manuelle)
# ============================================================


@router.patch("/{contact_id}", response_model=dict)
async def update_rgpd_fields(
    contact_id: str,
    request: RGPDUpdateRequest,
    session: AsyncSession = Depends(get_session),
):
    """
    Met à jour les champs RGPD d'un contact.

    Permet de modifier :
    - La base légale
    - Le statut de consentement
    """
    result = await session.execute(
        select(Contact).where(Contact.id == contact_id)
    )
    contact = result.scalar_one_or_none()

    if not contact:
        raise HTTPException(status_code=404, detail="Contact non trouvé")

    if request.rgpd_base_legale is not None:
        valid_bases = ["consentement", "contrat", "interet_legitime", "obligation_legale"]
        if request.rgpd_base_legale not in valid_bases:
            raise HTTPException(
                status_code=400,
                detail=f"Base légale invalide. Valeurs acceptées: {valid_bases}"
            )
        contact.rgpd_base_legale = request.rgpd_base_legale

    if request.rgpd_consentement is not None:
        contact.rgpd_consentement = request.rgpd_consentement

    # Auto-set dates if not set
    if contact.rgpd_date_collecte is None:
        contact.rgpd_date_collecte = contact.created_at or datetime.utcnow()

    if contact.rgpd_date_expiration is None:
        base_date = contact.rgpd_date_collecte or datetime.utcnow()
        contact.rgpd_date_expiration = base_date + timedelta(days=3 * 365)

    contact.updated_at = datetime.utcnow()

    await session.commit()

    logger.info(f"RGPD fields updated for contact {contact_id}")

    return {"success": True, "message": "Champs RGPD mis à jour"}


# ============================================================
# RGPD Statistiques
# ============================================================


@router.get("/stats", response_model=RGPDStatsResponse)
async def get_rgpd_stats(
    session: AsyncSession = Depends(get_session),
):
    """
    Retourne les statistiques RGPD globales.

    - Total contacts
    - Répartition par base légale
    - Contacts sans info RGPD
    - Contacts expirés ou bientôt (30 jours)
    - Contacts avec consentement
    """
    result = await session.execute(select(Contact))
    contacts = result.scalars().all()

    total = len(contacts)
    par_base_legale = {
        "consentement": 0,
        "contrat": 0,
        "interet_legitime": 0,
        "obligation_legale": 0,
        "non_defini": 0,
    }
    sans_info = 0
    expires_ou_bientot = 0
    avec_consentement = 0

    now = datetime.utcnow()
    seuil_30j = now + timedelta(days=30)

    for contact in contacts:
        # Par base légale
        base = contact.rgpd_base_legale
        if base and base in par_base_legale:
            par_base_legale[base] += 1
        else:
            par_base_legale["non_defini"] += 1

        # Sans info RGPD
        if not contact.rgpd_base_legale and not contact.rgpd_date_collecte:
            sans_info += 1

        # Expirés ou bientôt
        if contact.rgpd_date_expiration:
            if contact.rgpd_date_expiration <= seuil_30j:
                expires_ou_bientot += 1

        # Avec consentement
        if contact.rgpd_consentement:
            avec_consentement += 1

    return RGPDStatsResponse(
        total_contacts=total,
        par_base_legale=par_base_legale,
        sans_info_rgpd=sans_info,
        expires_ou_bientot=expires_ou_bientot,
        avec_consentement=avec_consentement,
    )


# ============================================================
# RGPD Auto-inférence base légale
# ============================================================


@router.post("/infer/{contact_id}", response_model=dict)
async def infer_rgpd_base_legale(
    contact_id: str,
    session: AsyncSession = Depends(get_session),
):
    """
    Infère automatiquement la base légale RGPD d'un contact.

    Logique :
    - Clients actifs/signature/delivery → contrat
    - Prospects (contact/discovery/proposition) → intérêt légitime
    - Si consentement explicite → consentement
    """
    result = await session.execute(
        select(Contact).where(Contact.id == contact_id)
    )
    contact = result.scalar_one_or_none()

    if not contact:
        raise HTTPException(status_code=404, detail="Contact non trouvé")

    # Infer base légale
    if contact.rgpd_consentement:
        base_legale = "consentement"
    elif contact.stage in ["active", "signature", "delivery"]:
        base_legale = "contrat"
    else:
        base_legale = "interet_legitime"

    # Set dates if not set
    now = datetime.utcnow()
    if not contact.rgpd_date_collecte:
        contact.rgpd_date_collecte = contact.created_at or now

    # Expiration based on base légale
    if base_legale == "contrat":
        # Durée contrat + 5 ans (obligation comptable)
        expiration = contact.rgpd_date_collecte + timedelta(days=5 * 365)
    else:
        # Prospects: 3 ans après dernier contact
        expiration = contact.rgpd_date_collecte + timedelta(days=3 * 365)

    contact.rgpd_base_legale = base_legale
    contact.rgpd_date_expiration = expiration
    contact.updated_at = now

    await session.commit()

    logger.info(f"RGPD base légale inferred for contact {contact_id}: {base_legale}")

    return {
        "success": True,
        "base_legale": base_legale,
        "date_expiration": expiration.isoformat(),
    }
