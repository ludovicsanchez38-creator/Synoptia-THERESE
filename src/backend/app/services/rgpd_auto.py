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
from typing import Any

from app.models.database import get_session_context
from app.models.entities import Activity, Contact, Notification
from app.services.rgpd_identite import anonymiser_la_personne, detacher_les_dossiers_synchronises
from sqlalchemy import func
from sqlmodel import or_, select

logger = logging.getLogger(__name__)

# Durée de rétention par défaut (en mois)
DEFAULT_RETENTION_MONTHS = 36


async def purge_contact_vector(contact_id: str, max_attempts: int = 3) -> int:
    """Supprime l'embedding Qdrant d'un contact (droit à l'oubli, Art. 17).

    Sans cette purge, la fiche anonymisée [ANONYMISÉ] continue de remonter en
    recherche sémantique au même score (constat C4 de la revue produit) :
    l'effacement reste incomplet et la faille RGPD est démontrable.

    US-003 (RGPD-2) : on retente en cas de panne transitoire de Qdrant pour
    réduire la fenêtre de « vecteur fantôme ». Best effort en dernier recours :
    une panne durable ne fait pas échouer l'anonymisation déjà actée en base
    (journalisée en ERROR pour traçabilité/alerte).
    """
    last_error: Exception | None = None
    for attempt in range(1, max_attempts + 1):
        try:
            from app.services.qdrant import get_qdrant_service

            return await get_qdrant_service().async_delete_by_entity(contact_id)
        except Exception as e:  # noqa: BLE001 - on retente puis on journalise
            last_error = e
            logger.warning(
                f"RGPD: échec purge vecteur Qdrant pour {contact_id} "
                f"(tentative {attempt}/{max_attempts}): {e}"
            )
    logger.error(
        f"RGPD: purge vecteur Qdrant définitivement échouée pour {contact_id} "
        f"après {max_attempts} tentatives: {last_error}"
    )
    return 0


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


PREAVIS_JOURS = 30


def _debut_de_l_episode(ref_date: datetime, expiration: datetime | None, retention_months: int) -> datetime:
    """B-1670 : moment où la fiche est devenue échue cette fois-ci (début des
    avertissements, ou fin du consentement renouvelé). Un préavis antérieur
    appartient à un épisode passé : relance ou consentement l'ont périmé."""
    debut = ref_date + timedelta(days=retention_months * 30 - PREAVIS_JOURS)
    if expiration is not None and expiration > debut:
        debut = expiration
    return debut


async def _premier_preavis(session: Any, contact_id: str, depuis: datetime) -> datetime | None:
    """B-1641 : date du premier préavis de purge donné pour ce contact pendant
    l'épisode en cours (B-1670)."""
    premier = (
        await session.execute(
            select(func.min(Notification.created_at)).where(
                Notification.source == "rgpd_purge",
                Notification.action_url == f"/crm/contacts/{contact_id}",
                Notification.created_at >= depuis,
            )
        )
    ).scalar()
    if premier is not None and premier.tzinfo is None:
        premier = premier.replace(tzinfo=UTC)
    return premier


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
                    # Pas déjà anonymisés. B-841 : un `!=` seul écarte aussi les
                    # prénoms NULL (comparaison SQL jamais vraie), donc un contact
                    # sans prénom échappait pour toujours à la purge.
                    or_(Contact.first_name.is_(None), Contact.first_name != "[ANONYMISÉ]"),
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

                # B-1667 : un consentement renouvelé (ou une expiration RGPD
                # encore à venir) protège le contact : l'écran promet
                # « prolongé de 3 ans ».
                expiration = contact.rgpd_date_expiration
                if expiration is not None:
                    if expiration.tzinfo is None:
                        expiration = expiration.replace(tzinfo=UTC)
                    if expiration > now:
                        continue

                if ref_date < purge_threshold:
                    # B-1641 : un contact importé ou synchronisé avec une
                    # vieille « Dernière interaction » était anonymisé au
                    # démarrage suivant, sans jamais avoir été annoncé. Aucune
                    # anonymisation sans un préavis donné 30 jours avant.
                    premier_preavis = await _premier_preavis(
                        session, contact.id, _debut_de_l_episode(ref_date, expiration, retention_months)
                    )
                    if premier_preavis is not None and premier_preavis <= now - timedelta(days=PREAVIS_JOURS):
                        contacts_to_purge.append(contact)
                    else:
                        contacts_to_warn.append(contact)
                elif ref_date < warning_threshold:
                    contacts_to_warn.append(contact)

            # B-1685 : les préavis écrivent dans la session ; les dossiers
            # synchronisés des fiches à anonymiser se détachent avant.
            for contact in contacts_to_purge:
                await detacher_les_dossiers_synchronises(session, contact.id)

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
                # B-878 : deux notifications pour le même contact faisaient
                # lever MultipleResultsFound et avortaient toute la campagne.
                if existing.scalars().first():
                    continue

                purge_date = contact.last_interaction or contact.updated_at or contact.created_at
                if purge_date:
                    if purge_date.tzinfo is None:
                        purge_date = purge_date.replace(tzinfo=UTC)
                    # B-1641 : jamais avant la fin du préavis.
                    expiration = contact.rgpd_date_expiration
                    if expiration is not None and expiration.tzinfo is None:
                        expiration = expiration.replace(tzinfo=UTC)
                    premier_preavis = await _premier_preavis(
                        session, contact.id, _debut_de_l_episode(purge_date, expiration, retention_months)
                    ) or now
                    echeance = max(
                        purge_date + timedelta(days=retention_months * 30),
                        premier_preavis + timedelta(days=PREAVIS_JOURS),
                    )
                    purge_date_str = echeance.strftime("%d/%m/%Y")
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
            anonymized_ids: list[str] = []
            dossiers_a_purger: list[str] = []
            for contact in contacts_to_purge:
                # Vérifier qu'on n'a pas déjà notifié l'anonymisation
                existing = await session.execute(
                    select(Notification).where(
                        Notification.source == "rgpd_purge_done",
                        Notification.action_url == f"/crm/contacts/{contact.id}",
                    )
                )
                if existing.scalars().first():
                    continue

                # B-880, B-1438 puis B-1651 : le même traitement que la route
                # manuelle (tâches, brouillons, prestations, activités, dossiers
                # et e-mails compris), décision de Ludo du 26/09.
                dossiers_a_purger.extend(await anonymiser_la_personne(session, contact, now))

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
                    # B-880 : la notification survit à l'effacement, elle ne
                    # porte donc plus le nom de la personne.
                    message=f"Un contact a été anonymisé automatiquement (inactif depuis {retention_months} mois)",
                    type="info",
                    source="rgpd_purge_done",
                    action_url=f"/crm/contacts/{contact.id}",
                    action_label="Voir",
                )
                session.add(notif)
                anonymized_ids.append(contact.id)
                results["anonymisations"] += 1

            await session.commit()

        # Purge du fantôme vectoriel (P0-RGPD-1) hors session SQL : même droit à
        # l'oubli que l'anonymisation manuelle, sinon la fiche [ANONYMISÉ]
        # resterait indexée dans Qdrant.
        for cid in anonymized_ids:
            await purge_contact_vector(cid)
        # B-445 : le dépôt disque des dossiers supprimés, après le commit.
        if dossiers_a_purger:
            from app.routers.memory import _purger_le_depot_du_dossier

            for dossier_id in dossiers_a_purger:
                await _purger_le_depot_du_dossier(dossier_id)

        total = results["notifications"] + results["anonymisations"]
        if total > 0:
            logger.info(f"Purge RGPD auto : {results}")
        else:
            logger.debug("Purge RGPD auto : aucune action nécessaire")

    except Exception as e:
        logger.error(f"Erreur purge RGPD automatique: {e}")
        # B-894 : un commit qui échoue n'a rien écrit ; les compteurs
        # incrémentés au fil de la boucle mentiraient à l'appelant.
        results = {"notifications": 0, "anonymisations": 0}

    return results
