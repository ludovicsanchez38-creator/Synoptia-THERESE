"""Sérialise les publications de fiches avec leurs transactions SQL."""

import asyncio
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from weakref import WeakKeyDictionary

from app.models.database import get_session_context
from app.models.entities import Contact, FileMetadata, Project
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_session
from sqlalchemy.orm import Session
from sqlalchemy.util.concurrency import await_only

_verrous = WeakKeyDictionary()


def _verrou() -> asyncio.Lock:
    boucle = asyncio.get_running_loop()
    return _verrous.setdefault(boucle, asyncio.Lock())


async def garder_verrou_fiches(session: AsyncSession) -> None:
    if not session.in_transaction():
        await session.begin()
    if "verrou_fiches" not in session.info:
        verrou = _verrou()
        await verrou.acquire()
        session.info["verrou_fiches"] = verrou


@event.listens_for(Session, "before_flush")
def _avant_ecriture(session, _contexte, _instances):
    # Inclut les imports, le CRM et l'anonymisation, pas seulement les routes
    # PATCH. Les sessions synchrones de migration n'ont pas de publications.
    porteuse = async_session(session)
    if porteuse is not None and any(
        isinstance(objet, (Contact, Project, FileMetadata))
        for objet in (*session.new, *session.dirty, *session.deleted)
    ):
        await_only(garder_verrou_fiches(porteuse))


@event.listens_for(Session, "after_transaction_end")
def _fin_ecriture(session, transaction):
    if transaction.parent is None:
        verrou = session.info.pop("verrou_fiches", None)
        if verrou is not None:
            verrou.release()


@event.listens_for(Session, "do_orm_execute")
def _avant_ecriture_directe(execution):
    # La purge globale utilise DELETE sans passer par le flush des objets.
    if (execution.is_update or execution.is_delete) and execution.statement.table.name in {
        Contact.__tablename__, Project.__tablename__, FileMetadata.__tablename__,
    }:
        porteuse = async_session(execution.session)
        if porteuse is not None:
            await_only(garder_verrou_fiches(porteuse))


def _version(fiche):
    return {
        cle: valeur.astimezone(UTC).replace(tzinfo=None)
        if isinstance(valeur, datetime) and valeur.tzinfo is not None else valeur
        for cle, valeur in fiche.model_dump().items()
    }


@asynccontextmanager
async def fiche_a_publier(fiche):
    # Le verrou reste détenu jusqu'à la fin effective de l'écriture Qdrant.
    async with _verrou():
        async with get_session_context() as session:
            actuelle = await session.get(type(fiche), fiche.id)
        yield actuelle if actuelle is not None and _version(actuelle) == _version(fiche) else None
