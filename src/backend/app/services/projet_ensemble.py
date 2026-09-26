"""P-148 : ce que rassemble un projet, sur une seule définition.

Chaque famille liée à un projet a ici sa clause `where`. Deux lecteurs les
partagent : la route d'ensemble (`GET /api/memory/projects/{id}/ensemble`),
qui montre et compte, et `_nettoyer_et_supprimer_projet`
(`routers/memory.py`), qui détache ou supprime. Deux surfaces qui réécrivent
le même filtre finissent par répondre deux chiffres
(`tests/test_relance_une_seule_definition.py`) : la confirmation de
suppression annonce le compte que la suppression exécutera.

Un service n'importe pas un routeur (`routers/prestations.py`) : c'est le
routeur qui lit ce module.
"""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from datetime import UTC, date, datetime
from typing import Any

from app.models.entities import (
    CalendarEvent,
    Contact,
    Conversation,
    Deliverable,
    Document,
    FileMetadata,
    PlanningResource,
    PlanningSnapshot,
    Project,
    Task,
)
from app.models.schemas import _iso_utc
from app.services.civil_time import date_civile_paris
from sqlalchemy import and_, case, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.elements import ColumnElement
from sqlmodel import col, select

logger = logging.getLogger(__name__)

LIMITE_PAR_DEFAUT = 5
#: Comme la liste des conversations (`routers/chat.py`) : au-delà, l'écran
#: dit « liste incomplète » plutôt que de charger un projet entier.
LIMITE_MAXIMALE = 200
STATUTS_OUVERTS = ("todo", "in_progress")


# ============================================================
# Les clauses : ce qu'« appartenir à ce projet » veut dire
# ============================================================


def clause_fichiers(projet_id: str) -> ColumnElement[bool]:
    return and_(col(FileMetadata.scope) == "project", col(FileMetadata.scope_id) == projet_id)


def clause_conversations(projet_id: str) -> ColumnElement[bool]:
    # Quel que soit `memory_scope` : cette définition dit à qui la
    # conversation est rattachée, pas ce qu'elle lit.
    return col(Conversation.project_id) == projet_id


def clause_documents(projet_id: str) -> ColumnElement[bool]:
    return col(Document.project_id) == projet_id


def clause_rendez_vous(projet_id: str) -> ColumnElement[bool]:
    return col(CalendarEvent.project_id) == projet_id


def clause_contacts_ranges(projet_id: str) -> ColumnElement[bool]:
    """Les contacts créés dans le projet (pas le contact associé, lien inverse)."""
    return and_(col(Contact.scope) == "project", col(Contact.scope_id) == projet_id)


def clause_sous_dossiers(projet_id: str) -> ColumnElement[bool]:
    return and_(col(Project.scope) == "project", col(Project.scope_id) == projet_id)


def clause_taches(projet_id: str) -> ColumnElement[bool]:
    return col(Task.project_id) == projet_id


def clause_livrables(projet_id: str) -> ColumnElement[bool]:
    return col(Deliverable.project_id) == projet_id


def clause_ressources_de_planning(projet_id: str) -> ColumnElement[bool]:
    return col(PlanningResource.project_id) == projet_id


def clause_instantanes_de_planning(projet_id: str) -> ColumnElement[bool]:
    return col(PlanningSnapshot.project_id) == projet_id


# ============================================================
# La lecture : une famille à la fois, chacune se dégrade seule
# ============================================================


async def _compter(session: AsyncSession, modele: Any, clause: ColumnElement[bool]) -> int:
    requete = select(func.count()).select_from(modele).where(clause)
    return int((await session.execute(requete)).scalar_one())


async def _lire_conversations(
    session: AsyncSession, projet_id: str, contact_id: str | None, limite: int, jour: date
) -> dict[str, Any]:
    clause = clause_conversations(projet_id)
    lignes = (
        await session.execute(
            select(Conversation)
            .where(clause)
            .order_by(col(Conversation.updated_at).desc(), col(Conversation.id))
            .limit(limite)
        )
    ).scalars().all()
    return {
        "total": await _compter(session, Conversation, clause),
        "elements": [
            {"id": c.id, "titre": c.title, "mise_a_jour": _iso_utc(c.updated_at)} for c in lignes
        ],
    }


async def _lire_documents(
    session: AsyncSession, projet_id: str, contact_id: str | None, limite: int, jour: date
) -> dict[str, Any]:
    clause = clause_documents(projet_id)
    lignes = (
        await session.execute(
            select(Document)
            .where(clause)
            .order_by(col(Document.updated_at).desc(), col(Document.id))
            .limit(limite)
        )
    ).scalars().all()
    return {
        "total": await _compter(session, Document, clause),
        "elements": [
            {"id": d.id, "titre": d.title, "statut": d.status, "mise_a_jour": _iso_utc(d.updated_at)}
            for d in lignes
        ],
    }


def _en_retard(tache: Task, jour: date) -> bool:
    # Une échéance est un jour décidé, stocké sans fuseau et lu comme heure
    # de Paris (`date_civile_paris`, comme l'accueil) : elle passe en retard
    # à minuit de Paris, pas à minuit UTC.
    return (
        tache.status in STATUTS_OUVERTS
        and tache.due_date is not None
        and date_civile_paris(tache.due_date) < jour
    )


async def _lire_taches(
    session: AsyncSession, projet_id: str, contact_id: str | None, limite: int, jour: date
) -> dict[str, Any]:
    clause = clause_taches(projet_id)
    # Ouvertes d'abord, puis par échéance, sans échéance en dernier. Pas les
    # rangs du routeur des tâches : un service n'importe pas un routeur.
    fermee = case((col(Task.status).in_(STATUTS_OUVERTS), 0), else_=1)
    sans_echeance = case((col(Task.due_date).is_(None), 1), else_=0)
    lignes = (
        await session.execute(
            select(Task)
            .where(clause)
            .order_by(fermee, sans_echeance, col(Task.due_date), col(Task.created_at), col(Task.id))
            .limit(limite)
        )
    ).scalars().all()
    ouvertes = (
        await session.execute(
            select(Task).where(clause, col(Task.status).in_(STATUTS_OUVERTS))
        )
    ).scalars().all()
    return {
        "total": await _compter(session, Task, clause),
        "ouvertes": len(ouvertes),
        "en_retard": sum(1 for tache in ouvertes if _en_retard(tache, jour)),
        "elements": [
            {
                "id": t.id,
                "titre": t.title,
                "statut": t.status,
                "echeance": t.due_date.isoformat() if t.due_date else None,
                "en_retard": _en_retard(t, jour),
            }
            for t in lignes
        ],
    }


def _contact(fiche: Contact, *, associe: bool) -> dict[str, Any]:
    # Revue P-148, constat 2 : les champs séparés, pas un nom composé. En
    # démonstration, l'écran applique maskContact champ par champ, comme le
    # sélecteur « Contact associé » ; une substitution de texte ne masquait
    # pas un contact absent du carnet chargé.
    return {
        "id": fiche.id,
        "first_name": fiche.first_name,
        "last_name": fiche.last_name,
        "company": fiche.company,
        "associe": associe,
    }


async def _lire_contacts(
    session: AsyncSession, projet_id: str, contact_id: str | None, limite: int, jour: date
) -> dict[str, Any]:
    clause = clause_contacts_ranges(projet_id)
    associe = await session.get(Contact, contact_id) if contact_id else None
    # Constat 18 de la revue : le contact associé peut aussi être rangé dans
    # le projet. Il ne s'affiche qu'une fois, en tête ; il reste compté parmi
    # les rangés, que la suppression rendra au périmètre général.
    requete = select(Contact).where(clause)
    if associe is not None:
        requete = requete.where(col(Contact.id) != associe.id)
    ranges_sans_associe = (
        await session.execute(
            requete.order_by(
                col(Contact.last_name), col(Contact.first_name), col(Contact.company), col(Contact.id)
            ).limit(limite - (1 if associe is not None else 0))
        )
    ).scalars().all()
    ranges = await _compter(session, Contact, clause)
    associe_range = associe is not None and associe.scope == "project" and associe.scope_id == projet_id
    elements = ([_contact(associe, associe=True)] if associe is not None else []) + [
        _contact(fiche, associe=False) for fiche in ranges_sans_associe
    ]
    return {
        "total": ranges + (1 if associe is not None and not associe_range else 0),
        "ranges": ranges,
        "elements": elements,
    }


def _total(modele: Any, clause: Callable[[str], ColumnElement[bool]]) -> Callable[..., Awaitable[dict[str, Any]]]:
    async def lire(
        session: AsyncSession, projet_id: str, contact_id: str | None, limite: int, jour: date
    ) -> dict[str, Any]:
        return {"total": await _compter(session, modele, clause(projet_id))}

    return lire


async def _lire_planning(
    session: AsyncSession, projet_id: str, contact_id: str | None, limite: int, jour: date
) -> dict[str, Any]:
    # Ressources et instantanés partent par la cascade du projet
    # (`Project.planning_resources`, `Project.planning_snapshots`).
    return {
        "total": await _compter(session, PlanningResource, clause_ressources_de_planning(projet_id))
        + await _compter(session, PlanningSnapshot, clause_instantanes_de_planning(projet_id))
    }


async def lire_l_ensemble(
    session: AsyncSession,
    projet: Project,
    limite: int = LIMITE_PAR_DEFAUT,
    maintenant: datetime | None = None,
) -> dict[str, Any]:
    """Chaque famille du projet, bornée à `limite` éléments, avec son total.

    Une famille dont la lecture échoue vaut `None` et se nomme dans
    `indisponibles`, comme `/api/dashboard/semaine` : une panne n'est pas un
    vide, et la confirmation de suppression ne doit pas annoncer « 0 tâche ».
    """
    # Valeurs lues une fois : aucune famille ne relit l'objet du projet.
    projet_id, contact_id = projet.id, projet.contact_id
    jour = date_civile_paris(maintenant or datetime.now(UTC))
    familles: tuple[tuple[str, Callable[..., Awaitable[dict[str, Any]]]], ...] = (
        ("conversations", _lire_conversations),
        ("documents", _lire_documents),
        ("taches", _lire_taches),
        ("contacts", _lire_contacts),
        ("livrables", _total(Deliverable, clause_livrables)),
        ("fichiers", _total(FileMetadata, clause_fichiers)),
        ("rendez_vous", _total(CalendarEvent, clause_rendez_vous)),
        ("sous_dossiers", _total(Project, clause_sous_dossiers)),
        ("planning", _lire_planning),
    )
    ensemble: dict[str, Any] = {}
    indisponibles: list[str] = []
    for nom, lire in familles:
        try:
            ensemble[nom] = await lire(session, projet_id, contact_id, limite, jour)
        except Exception:
            logger.warning("Lecture de la famille %s du projet %s en échec", nom, projet_id, exc_info=True)
            ensemble[nom] = None
            indisponibles.append(nom)
    ensemble["indisponibles"] = indisponibles
    return ensemble
