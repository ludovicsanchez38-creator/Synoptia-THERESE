"""
THÉRÈSE v2 - Scoring Service

Système de scoring prospects/clients.
Phase 5 - CRM Features
"""

import logging
from datetime import UTC, datetime

from app.models.entities import Activity, Contact
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

# Scoring rules (inspiré synoptia-erp-clean)
SCORING_RULES = {
    "base": 50,
    "email": 20,
    "phone": 15,
    "company": 10,
    "source_referral": 25,
    "source_website": 15,
    "source_linkedin": 20,
    "interaction_meeting": 25,
    "interaction_call": 15,
    "interaction_email": 10,
    "decay_30days": -5,  # Si inactif 30 jours
}

STAGE_SCORES = {
    "contact": 0,  # Nouveau lead, score de base
    "discovery": 10,  # Premier échange
    "proposition": 20,  # Offre envoyée
    "signature": 30,  # En attente signature
    "delivery": 40,  # Projet en cours
    "active": 50,  # Client actif
    "archive": -100,  # Perdu ou terminé
}


def calculate_base_score(contact: Contact) -> int:
    """
    Calcule le score de base d'un contact.

    Args:
        contact: Contact entity

    Returns:
        Score calculé
    """
    score = SCORING_RULES["base"]

    # Email fourni
    if contact.email:
        score += SCORING_RULES["email"]

    # Téléphone fourni
    if contact.phone:
        score += SCORING_RULES["phone"]

    # Entreprise fournie
    if contact.company:
        score += SCORING_RULES["company"]

    # Source
    if contact.source:
        source_key = f"source_{contact.source.lower()}"
        if source_key in SCORING_RULES:
            score += SCORING_RULES[source_key]

    # Stage
    if contact.stage in STAGE_SCORES:
        score += STAGE_SCORES[contact.stage]

    # Decay si inactif
    if contact.last_interaction:
        last = contact.last_interaction
        if last.tzinfo is None:
            last = last.replace(tzinfo=UTC)
        days_inactive = (datetime.now(UTC) - last).days
        if days_inactive >= 30:
            # -5 points tous les 30 jours
            decay_count = days_inactive // 30
            score += SCORING_RULES["decay_30days"] * decay_count

    return max(0, score)  # Minimum 0


async def update_contact_score(session: AsyncSession, contact: Contact, reason: str = "recalculation") -> dict:
    """
    Met à jour le score d'un contact et crée une activité.

    Args:
        session: AsyncSession
        contact: Contact entity
        reason: Raison de la mise à jour

    Returns:
        Dict avec old_score, new_score, reason
    """
    old_score = contact.score
    new_score = calculate_base_score(contact)

    if old_score != new_score:
        contact.score = new_score
        contact.updated_at = datetime.now(UTC)
        session.add(contact)

        # Créer une activité
        activity = Activity(
            contact_id=contact.id,
            type="score_change",
            title=f"Score: {old_score} → {new_score}",
            description=f"Raison: {reason}",
            extra_data=f'{{"old_score": {old_score}, "new_score": {new_score}, "reason": "{reason}"}}',
        )
        session.add(activity)

        logger.info(f"Contact {contact.id} score updated: {old_score} → {new_score} ({reason})")

    return {
        "contact_id": contact.id,
        "old_score": old_score,
        "new_score": new_score,
        "reason": reason,
    }


async def recalculate_all_scores(session: AsyncSession) -> int:
    """
    Recalcule tous les scores de tous les contacts.

    Utile pour migration ou correction.

    Args:
        session: AsyncSession

    Returns:
        Nombre de contacts mis à jour
    """
    statement = select(Contact)
    result = await session.execute(statement)
    contacts = result.scalars().all()

    updated_count = 0

    for contact in contacts:
        score_result = await update_contact_score(session, contact, reason="batch_recalculation")
        if score_result["old_score"] != score_result["new_score"]:
            updated_count += 1

    await session.commit()

    logger.info(f"Recalculated scores for {updated_count}/{len(contacts)} contacts")

    return updated_count
