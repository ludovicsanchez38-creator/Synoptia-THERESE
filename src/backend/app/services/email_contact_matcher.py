"""
THERESE v2 - Email-Contact Matcher

Auto-associe les emails aux contacts CRM par adresse email.
"""

import logging

from app.models.entities import Contact
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

logger = logging.getLogger(__name__)


async def match_email_to_contact(
    email_address: str,
    session: AsyncSession,
) -> str | None:
    """
    Cherche un contact CRM par adresse email.

    Args:
        email_address: Adresse email à rechercher.
        session: Session de base de données.

    Returns:
        L'ID du contact trouvé, ou None si aucun match.
    """
    if not email_address:
        return None

    email_lower = email_address.lower().strip()

    statement = select(Contact).where(Contact.email == email_lower)
    result = await session.execute(statement)
    contact = result.scalar_one_or_none()

    if contact:
        logger.debug("Email %s matched to contact %s", email_lower, contact.id)
        return contact.id

    return None
