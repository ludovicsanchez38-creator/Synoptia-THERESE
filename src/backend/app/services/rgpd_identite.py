"""L'identité d'une fiche au sens du RGPD : ce qu'on exporte, ce qu'on efface.

B-1438 (recette P-146, lot 2) : l'export Art. 20 d'une fiche oubliait
l'adresse, et l'anonymisation Art. 17 la laissait en clair. B-880 avait
corrigé la purge automatique seulement : la route manuelle tenait sa propre
liste de champs, qui avait divergé. Les deux chemins passent désormais par
ce module, et `CHAMPS_EFFACES` / `CHAMPS_GARDES` classent chaque colonne de
`Contact` (un test refuse une colonne non classée).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from app.models.entities import Contact

ANONYMISE = "[ANONYMISÉ]"

# Valeur posée à l'effacement. La relance datée part avec l'identité : sans
# quoi le brief afficherait « Relancer [ANONYMISÉ] ».
CHAMPS_EFFACES: dict[str, Any] = {
    "first_name": ANONYMISE,
    "last_name": None,
    "company": ANONYMISE,
    "email": None,
    "phone": None,
    "address": None,
    "notes": None,
    "tags": None,
    "extra_data": None,
    "next_follow_up": None,
    "stage": "archive",
}

# Gardées : techniques, ou nécessaires au registre (base légale, dates de
# collecte et d'expiration, exclusion de purge).
CHAMPS_GARDES: tuple[str, ...] = (
    "id",
    "score",
    "source",
    "last_interaction",
    "rgpd_base_legale",
    "rgpd_date_collecte",
    "rgpd_date_expiration",
    "rgpd_consentement",
    "purge_excluded",
    "scope",
    "scope_id",
    "created_at",
    "updated_at",
)


def effacer_l_identite(contact: Contact, maintenant: datetime) -> None:
    """Efface l'identité de la fiche, en place (Art. 17)."""
    for champ, valeur in CHAMPS_EFFACES.items():
        setattr(contact, champ, valeur)
    contact.updated_at = maintenant


def exporter_la_fiche(contact: Contact) -> dict[str, Any]:
    """Toutes les colonnes de la fiche, dates en ISO 8601 (Art. 20)."""
    donnees: dict[str, Any] = {}
    for champ in Contact.model_fields:
        valeur = getattr(contact, champ, None)
        donnees[champ] = valeur.isoformat() if isinstance(valeur, datetime) else valeur
    return donnees


async def detacher_les_dossiers_synchronises(session: Any, contact_id: str) -> None:
    """B-1685 : détache la racine locale de chaque dossier de la personne.

    `retirer_racine` écrit sur sa propre session. Appelée après une écriture
    de la session appelante, elle attendait un verrou que cette session tient
    (« database is locked ») : l'anonymisation d'une personne dont un dossier
    est synchronisé échouait, et avec elle toute la purge automatique du jour.
    À appeler avant toute écriture de la session ; ensuite, la suppression du
    dossier trouve la racine déjà détachée et n'écrit plus rien."""
    from app.models.entities import Project
    from app.services.project_sync_service import retirer_racine
    from sqlmodel import select

    projets = (await session.execute(select(Project.id).where(Project.contact_id == contact_id))).scalars().all()
    for projet_id in projets:
        await retirer_racine(projet_id)


async def anonymiser_la_personne(session: Any, contact: Contact, maintenant: datetime) -> list[str]:
    """B-1651 (décision de Ludo, 26/09) : UN traitement pour l'anonymisation
    manuelle et la purge automatique, qui n'effaçait que la fiche et ses
    e-mails. Rend les identifiants des dossiers supprimés, dont le dépôt
    disque se purge APRÈS le commit (B-445). Ne commite pas."""
    from app.models.entities import (
        Activity,
        EmailMessage,
        Invoice,
        Notification,
        Prestation,
        Project,
        Task,
    )
    from app.routers.memory import _nettoyer_et_supprimer_projet
    from sqlmodel import select

    contact_id = contact.id
    # B-1685 : avant la première écriture de la session.
    await detacher_les_dossiers_synchronises(session, contact_id)
    # B-1438 : l'identité, l'adresse et la relance datée.
    effacer_l_identite(contact, maintenant)

    # Incident du 30/08 : une prestation sans personne n'a pas de sens.
    for prestation in (
        await session.execute(select(Prestation).where(Prestation.contact_id == contact_id))
    ).scalars().all():
        await session.delete(prestation)

    # B-169 (P-003, décision de Ludo) : le nom reste sur les pièces émises
    # (pièce comptable à conserver) ; il disparaît des brouillons.
    for piece in (
        await session.execute(
            select(Invoice).where(Invoice.contact_id == contact_id, Invoice.status == "draft")
        )
    ).scalars().all():
        piece.client_name = "[ANONYMISÉ]"
        piece.client_company = None
        piece.client_email = None
        piece.client_phone = None
        piece.client_address = None
        piece.updated_at = maintenant
        session.add(piece)

    for activite in (
        await session.execute(select(Activity).where(Activity.contact_id == contact_id))
    ).scalars().all():
        await session.delete(activite)

    # B-140 : le dossier suit le chemin de la route de suppression (fragments,
    # fichiers indexés, racine, conversations, documents, événements).
    projets = (
        await session.execute(select(Project).where(Project.contact_id == contact_id))
    ).scalars().all()
    dossiers = [projet.id for projet in projets]
    for projet in projets:
        await _nettoyer_et_supprimer_projet(session, projet)

    # Cycle 6 : les tâches rattachées au contact seul.
    for tache in (await session.execute(select(Task).where(Task.contact_id == contact_id))).scalars().all():
        await session.delete(tache)

    # B-1640 puis B-1688 : les notifications qui visent la fiche portent le
    # nom (« X sera anonymisé le … », « Relance de X prévue … ») ; elles n'ont
    # plus d'objet et ne survivent pas à l'anonymisation, quelle que soit leur
    # source. La notification finale de la purge automatique, sans nom (B-880),
    # est créée après.
    for notification in (
        await session.execute(
            select(Notification).where(Notification.action_url == f"/crm/contacts/{contact_id}")
        )
    ).scalars().all():
        await session.delete(notification)

    # RGPD-1 (US-003) : les e-mails liés (art. 17).
    for email_msg in (
        await session.execute(select(EmailMessage).where(EmailMessage.contact_id == contact_id))
    ).scalars().all():
        await session.delete(email_msg)

    return dossiers
