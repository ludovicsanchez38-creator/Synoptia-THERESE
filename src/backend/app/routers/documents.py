"""
THÉRÈSE v2 - Documents Router

CRUD de l'atelier documentaire : documents, sections, pistes, génération
de trame, rédaction en streaming SSE, validation d'une section via le LLM
et export md/docx (assemblage : `app.services.document_orchestrator.assemble_markdown`).

L'invariant du design vit dans la réorganisation, la génération de trame
ET l'export. À la réorganisation, l'ensemble des ids de sections reçus
doit être EXACTEMENT l'ensemble des ids de sections non-orphelines en
base, vérifié AVANT toute écriture. Un écart (id manquant ou inconnu)
renvoie un 409 avec le détail, sans toucher à la moindre ligne. À la
génération de trame, la présence d'une seule section non vide (statut !=
'vide' ou contenu non vide) bloque l'appel au LLM avec un 409 - aucune
régénération silencieuse. À l'export, la trame est lue UNE SEULE FOIS et
cette lecture alimente à la fois la vérification de complétude et
l'assemblage - jamais deux lectures qui pourraient diverger.
"""

import asyncio
import functools
import json
import logging
import time
import uuid
from datetime import UTC, datetime
from typing import AsyncGenerator, cast

from app.models.database import get_session, get_session_context
from app.models.entities import Contact, Document, DocumentPiste, DocumentSection, Project
from app.models.processing import EtatTache
from app.models.schemas_documents import (
    DocumentCreate,
    DocumentResponse,
    DraftRequest,
    PisteResponse,
    PisteUpdate,
    SectionResponse,
    SectionsReorder,
    SectionUpdate,
)
from app.services import task_registry, traitements
from app.services.document_orchestrator import (
    assemble_markdown,
    build_outline_prompt,
    build_section_context,
    build_summary_prompt,
    parse_draft_output,
    parse_outline_response,
)
from app.services.error_handler import message_pour_ecran
from app.services.llm import Message, get_llm_service
from app.services.token_tracker import enregistrer_usage_llm
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import case, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

router = APIRouter()
logger = logging.getLogger(__name__)

# Persistance au fil de l'eau du brouillon streamé (design : zéro perte de
# contenu, même sur fermeture d'app). Constante de module pour que les tests
# puissent la réduire (monkeypatch) sans dépendre d'un vrai sleep de 2 s.
DRAFT_FLUSH_INTERVAL_SECONDS = 2.0


# =============================================================================
# Schémas locaux (requêtes non couvertes par schemas_documents.py - tâche A2)
# =============================================================================


class SectionCreate(BaseModel):
    """Requête de création manuelle d'une section (hors génération de trame)."""

    title: str
    brief: str = ""
    order: float = Field(..., allow_inf_nan=False)  # B-184 : ni NaN ni l'infini
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


def _touch_document(document: Document, session: AsyncSession) -> None:
    """Bump `Document.updated_at` (finding minor 9, revue finale) : la liste
    des documents est triée par updated_at desc - un document en cours de
    rédaction (section retouchée, réordonnée, validée, ou nouvelle
    section/piste) doit remonter, pas rester figé à sa date de création."""
    document.updated_at = datetime.now(UTC)
    session.add(document)


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
    # B-561 (05/09/2026) : un document naissait rattaché à un projet ou un
    # contact inexistant. Les tâches vérifient déjà leur projet : même devoir.
    if payload.project_id and await session.get(Project, payload.project_id) is None:
        raise HTTPException(status_code=404, detail="Projet non trouvé")
    if payload.contact_id and await session.get(Contact, payload.contact_id) is None:
        raise HTTPException(status_code=404, detail="Contact non trouvé")
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

    Un `null` explicite sur un champ (ex. `{"title": null}`) est traité comme
    une absence de changement plutôt que comme une tentative d'écrire NULL -
    tous les champs de `SectionUpdate` correspondent à des colonnes
    non-nullables (`title`, `order`, `depth`...), un null écrit tel quel
    aurait fait échouer le commit avec une 500 (revue finale, finding 5).
    """
    section = await session.get(DocumentSection, section_id)
    if not section:
        raise HTTPException(status_code=404, detail="Section introuvable")

    updates = payload.model_dump(exclude_unset=True, exclude_none=True)

    if "content" in updates and section.status == "vide":
        section.status = "brouillon"

    for field, value in updates.items():
        setattr(section, field, value)

    section.updated_at = datetime.now(UTC)
    session.add(section)

    document = await session.get(Document, section.document_id)
    if document:
        _touch_document(document, session)

    await session.commit()
    await session.refresh(section)

    return _section_to_response(section)


async def _draft_stream(
    document: Document,
    sections: list[DocumentSection],
    target: DocumentSection,
    instruction: str | None,
    session: AsyncSession,
) -> AsyncGenerator[str, None]:
    """Génère le SSE de rédaction d'une section, avec persistance continue.

    Invariant de design (zéro perte) : le contenu accumulé est écrit en base
    toutes les ~2 s (`DRAFT_FLUSH_INTERVAL_SECONDS`), statut 'brouillon' dès
    la première écriture. Si le fournisseur LLM échoue en cours de route, le
    partiel accumulé jusqu'ici est flushé une dernière fois AVANT le chunk
    d'erreur - il reste en base, jamais perdu.

    Filet de dernier recours (revue adversariale lot B, finding 3) : le
    `finally` global flushe l'accumulé s'il n'a pas déjà été persisté par un
    chemin normal, y compris sur `asyncio.CancelledError` ou `GeneratorExit`
    (fermeture d'app, déconnexion réelle du client) - ces deux exceptions
    sont des `BaseException`, jamais interceptées par le `except Exception`
    ci-dessous, donc elles remontent bien jusqu'au `finally` puis continuent
    de se propager (rien n'est avalé). Aucun chunk n'est émis dans ce cas :
    la connexion est déjà morte, et `yield` dans un `finally` qui gère un
    `GeneratorExit` lèverait de toute façon une `RuntimeError`.

    Complétion vide (finding 1) : si le contenu rédigé final est vide après
    parsing (0 chunk reçu, ou réponse ne contenant qu'un bloc PISTES sans
    aucun contenu réel), on n'écrase JAMAIS `target.content` ni son statut,
    et aucune piste n'est créée - seul un chunk `error` est émis.

    Document rouvert (finding 5) : dès qu'un draft persiste effectivement du
    contenu (flush périodique, filet de fermeture, ou fin de rédaction), un
    document déjà `termine` repasse à `en_cours` - une retouche ne doit
    jamais laisser un document affiché comme terminé avec une section
    redevenue `brouillon`.
    """
    llm_service = get_llm_service()
    prompt = build_section_context(document, sections, target, instruction)
    context = llm_service.prepare_context(messages=[Message(role="user", content=prompt)])

    accumulated = ""
    last_flush = time.monotonic()
    last_flushed_raw: str | None = None
    completed = False

    def _reopen_document_if_termine() -> None:
        if document.status == "termine":
            document.status = "en_cours"

    async def _flush(raw_content: str) -> None:
        nonlocal last_flushed_raw
        target.content = raw_content
        target.status = "brouillon"
        target.updated_at = datetime.now(UTC)
        session.add(target)
        _reopen_document_if_termine()
        # Finding minor 9 : chaque flush (périodique ou final) fait vivre le
        # document, pas seulement une transition termine -> en_cours.
        _touch_document(document, session)
        await session.commit()
        last_flushed_raw = raw_content

    try:
        try:
            usage_redaction: dict[str, int] = {}
            async for chunk in llm_service.stream_response(context, raise_on_error=True, usage_sink=usage_redaction):
                accumulated += chunk
                yield f"data: {json.dumps({'type': 'text', 'content': chunk})}\n\n"

                now = time.monotonic()
                if now - last_flush >= DRAFT_FLUSH_INTERVAL_SECONDS:
                    await _flush(accumulated)
                    last_flush = now
        except Exception as exc:  # erreur provider (réseau, quota, etc.) à reporter en SSE
            if accumulated and accumulated != last_flushed_raw:
                await _flush(accumulated)
            completed = True
            logger.warning(
                "Draft SSE : échec du fournisseur LLM pour la section %s : %s",
                target.id,
                exc,
            )
            message = message_pour_ecran(exc, ou="pendant la rédaction")
            yield f"data: {json.dumps({'type': 'error', 'content': message})}\n\n"
            return

        # B-632 : compté avant l'analyse du texte, une réponse inexploitable a
        # quand même coûté des jetons.
        enregistrer_usage_llm(llm_service, usage_redaction, f"document:{document.id}", prompt, accumulated)
        content, pistes_texts = parse_draft_output(accumulated)
        if not content.strip():
            completed = True
            logger.warning(
                "Draft SSE : complétion vide pour la section %s (aucun contenu "
                "exploitable après parsing) - contenu existant préservé",
                target.id,
            )
            message = "Le modèle n'a produit aucun contenu, réessaie."
            yield f"data: {json.dumps({'type': 'error', 'content': message})}\n\n"
            return

        target.content = content
        target.status = "brouillon"
        target.updated_at = datetime.now(UTC)
        session.add(target)
        _reopen_document_if_termine()
        _touch_document(document, session)

        for piste_text in pistes_texts:
            session.add(
                DocumentPiste(
                    document_id=document.id,
                    section_origine_id=target.id,
                    texte=piste_text,
                )
            )

        await session.commit()
        completed = True

        yield f"data: {json.dumps({'type': 'done', 'section_id': target.id})}\n\n"
    finally:
        if not completed and accumulated and accumulated != last_flushed_raw:
            await _flush(accumulated)


@router.post("/sections/{section_id}/draft", response_model=None)
async def draft_section(
    section_id: str,
    payload: DraftRequest,
    session: AsyncSession = Depends(get_session),
) -> StreamingResponse:
    """
    Rédige (ou retouche) une section via le LLM, en streaming SSE.

    Format des chunks (un par ligne `data: {...}\\n\\n`, cf `_command_stream`
    de chat.py) : {"type": "text", "content": ...} pendant la génération,
    {"type": "done", "section_id": ...} à la fin, ou {"type": "error",
    "content": message français} si le fournisseur échoue en cours de route
    (le contenu déjà généré reste en base, statut 'brouillon' - zéro perte)
    OU si la complétion finale est vide une fois parsée (aucun chunk reçu,
    ou réponse ne contenant qu'un bloc PISTES sans contenu réel) - dans ce
    dernier cas, le contenu existant de la section n'est JAMAIS écrasé et
    son statut reste inchangé.
    """
    target = await session.get(DocumentSection, section_id)
    if not target:
        raise HTTPException(status_code=404, detail="Section introuvable")

    document = await _get_document_or_404(session, target.document_id)

    sections_result = await session.execute(
        select(DocumentSection)
        .where(DocumentSection.document_id == document.id)
        .order_by(DocumentSection.order)
    )
    sections = list(sections_result.scalars().all())

    return StreamingResponse(
        _draft_stream(document, sections, target, payload.instruction, session),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/sections/{section_id}/validate")
async def validate_section(
    section_id: str,
    session: AsyncSession = Depends(get_session),
) -> SectionResponse:
    """
    Valide une section : génère son résumé (contexte des sections suivantes,
    jamais son texte intégral) et passe son statut à 'validee'.

    La validation ne bloque JAMAIS sur un échec LLM : si le résumé ne peut
    pas être généré, on retombe sur les 300 premiers caractères du contenu.
    Si toutes les sections non-orphelines du document sont désormais
    'validee', le document entier passe à 'termine'.
    """
    section = await session.get(DocumentSection, section_id)
    if not section:
        raise HTTPException(status_code=404, detail="Section introuvable")

    if not section.content.strip():
        raise HTTPException(
            status_code=400,
            detail="Impossible de valider une section sans contenu.",
        )

    llm_service = get_llm_service()
    try:
        usage_resume: dict[str, int] = {}
        summary = (await llm_service.generate_content(prompt=build_summary_prompt(section), usage_sink=usage_resume)).strip()
        enregistrer_usage_llm(llm_service, usage_resume, f"document:{section.document_id}", section.content, summary)
        if not summary:
            summary = section.content[:300]
    except Exception as exc:  # fallback volontaire : la validation ne bloque jamais
        logger.warning(
            "Validation section %s : résumé LLM indisponible (%s), fallback 300 caractères",
            section_id,
            exc,
        )
        summary = section.content[:300]

    section.summary = summary
    section.status = "validee"
    section.updated_at = datetime.now(UTC)
    session.add(section)

    document = await _get_document_or_404(session, section.document_id)
    siblings_result = await session.execute(
        select(DocumentSection).where(
            DocumentSection.document_id == document.id,
            DocumentSection.orphan.is_(False),
        )
    )
    siblings = siblings_result.scalars().all()
    if siblings and all(s.status == "validee" for s in siblings):
        document.status = "termine"
    # Finding minor 9 : valider une section fait vivre le document même sans
    # transition vers 'termine' (liste triée par updated_at desc).
    _touch_document(document, session)

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
    document = await _get_document_or_404(session, document_id)

    section = DocumentSection(
        document_id=document_id,
        title=payload.title,
        brief=payload.brief,
        order=payload.order,
        depth=payload.depth,
    )
    session.add(section)
    _touch_document(document, session)  # finding minor 9
    await session.commit()
    await session.refresh(section)

    return _section_to_response(section)


class OutlineRequest(BaseModel):
    """P-056 : le client choisit l'identifiant du traitement pour pouvoir
    demander l'arrêt pendant que la requête est en vol (voie (a) de la revue
    COCO). Optionnel : les appels existants continuent de marcher."""

    task_id: uuid.UUID | None = None


class TrameIllisible(Exception):
    """Le LLM a répondu, mais pas une trame."""


class TrameOccupee(Exception):
    """Des sections ont été rédigées pendant la génération : on n'écrase rien."""


class _TrameAnnulee:
    """Sentinelle : la génération s'est arrêtée avant toute écriture."""


TRAME_ANNULEE = _TrameAnnulee()

# Références fortes sur les porteuses : une déconnexion du client n'annule pas
# la génération (elle reste visible et annulable dans « Travaux »).
_PORTEUSES: set["asyncio.Task[object]"] = set()

_MESSAGE_SECTIONS_REDIGEES = (
    "Ce document a déjà des sections rédigées - la génération de "
    "trame ne peut pas les écraser. Crée une section manuellement "
    "pour compléter la trame existante."
)


async def _terminer_temoin(handle: traitements.TraitementHandle, etat: str, *, error: str | None = None) -> None:
    """Le suivi est un témoin, jamais un acteur : sa clôture peut échouer (base
    verrouillée) sans changer le sort de la trame. Revue COCO 0.69.0 (finding 8) :
    une seconde tentative, puis la ligne reste sans producteur ; `actif_pour`
    ignore une telle orpheline, elle ne verrouille pas la génération suivante."""
    for tentative in (1, 2):
        try:
            await handle.terminer(etat, error=error)
            return
        except Exception:
            logger.warning("Suivi de la trame non clôturé (%s, tentative %d)", handle.id, tentative, exc_info=True)
            if tentative == 1:
                await asyncio.sleep(0.2)


def _clore_si_orpheline(handle: traitements.TraitementHandle, tache: "asyncio.Task[object]") -> None:
    """Revue COCO 0.69.0 (finding 3) : une annulation qui touche la porteuse
    avant son premier pas n'entre jamais dans son `try`, personne ne pose
    l'état terminal et le traitement reste `cancel_requested` pour toujours
    (non annulable, et `actif_pour` bloque le document). C'est ici, à la fin
    de la tâche, que le témoin est clos dans ce cas."""
    if not tache.cancelled():
        return
    cloture = asyncio.ensure_future(_terminer_temoin(handle, EtatTache.CANCELLED))
    _PORTEUSES.add(cloture)
    cloture.add_done_callback(_PORTEUSES.discard)


async def _ecrire_la_trame(
    document_id: str, parsed_sections: list[dict[str, object]], ids_initiales: frozenset[str] = frozenset()
) -> list[SectionResponse]:
    """Point de non-retour de la génération : relit les sections dans SA
    transaction (revue COCO, finding 4) et ne remplace que des sections encore
    toutes vides. Appelée sous `asyncio.shield` : une annulation qui arrive
    pendant l'écriture laisse l'écriture aboutir.

    Revue COCO 0.69.0 (finding 1) : seules les sections vides CONNUES AU
    LANCEMENT sont remplacées. Une section ajoutée à la main pendant la
    génération (titre et consigne saisis, contenu encore vide) est du travail
    de l'utilisateur : elle est conservée, placée après la trame générée."""
    async with get_session_context() as session:
        existing_result = await session.execute(
            select(DocumentSection).where(DocumentSection.document_id == document_id)
        )
        existing_sections = existing_result.scalars().all()
        if any(s.status != "vide" or s.content != "" for s in existing_sections):
            raise TrameOccupee()
        ajoutees_pendant = sorted(
            (s for s in existing_sections if s.id not in ids_initiales), key=lambda s: s.order
        )
        for old_section in existing_sections:
            if old_section.id in ids_initiales:
                await session.delete(old_section)
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
        for rang, section in enumerate(ajoutees_pendant, start=len(parsed_sections) + 1):
            section.order = rang * 10.0
            sections.append(section)
        await session.commit()
        for section in sections:
            await session.refresh(section)
        sections.sort(key=lambda s: s.order)
        return [_section_to_response(s) for s in sections]


async def _generer_la_trame(
    handle: traitements.TraitementHandle,
    document_id: str,
    titre: str,
    brief: str | None,
    ids_initiales: frozenset[str] = frozenset(),
) -> list[SectionResponse] | _TrameAnnulee:
    """La porteuse : tout le travail (LLM, analyse, écriture), avec les
    transitions exactes du registre. L'état terminal est posé ICI, par le
    producteur, après son nettoyage réel : DONE, FAILED ou CANCELLED.

    Revue COCO 0.69.0 (finding 3) : QUEUED → RUNNING se fait ICI, après
    l'enrôlement de l'adaptateur par `_lancer_la_generation`. Il n'existe donc
    plus de fenêtre « running sans adaptateur » : une demande d'arrêt trouve
    soit une ligne queued (annulée directement, `demarrer()` refuse), soit
    l'adaptateur vivant."""
    try:
        try:
            await handle.demarrer()
        except traitements.AnnuleAvantDemarrage:
            return TRAME_ANNULEE
        llm_service = get_llm_service()
        usage_trame: dict[str, int] = {}
        raw_response = await llm_service.generate_content(
            usage_sink=usage_trame,
            prompt=build_outline_prompt(titre, brief),
        )
        enregistrer_usage_llm(llm_service, usage_trame, f"document:{document_id}", brief or titre, raw_response)
        try:
            parsed_sections = parse_outline_response(raw_response)
        except ValueError:
            await _terminer_temoin(handle, EtatTache.FAILED, error="Trame illisible")
            raise TrameIllisible() from None
        # Dernier point où l'arrêt ne coûte rien : rien n'est écrit.
        if await handle.annulation_demandee():
            await _terminer_temoin(handle, EtatTache.CANCELLED)
            return TRAME_ANNULEE
        ecriture = asyncio.ensure_future(_ecrire_la_trame(document_id, parsed_sections, ids_initiales))
        try:
            sections = await asyncio.shield(ecriture)
        except asyncio.CancelledError:
            # Point de non-retour franchi : la persistance acquise vaut succès.
            sections = await ecriture
        # Revue COCO 0.69.0 (finding 5) : la clôture DONE est elle aussi à
        # l'abri d'une annulation tardive ; après la persistance, le résultat
        # reste un succès et la réponse renvoie la trame.
        cloture = asyncio.ensure_future(_terminer_temoin(handle, EtatTache.DONE))
        try:
            await asyncio.shield(cloture)
        except asyncio.CancelledError:
            await cloture
        return sections
    except asyncio.CancelledError:
        await _terminer_temoin(handle, EtatTache.CANCELLED)
        return TRAME_ANNULEE
    except TrameIllisible:
        raise
    except TrameOccupee:
        await _terminer_temoin(handle, EtatTache.FAILED, error="Sections rédigées pendant la génération")
        raise
    except Exception as exc:
        await _terminer_temoin(handle, EtatTache.FAILED, error=str(exc)[:200])
        raise


async def _lancer_la_generation(
    handle: traitements.TraitementHandle,
    document_id: str,
    titre: str,
    brief: str | None,
    ids_initiales: frozenset[str] = frozenset(),
) -> "asyncio.Task[list[SectionResponse] | _TrameAnnulee]":
    """La porteuse détachée, enrôlée pour l'annulation AVANT son premier pas
    (elle fait elle-même QUEUED → RUNNING). Une annulation arrivée avant
    tourne en `TRAME_ANNULEE` ; une annulation qui la touche avant son premier
    pas est close par `_clore_si_orpheline`."""
    porteuse = asyncio.create_task(_generer_la_trame(handle, document_id, titre, brief, ids_initiales))
    _PORTEUSES.add(porteuse)
    porteuse.add_done_callback(_PORTEUSES.discard)
    porteuse.add_done_callback(functools.partial(_clore_si_orpheline, handle))
    await handle.lier_adaptateur(task_registry.AnnulationParTacheAsyncio(porteuse))
    return porteuse


def _reponse_code(status_code: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"code": code, "message": message})


@router.post("/{document_id}/outline", response_model=None)
async def generate_outline(
    document_id: str,
    corps: OutlineRequest | None = None,
    session: AsyncSession = Depends(get_session),
) -> list[SectionResponse] | JSONResponse:
    """
    Génère la trame (plan détaillé) d'un document via le LLM.

    Garde-fou anti-régénération silencieuse : si le document a déjà des
    sections non vides (statut différent de 'vide' OU contenu non vide),
    refuse avec 409 SANS APPELER LE LLM - la création manuelle de section
    reste possible pour compléter une trame existante.

    P-056 (ronde B2, design V2 après revue COCO) : la génération est un
    traitement `document_outline` du registre, annulable depuis « Travaux »
    ou depuis l'Atelier. Pas de fail-open : sans registre, pas de LLM (503).
    Deux générations simultanées du même document : 409 `outline_in_progress`.
    Annulation avant écriture : 409 `outline_cancelled`, zéro section.
    Annulation pendant l'écriture : la trame existe, le traitement est DONE.
    Une déconnexion du client n'arrête rien : la porteuse est détachée.
    """
    document = await _get_document_or_404(session, document_id)
    existing_result = await session.execute(
        select(DocumentSection).where(DocumentSection.document_id == document_id)
    )
    sections_initiales = existing_result.scalars().all()
    if any(s.status != "vide" or s.content != "" for s in sections_initiales):
        raise HTTPException(status_code=409, detail=_MESSAGE_SECTIONS_REDIGEES)
    ids_initiales = frozenset(s.id for s in sections_initiales)

    if await traitements.actif_pour("document_outline", document_id):
        return _reponse_code(409, "outline_in_progress", "Une génération de trame est déjà en cours pour ce document.")

    titre, brief = document.title, document.brief
    try:
        handle = await traitements.creer_traitement(
            type="document_outline",
            label=f"Trame : {titre[:60]}",
            entity_id=document_id,
            id=str(corps.task_id) if corps and corps.task_id else None,
        )
    except traitements.IdentifiantDejaPris:
        return _reponse_code(409, "task_id_taken", "Cet identifiant de traitement est déjà utilisé.")
    except Exception:
        logger.warning("Suivi indisponible pour la trame de %s", document_id, exc_info=True)
        return _reponse_code(503, "suivi_indisponible", "Suivi des traitements indisponible : la génération n'a pas été lancée.")

    porteuse = await _lancer_la_generation(handle, document_id, titre, brief, ids_initiales)

    # Aucune connexion tenue pendant l'attente du modèle (leçon B-653).
    await session.close()
    try:
        resultat = await asyncio.shield(porteuse)
    except TrameIllisible:
        raise HTTPException(status_code=502, detail="Trame illisible, réessaie.") from None
    except TrameOccupee:
        raise HTTPException(status_code=409, detail=_MESSAGE_SECTIONS_REDIGEES) from None
    except asyncio.CancelledError:
        if porteuse.cancelled():
            # La porteuse a été annulée avant son premier pas : c'est une
            # annulation de la trame, pas de la requête.
            return _reponse_code(409, "outline_cancelled", "Génération de la trame annulée.")
        raise
    except Exception as exc:
        logger.error("Génération de la trame impossible : %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=message_pour_ecran(exc, ou="pendant la génération de la trame")) from exc
    if isinstance(resultat, _TrameAnnulee):
        return _reponse_code(409, "outline_cancelled", "Génération de la trame annulée.")
    return resultat


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
    document = await _get_document_or_404(session, document_id)

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

    _touch_document(document, session)  # finding minor 9
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
    document = await _get_document_or_404(session, document_id)

    piste = DocumentPiste(
        document_id=document_id,
        section_origine_id=payload.section_origine_id,
        texte=payload.texte,
    )
    session.add(piste)
    _touch_document(document, session)  # finding minor 9
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
# EXPORT (lot C, tâche C1)
# =============================================================================
# NB routage : /{document_id}/export a deux segments de chemin, donc ne
# risque déjà aucune collision avec /{document_id} (un seul segment) -
# déclarée avant quand même, par cohérence avec la convention du fichier
# (chemins spécifiques avant les chemins génériques).


@router.get("/{document_id}/export")
async def export_document(
    document_id: str,
    format: str = "md",
    session: AsyncSession = Depends(get_session),
) -> dict[str, object]:
    """
    Exporte un document en fichier téléchargeable (md ou docx).

    Réutilise TEL QUEL le circuit d'export des conversations
    (`chat.py::export_conversation`, commit e6c25b1) : le markdown assemblé
    est écrit directement dans `registry.output_dir` - brut (format md) ou
    converti par `render_markdown_docx` (format docx, BUG-135 : conversion
    déterministe locale, plus de passage par `registry.execute("docx-pro")`
    dont le nettoyage de code pouvait tronquer le document et dont le chemin
    LLM pouvait exécuter un bloc ```python``` du contenu). Téléchargement via
    `GET /api/skills/download/{file_id}` dans les deux cas.

    Invariant de complétude (même principe que `reorder_sections` plus
    haut) : la trame est lue UNE SEULE FOIS (`sections` ci-dessous) et
    c'est CETTE lecture qui alimente à la fois la vérification et
    `assemble_markdown` - jamais une deuxième requête qui pourrait diverger
    de la première. Contrairement à la réorganisation (qui compare à un
    ensemble d'ids reçu du client), la seule source d'ids possible ici est
    la base elle-même : le garde-fou est donc structurel (single-read),
    pas un scénario de désaccord réel à ce stade du design.

    Document sans aucune section non-orpheline non vide -> 400 (« rien à
    exporter »). Format inconnu -> 400.
    """
    from uuid import uuid4

    from app.services.skills import get_skills_registry
    from app.services.skills.markdown_docx import render_markdown_docx

    fmt = (format or "md").lower()
    if fmt not in ("md", "docx"):
        raise HTTPException(
            status_code=400,
            detail=f"Format non supporté : {fmt}. Formats disponibles : md, docx.",
        )

    document = await _get_document_or_404(session, document_id)

    sections_result = await session.execute(
        select(DocumentSection)
        .where(DocumentSection.document_id == document_id)
        .order_by(DocumentSection.order)
    )
    sections = list(sections_result.scalars().all())

    non_orphan_with_content = [s for s in sections if not s.orphan and s.content.strip()]
    if not non_orphan_with_content:
        raise HTTPException(
            status_code=400,
            detail="Document vide : rien à exporter.",
        )

    markdown = assemble_markdown(document, sections)
    registry = get_skills_registry()

    # Fichier écrit directement dans le dossier des documents générés (même
    # convention de nommage {titre}_{id8}.{ext} que export_conversation,
    # retrouvé par le download endpoint via glob même sans cache).
    file_id = str(uuid4())
    safe_title = "".join(c if c.isalnum() or c in " -_" else "_" for c in document.title)[
        :50
    ].strip()
    file_name = f"{safe_title}_{file_id[:8]}.{fmt}"
    output_path = registry.output_dir / file_name

    if fmt == "docx":
        from app.services.export_profile import load_export_profile

        profile, profile_warning = load_export_profile()
        if profile_warning:
            logger.warning("Export DOCX : %s", profile_warning)
        render_markdown_docx(markdown, output_path, profile=profile)
    else:
        output_path.write_text(markdown, encoding="utf-8")

    return {
        "success": True,
        "format": fmt,
        "file_name": file_name,
        "download_url": f"/api/skills/download/{file_id}",
    }


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
