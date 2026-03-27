"""
THÉRÈSE v2 - Service de purge RGPD automatique (US-017)

Anonymise automatiquement les contacts dont la dernière interaction
dépasse la durée de rétention configurée (défaut : 36 mois).

- 30 jours avant : notification de prévention
- Le jour J : anonymisation via l'endpoint existant
- Les contacts avec purge_excluded=True sont ignorés
"""

import logging
from datetime import UTC, datetime, timedelta

from app.models.database import get_session_context
from app.models.entities import Activity, Contact, Notification
from sqlmodel import select

logger = logging.getLogger(__name__)

# Durée de rétention par défaut (en mois)
DEFAULT_RETENTION_MONTHS = 36


async def _get_purge_retention_months() -> int:
    """Récupère la durée de rétention configurée (préférence utilisateur)."""
    try:
        from app.models.entities import Preference

        async with get_session_context() as session:
            result = await session.execute(
                select(Preference).where(Preference.key == "rgpd_purge_months")
            )
            pref = result.scalar_one_or_none()
            if pref and pref.value:
                months = int(pref.value)
                if 12 <= months <= 60:
                    return months
    except Exception as e:
        logger.debug(f"Préférence rgpd_purge_months non disponible: {e}")
    return DEFAULT_RETENTION_MONTHS


async def _is_purge_enabled() -> bool:
    """Vérifie si la purge automatique est activée."""
    try:
        from app.models.entities import Preference

        async with get_session_context() as session:
            result = await session.execute(
                select(Preference).where(Preference.key == "rgpd_purge_enabled")
            )
            pref = result.scalar_one_or_none()
            if pref and pref.value:
                return pref.value.lower() in ("true", "1", "yes")
    except Exception as e:
        logger.debug(f"Préférence rgpd_purge_enabled non disponible: {e}")
    # Par défaut activé
    return True


async def auto_purge_expired_contacts() -> dict[str, int]:
    """
    Purge automatique des contacts expirés.

    Logique :
    1. Contacts dont last_interaction (ou updated_at) > retention_months
    2. Exclure ceux avec purge_excluded=True
    3. 30 jours avant : créer une notification d'avertissement
    4. Le jour J : anonymiser le contact

    Retourne un dict avec le nombre de notifications et d'anonymisations.
    """
    if not await _is_purge_enabled():
        logger.debug("Purge RGPD automatique désactivée")
        return {"notifications": 0, "anonymisations": 0}

    retention_months = await _get_purge_retention_months()
    now = datetime.now(UTC)
    purge_threshold = now - timedelta(days=retention_months * 30)
    warning_threshold = now - timedelta(days=(retention_months * 30) - 30)

    results = {"notifications": 0, "anonymisations": 0}

    try:
        async with get_session_context() as session:
            # Récupérer tous les contacts potentiellement concernés
            result = await session.execute(
                select(Contact).where(
                    Contact.purge_excluded == False,  # noqa: E712
                    Contact.first_name != "[ANONYMISÉ]",  # Pas déjà anonymisés
                )
            )
            contacts = result.scalars().all()

            contacts_to_warn: list[Contact] = []
            contacts_to_purge: list[Contact] = []

            for contact in contacts:
                # Déterminer la date de référence
                ref_date = contact.last_interaction or contact.updated_at or contact.created_at
                if ref_date is None:
                    continue

                # Normaliser timezone
                if ref_date.tzinfo is None:
                    ref_date = ref_date.replace(tzinfo=UTC)

                if ref_date < purge_threshold:
                    contacts_to_purge.append(contact)
                elif ref_date < warning_threshold:
                    contacts_to_warn.append(contact)

            # Notifications d'avertissement (30 jours avant)
            for contact in contacts_to_warn:
                # Vérifier qu'on n'a pas déjà notifié récemment
                existing = await session.execute(
                    select(Notification).where(
                        Notification.source == "rgpd_purge",
                        Notification.action_url == f"/crm/contacts/{contact.id}",
                        Notification.created_at > now - timedelta(days=7),
                    )
                )
                if existing.scalar_one_or_none():
                    continue

                purge_date = (contact.last_interaction or contact.updated_at or contact.created_at)
                if purge_date:
                    purge_date_str = (purge_date + timedelta(days=retention_months * 30)).strftime("%d/%m/%Y")
                else:
                    purge_date_str = "bientôt"

                notif = Notification(
                    title="Purge RGPD programmée",
                    message=f"{contact.display_name} sera anonymisé le {purge_date_str}",
                    type="warning",
                    source="rgpd_purge",
                    action_url=f"/crm/contacts/{contact.id}",
                    action_label="Voir",
                )
                session.add(notif)
                results["notifications"] += 1

            # Anonymisation le jour J
            for contact in contacts_to_purge:
                # Vérifier qu'on n'a pas déjà notifié l'anonymisation
                existing = await session.execute(
                    select(Notification).where(
                        Notification.source == "rgpd_purge_done",
                        Notification.action_url == f"/crm/contacts/{contact.id}",
                    )
                )
                if existing.scalar_one_or_none():
                    continue

                display_name = contact.display_name

                # Anonymiser
                contact.first_name = "[ANONYMISÉ]"
                contact.last_name = None
                contact.email = None
                contact.phone = None
                contact.notes = None
                contact.tags = None
                contact.company = "[ANONYMISÉ]"
                contact.stage = "archive"
                contact.extra_data = None
                contact.updated_at = now

                # Log d'activité
                activity = Activity(
                    contact_id=contact.id,
                    type="rgpd_auto_purge",
                    title="Contact anonymisé (purge automatique)",
                    description=f"Anonymisation automatique après {retention_months} mois d'inactivité",
                )
                session.add(activity)

                # Notification
                notif = Notification(
                    title="Contact anonymisé (RGPD)",
                    message=f"{display_name} a été anonymisé automatiquement (inactif depuis {retention_months} mois)",
                    type="info",
                    source="rgpd_purge_done",
                    action_url=f"/crm/contacts/{contact.id}",
                    action_label="Voir",
                )
                session.add(notif)
                results["anonymisations"] += 1

            await session.commit()

        total = results["notifications"] + results["anonymisations"]
        if total > 0:
            logger.info(f"Purge RGPD auto : {results}")
        else:
            logger.debug("Purge RGPD auto : aucune action nécessaire")

    except Exception as e:
        logger.error(f"Erreur purge RGPD automatique: {e}")

    return results
