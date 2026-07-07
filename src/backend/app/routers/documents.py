"""
THÉRÈSE v2 - Documents Router

CRUD de l'atelier documentaire : documents, sections, pistes, et
génération de trame via le LLM (rédaction et export = tâches suivantes
du plan - lots B et C).

L'invariant du design vit dans la réorganisation ET la génération de la
trame : jamais de perte de travail déjà engagé. À la réorganisation,
l'ensemble des ids de sections reçus doit être EXACTEMENT l'ensemble des
ids de sections non-orphelines en base, vérifié AVANT toute écriture. Un
écart (id manquant ou inconnu) renvoie un 409 avec le détail, sans toucher
à la moindre ligne. À la génération de trame, la présence d'une seule
section non vide (statut != 'vide' ou contenu non vide) bloque l'appel au
LLM avec un 409 - aucune régénération silencieuse.
"""

import logging
from datetime import UTC, datetime
from typing import cast

from app.models.database import get_session
from app.models.entities import Document, DocumentPiste, DocumentSection
from app.models.schemas_documents import (
    DocumentCreate,
    DocumentResponse,
    PisteResponse,
    PisteUpdate,
    SectionResponse,
    SectionsReorder,
    SectionUpdate,
)
from app.services.document_orchestrator import build_outline_prompt, parse_outline_response
from app.services.llm import get_llm_service
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import case, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

router = APIRouter()
logger = logging.getLogger(__name__)


# =============================================================================
# Schémas locaux (requêtes non couvertes par schemas_documents.py - tâche A2)
# =============================================================================


class SectionCreate(BaseModel):
    """Requête de création manuelle d'une section (hors génération de trame)."""

    title: str
    brief: str = ""
    order: float
    depth: int = 0


class PisteCreate(BaseModel):
    """Requête de capture manuelle d'une piste."""

    texte: str
    section_origine_id: str | None = None


class DocumentDetailResponse(BaseModel):
    """Document complet : trame (sections triées par ordre) + pistes.

    Duplique les champs de DocumentResponse plutôt que d'en hériter - mypy
    (sans le plugin pydantic) type l'import inter-module comme Any et refuse
    la subclassification ("Class cannot subclass ... has type Any").
    """

    id: str
    title: str
    brief: str
    status: str
    project_id: str | None
    contact_id: str | None
    created_at: datetime
    updated_at: datetime
    sections_total: int
    sections_validees: int
    sections: list[SectionResponse]
    pistes: list[PisteResponse]


PISTE_STATUSES = {"nouvelle", "exploree", "ignoree"}


# =============================================================================
# Helpers de sérialisation
# =============================================================================


def _section_to_response(section: DocumentSection) -> SectionResponse:
    return SectionResponse(
        id=section.id,
        document_id=section.document_id,
        title=section.title,
        brief=section.brief,
        order=section.order,
        depth=section.depth,
        content=section.content,
        summary=section.summary,
        status=section.status,
        orphan=section.orphan,
        created_at=section.created_at,
        updated_at=section.updated_at,
    )


def _piste_to_response(piste: DocumentPiste) -> PisteResponse:
    return PisteResponse(
        id=piste.id,
        document_id=piste.document_id,
        section_origine_id=piste.section_origine_id,
        texte=piste.texte,
        status=piste.status,
        created_at=piste.created_at,
    )


def _document_to_response(
    document: Document, sections_total: int, sections_validees: int
) -> DocumentResponse:
    return DocumentResponse(
        id=document.id,
        title=document.title,
        brief=document.brief,
        status=document.status,
        project_id=document.project_id,
        contact_id=document.contact_id,
        created_at=document.created_at,
        updated_at=document.updated_at,
        sections_total=sections_total,
        sections_validees=sections_validees,
    )


async def _get_document_or_404(session: AsyncSession, document_id: str) -> Document:
    document = await session.get(Document, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document introuvable")
    return document


# =============================================================================
# CRUD DOCUMENTS
# =============================================================================


# Collection exposée avec ET sans slash final (anti-redirection 307, cf tasks.py).
@router.post("", include_in_schema=False)
@router.post("/")
async def create_document(
    payload: DocumentCreate,
    session: AsyncSession = Depends(get_session),
) -> DocumentResponse:
    """Crée un nouveau document, vide de toute section."""
    document = Document(
        title=payload.title,
        brief=payload.brief,
        project_id=payload.project_id,
        contact_id=payload.contact_id,
    )
    session.add(document)
    await session.commit()
    await session.refresh(document)

    return _document_to_response(document, sections_total=0, sections_validees=0)


@router.get("", include_in_schema=False)
@router.get("/")
async def list_documents(
    session: AsyncSession = Depends(get_session),
) -> list[DocumentResponse]:
    """Liste tous les documents, avec le décompte de leurs sections (requête agrégée)."""
    result = await session.execute(select(Document).order_by(Document.updated_at.desc()))
    documents = result.scalars().all()

    if not documents:
        return []

    counts_stmt = (
        select(
            DocumentSection.document_id,
            func.count(DocumentSection.id),
            func.sum(case((DocumentSection.status == "validee", 1), else_=0)),
        )
        .where(DocumentSection.document_id.in_([doc.id for doc in documents]))
        .group_by(DocumentSection.document_id)
    )
    counts_result = await session.execute(counts_stmt)
    counts: dict[str, tuple[int, int]] = {
        doc_id: (total, validees or 0) for doc_id, total, validees in counts_result.all()
    }

    return [_document_to_response(doc, *counts.get(doc.id, (0, 0))) for doc in documents]


# =============================================================================
# SECTIONS
# =============================================================================
# NB routage : les chemins spécifiques (/sections/{id}, /{id}/sections,
# /{id}/sections/reorder, /{id}/pistes, /pistes/{id}) sont déclarés AVANT
# les routes génériques /{document_id} plus bas, pour ne jamais se faire
# masquer par elles (FastAPI matche les routes dans l'ordre de déclaration).


@router.patch("/sections/{section_id}")
async def update_section(
    section_id: str,
    payload: SectionUpdate,
    session: AsyncSession = Depends(get_session),
) -> SectionResponse:
    """
    Met à jour une section (titre, consigne, contenu, position, profondeur).

    Une modification du contenu fait passer une section 'vide' à 'brouillon' -
    c'est la trace que la rédaction a démarré sur cette section.
    """
    section = await session.get(DocumentSection, section_id)
    if not section:
        raise HTTPException(status_code=404, detail="Section introuvable")

    updates = payload.model_dump(exclude_unset=True)

    if "content" in updates and section.status == "vide":
        section.status = "brouillon"

    for field, value in updates.items():
        setattr(section, field, value)

    section.updated_at = datetime.now(UTC)
    session.add(section)
    await session.commit()
    await session.refresh(section)

    return _section_to_response(section)


@router.post("/{document_id}/sections")
async def create_section(
    document_id: str,
    payload: SectionCreate,
    session: AsyncSession = Depends(get_session),
) -> SectionResponse:
    """Crée une section manuelle (hors génération de trame par l'IA)."""
    await _get_document_or_404(session, document_id)

    section = DocumentSection(
        document_id=document_id,
        title=payload.title,
        brief=payload.brief,
        order=payload.order,
        depth=payload.depth,
    )
    session.add(section)
    await session.commit()
    await session.refresh(section)

    return _section_to_response(section)


@router.post("/{document_id}/outline")
async def generate_outline(
    document_id: str,
    session: AsyncSession = Depends(get_session),
) -> list[SectionResponse]:
    """
    Génère la trame (plan détaillé) d'un document via le LLM.

    Garde-fou anti-régénération silencieuse : si le document a déjà des
    sections non vides (statut différent de 'vide' OU contenu non vide),
    refuse avec 409 SANS APPELER LE LLM - la création manuelle de section
    reste possible pour compléter une trame existante.

    Si la réponse du LLM est illisible (`parse_outline_response` lève
    `ValueError`), répond 502 sans créer la moindre section.
    """
    document = await _get_document_or_404(session, document_id)

    existing_result = await session.execute(
        select(DocumentSection).where(DocumentSection.document_id == document_id)
    )
    existing_sections = existing_result.scalars().all()
    if any(s.status != "vide" or s.content != "" for s in existing_sections):
        raise HTTPException(
            status_code=409,
            detail=(
                "Ce document a déjà des sections rédigées - la génération de "
                "trame ne peut pas les écraser. Crée une section manuellement "
                "pour compléter la trame existante."
            ),
        )

    llm_service = get_llm_service()
    raw_response = await llm_service.generate_content(
        prompt=build_outline_prompt(document.title, document.brief)
    )

    try:
        parsed_sections = parse_outline_response(raw_response)
    except ValueError:
        raise HTTPException(status_code=502, detail="Trame illisible, réessaie.")

    sections: list[DocumentSection] = []
    for index, item in enumerate(parsed_sections):
        section = DocumentSection(
            document_id=document_id,
            title=cast(str, item["title"]),
            brief=cast(str, item["brief"]),
            order=(index + 1) * 10.0,
            depth=cast(int, item["depth"]),
        )
        session.add(section)
        sections.append(section)

    await session.commit()
    for section in sections:
        await session.refresh(section)

    sections.sort(key=lambda s: s.order)
    return [_section_to_response(s) for s in sections]


@router.post("/{document_id}/sections/reorder", response_model=None)
async def reorder_sections(
    document_id: str,
    payload: SectionsReorder,
    session: AsyncSession = Depends(get_session),
) -> list[SectionResponse] | JSONResponse:
    """
    Réorganise la trame d'un document (ordre + profondeur des sections).

    Invariant anti-perte de données : l'ensemble des ids reçus doit être
    EXACTEMENT l'ensemble des ids de sections non-orphelines en base. La
    vérification a lieu avant toute écriture - un écart (id manquant ou
    inconnu) renvoie 409 avec le détail, sans modifier une seule ligne.

    Renvoie un JSONResponse explicite (et non HTTPException) sur l'écart :
    le handler global (main.py, ARCH-029) sérialise `detail` via `str(...)`,
    ce qui aurait transformé missing_ids/unknown_ids en repr Python illisible
    plutôt qu'en tableaux JSON exploitables par le front.
    """
    await _get_document_or_404(session, document_id)

    result = await session.execute(
        select(DocumentSection).where(
            DocumentSection.document_id == document_id,
            DocumentSection.orphan.is_(False),
        )
    )
    base_sections = {s.id: s for s in result.scalars().all()}
    base_ids = set(base_sections.keys())
    received_ids = {item.id for item in payload.items}

    if base_ids != received_ids:
        missing_ids = sorted(base_ids - received_ids)
        unknown_ids = sorted(received_ids - base_ids)
        return JSONResponse(
            status_code=409,
            content={
                "code": "SECTIONS_INCOMPLETE",
                "message": (
                    "La réorganisation ne couvre pas exactement les sections "
                    "existantes du document - aucune écriture effectuée."
                ),
                "missing_ids": missing_ids,
                "unknown_ids": unknown_ids,
            },
        )

    # Passé ce point, l'ensemble est complet : on peut écrire sans risque de perte.
    for item in payload.items:
        section = base_sections[item.id]
        section.order = item.order
        section.depth = item.depth
        section.updated_at = datetime.now(UTC)
        session.add(section)

    await session.commit()

    refreshed = await session.execute(
        select(DocumentSection)
        .where(DocumentSection.document_id == document_id)
        .order_by(DocumentSection.order)
    )
    return [_section_to_response(s) for s in refreshed.scalars().all()]


# =============================================================================
# PISTES
# =============================================================================


@router.get("/{document_id}/pistes")
async def list_pistes(
    document_id: str,
    session: AsyncSession = Depends(get_session),
) -> list[PisteResponse]:
    """Liste les pistes capturées pour un document (idées annexes de rédaction)."""
    await _get_document_or_404(session, document_id)

    result = await session.execute(
        select(DocumentPiste)
        .where(DocumentPiste.document_id == document_id)
        .order_by(DocumentPiste.created_at)
    )
    return [_piste_to_response(p) for p in result.scalars().all()]


@router.post("/{document_id}/pistes")
async def create_piste(
    document_id: str,
    payload: PisteCreate,
    session: AsyncSession = Depends(get_session),
) -> PisteResponse:
    """Capture manuellement une piste pour un document."""
    await _get_document_or_404(session, document_id)

    piste = DocumentPiste(
        document_id=document_id,
        section_origine_id=payload.section_origine_id,
        texte=payload.texte,
    )
    session.add(piste)
    await session.commit()
    await session.refresh(piste)

    return _piste_to_response(piste)


@router.patch("/pistes/{piste_id}")
async def update_piste_status(
    piste_id: str,
    payload: PisteUpdate,
    session: AsyncSession = Depends(get_session),
) -> PisteResponse:
    """Change le statut d'une piste (nouvelle / exploree / ignoree)."""
    piste = await session.get(DocumentPiste, piste_id)
    if not piste:
        raise HTTPException(status_code=404, detail="Piste introuvable")

    if payload.status not in PISTE_STATUSES:
        raise HTTPException(
            status_code=400,
            detail=f"Statut de piste inconnu : {payload.status!r}",
        )

    piste.status = payload.status
    session.add(piste)
    await session.commit()
    await session.refresh(piste)

    return _piste_to_response(piste)


# =============================================================================
# DOCUMENT PAR ID (routes génériques - déclarées après les chemins spécifiques)
# =============================================================================


@router.get("/{document_id}")
async def get_document(
    document_id: str,
    session: AsyncSession = Depends(get_session),
) -> DocumentDetailResponse:
    """Récupère un document avec sa trame (sections triées par ordre) et ses pistes."""
    document = await _get_document_or_404(session, document_id)

    sections_result = await session.execute(
        select(DocumentSection)
        .where(DocumentSection.document_id == document_id)
        .order_by(DocumentSection.order)
    )
    sections = sections_result.scalars().all()

    pistes_result = await session.execute(
        select(DocumentPiste)
        .where(DocumentPiste.document_id == document_id)
        .order_by(DocumentPiste.created_at)
    )
    pistes = pistes_result.scalars().all()

    sections_validees = sum(1 for s in sections if s.status == "validee")

    return DocumentDetailResponse(
        id=document.id,
        title=document.title,
        brief=document.brief,
        status=document.status,
        project_id=document.project_id,
        contact_id=document.contact_id,
        created_at=document.created_at,
        updated_at=document.updated_at,
        sections_total=len(sections),
        sections_validees=sections_validees,
        sections=[_section_to_response(s) for s in sections],
        pistes=[_piste_to_response(p) for p in pistes],
    )


@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    session: AsyncSession = Depends(get_session),
) -> dict[str, bool | str]:
    """Supprime un document et cascade ses sections + pistes (transactionnel)."""
    document = await _get_document_or_404(session, document_id)

    sections_result = await session.execute(
        select(DocumentSection).where(DocumentSection.document_id == document_id)
    )
    for section in sections_result.scalars().all():
        await session.delete(section)

    pistes_result = await session.execute(
        select(DocumentPiste).where(DocumentPiste.document_id == document_id)
    )
    for piste in pistes_result.scalars().all():
        await session.delete(piste)

    await session.delete(document)
    await session.commit()

    logger.info(f"Document deleted: {document_id}")

    return {"success": True, "message": "Document supprimé"}
