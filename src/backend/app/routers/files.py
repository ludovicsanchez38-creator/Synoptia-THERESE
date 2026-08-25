"""
THÉRÈSE v2 - Files Router

Endpoints for file management and indexing.
"""

import asyncio
import contextlib
import logging
import os
import shutil
from pathlib import Path
from typing import Awaitable, Callable

from app.config import settings
from app.models.database import get_session, get_session_context
from app.models.entities import FileMetadata
from app.models.processing import EtatTache as EtatTacheTraitement
from app.models.schemas import FileIndexRequest, FileResponse
from app.services.indexation import (
    IndexationAbandonnee,
    extract_text_async,
    index_payload,
    remplacer_puis_indexer,
)
from app.services.traitements import TraitementHandle
from fastapi import APIRouter, Depends, Form, HTTPException, Query, Request, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from starlette.concurrency import run_in_threadpool

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/", response_model=list[FileResponse])
async def list_files(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_session),
):
    """List all indexed files."""
    result = await session.execute(
        select(FileMetadata)
        .order_by(FileMetadata.indexed_at.desc())
        .offset(offset)
        .limit(limit)
    )
    files = result.scalars().all()

    return [
        FileResponse(
            id=f.id,
            path=f.path,
            name=f.name,
            extension=f.extension,
            size=f.size,
            mime_type=f.mime_type,
            chunk_count=f.chunk_count,
            indexed_at=f.indexed_at,
            created_at=f.created_at,
            scope=f.scope,
            scope_id=f.scope_id,
        )
        for f in files
    ]


async def _executer_avec_suivi(
    *,
    label: str,
    entity_id: str,
    project_id: str | None,
    est_deconnecte: Callable[[], Awaitable[bool]] | None,
    executer: Callable[[Callable[[], Awaitable[bool]]], Awaitable[FileResponse]],
) -> FileResponse:
    """Enveloppe de surface (0.47) : l'indexation est un ProcessingTask.

    Le cœur n'enrôle JAMAIS (project.sync et le chat l'appellent aussi) :
    seules les surfaces `/index` et `/upload` passent ici. Fail-open sur le
    suivi - une panne de la table ne doit pas empêcher d'indexer.
    """
    from app.services import task_registry, traitements

    handle: "traitements.TraitementHandle | None" = None
    try:
        handle = await traitements.creer_traitement(
            type="indexation",
            label=label,
            entity_id=entity_id,
            project_id=project_id,
        )
    except Exception:
        logger.warning(
            "Suivi indisponible pour l'indexation de %s", label, exc_info=True
        )

    arret = asyncio.Event()

    async def _abandonnee() -> bool:
        # L'arrêt au panneau OU la déconnexion du client : mêmes points
        # d'abandon dans le cœur.
        if arret.is_set():
            return True
        return bool(est_deconnecte and await est_deconnecte())

    # Second panel de revue : le suivi est un TÉMOIN, jamais un acteur.
    # Une panne du suivi (SQLite occupée) ne doit ni empêcher d'indexer,
    # ni transformer un succès en 500, ni un 409 d'annulation en panne.
    suivi_bancal = False
    if handle is not None:
        try:
            await handle.demarrer()
            # L'extraction déjà lancée va à son terme (un thread ne
            # s'interrompt pas) : on note la demande, les étapes suivantes
            # la consultent.
            await handle.lier_adaptateur(
                task_registry.TravailNonInterruptible(arret.set)
            )
        except traitements.AnnuleAvantDemarrage:
            # demander_arret a déjà posé CANCELLED durable.
            raise IndexationAbandonnee(
                f"Indexation de {label} annulée avant démarrage"
            )
        except Exception:
            # Passe 2 de revue (P2-2) : ne PAS clore en failed - l'indexation
            # va peut-être réussir. Passe 3 (P3-5) : la clôture RETENTE
            # demarrer avant done, pour que la ligne dise la vérité.
            suivi_bancal = True
            logger.warning(
                "Suivi en panne au démarrage pour %s : indexation sans "
                "annulation possible", label, exc_info=True,
            )

    # Passe 4 de revue (P4-2) : le SUPERVISEUR (travail + clôture) part
    # détaché en UN bloc - une annulation du porteur pendant la clôture
    # vivante laissait une fenêtre à zéro terminaison (ligne running).
    # Le porteur ne fait qu'attendre ; l'état final est TOUJOURS posé par
    # le superviseur, que le porteur vive ou meure.
    superviseur: "asyncio.Task[FileResponse]" = asyncio.ensure_future(
        _travailler_et_clore(executer, _abandonnee, handle, label, suivi_bancal)
    )
    _travaux_en_cours.add(superviseur)
    superviseur.add_done_callback(_consommer_issue_superviseur)
    return await asyncio.shield(superviseur)


def _consommer_issue_superviseur(superviseur: "asyncio.Task[object]") -> None:
    """P5-2 : quand le porteur est mort, plus personne n'attend le
    superviseur - consommer son exception (l'état durable est déjà posé)."""
    _travaux_en_cours.discard(superviseur)
    if superviseur.cancelled():
        return
    issue = superviseur.exception()
    if issue is not None and not isinstance(
        issue, (IndexationAbandonnee, HTTPException)
    ):
        logger.warning(
            "Superviseur d'indexation terminé en échec", exc_info=issue
        )


async def _travailler_et_clore(
    executer: "Callable[[Callable[[], Awaitable[bool]]], Awaitable[FileResponse]]",
    abandonnee: "Callable[[], Awaitable[bool]]",
    handle: "TraitementHandle | None",
    label: str,
    suivi_bancal: bool,
) -> FileResponse:
    """Exécute le geste ET pose l'état final - insensible au sort du
    porteur HTTP (passe 4, P4-2)."""
    try:
        reponse = await executer(abandonnee)
    except IndexationAbandonnee:
        if handle is not None:
            with contextlib.suppress(Exception):
                await handle.terminer(EtatTacheTraitement.CANCELLED)
        raise
    except HTTPException as e:
        if handle is not None:
            with contextlib.suppress(Exception):
                await handle.terminer(
                    EtatTacheTraitement.FAILED, error=str(e.detail)[:200]
                )
        raise
    except Exception as e:
        if handle is not None:
            with contextlib.suppress(Exception):
                await handle.terminer(
                    EtatTacheTraitement.FAILED, error=str(e)[:200]
                )
        raise
    if handle is not None:
        await _clore_succes(handle, label, suivi_bancal)
    return reponse


# Travaux d'indexation et clôtures détachés (références fortes).
_travaux_en_cours: set["asyncio.Task[object]"] = set()


async def _clore_succes(
    handle: "TraitementHandle", label: str, suivi_bancal: bool
) -> None:
    """Clôture d'une indexation réussie - la ligne doit dire la vérité.

    Passe 3 (P3-5) : si le démarrage du suivi avait raté (ligne restée
    queued), demander_arret a pu la clore cancelled entre-temps - retenter
    demarrer expose ce cas : la ligne est alors ANNOTÉE plutôt que de
    mentir en silence.
    """
    if suivi_bancal:
        from app.services import traitements

        try:
            await handle.demarrer()
        except traitements.AnnuleAvantDemarrage:
            with contextlib.suppress(Exception):
                await handle.progresser(
                    step="indexée malgré l'arrêt demandé (suivi dégradé "
                    "au démarrage)",
                    progress=1.0,
                )
            logger.warning(
                "La ligne de %s dit « annulé » mais l'indexation a réussi "
                "(suivi dégradé au démarrage) - annotée", label,
            )
            return
        except Exception:
            logger.debug("Retry demarrer impossible pour %s", label)
    # Passe 2 de revue (P2-1) : progresser et terminer ne partagent pas
    # leur sort.
    with contextlib.suppress(Exception):
        await handle.progresser(progress=1.0)
    try:
        await handle.terminer(EtatTacheTraitement.DONE)
    except Exception:
        logger.warning(
            "Clôture du suivi impossible pour %s : l'indexation a "
            "pourtant réussi", label, exc_info=True,
        )




async def indexer_avec_suivi(
    path: str,
    *,
    est_deconnecte: Callable[[], Awaitable[bool]] | None = None,
    scope: str = "global",
    scope_id: str | None = None,
    perimetre_provisoire: bool = False,
) -> FileResponse:
    """Le chemin du bouton Indexer et du trombone, avec suivi au panneau."""
    return await _executer_avec_suivi(
        label=Path(path).name,
        entity_id=path,
        project_id=scope_id if scope == "project" else None,
        est_deconnecte=est_deconnecte,
        executer=lambda abandonnee: index_payload(
            path,
            est_abandonnee=abandonnee,
            scope=scope,
            scope_id=scope_id,
            perimetre_provisoire=perimetre_provisoire,
        ),
    )


@router.post("/index", response_model=FileResponse)
async def index_file(
    request: FileIndexRequest,
    http_request: Request,
):
    """
    Index a file for RAG.

    Extracts content, chunks it, and stores embeddings in Qdrant.

    BUG-165 : quand l'appel vient du composeur du chat, il porte la
    conversation d'origine. Le périmètre en est DÉRIVÉ, jamais dicté par le
    client : c'est le même résolveur que celui du contexte du chat, donc les
    deux ne peuvent pas diverger. Sans conversation, le fichier reste global,
    ce qui est le bon défaut pour l'explorateur de fichiers.
    """
    scope, scope_id = "global", None
    # Le provisoire est demandé explicitement par l'appelant (le composeur du
    # chat quand sa conversation n'existe pas encore côté backend). L'absence de
    # conversation ne suffit pas : l'explorateur est dans ce cas et son
    # périmètre est voulu.
    perimetre_provisoire = request.perimetre_provisoire
    if request.conversation_id:
        from app.routers.chat import perimetre_de_piece_jointe

        async with get_session_context() as session:
            scope, scope_id, conversation_connue = await perimetre_de_piece_jointe(
                request.conversation_id, session
            )
        # Une conversation RÉELLEMENT connue donne un périmètre voulu. Un
        # identifiant encore local (conversation pas synchronisée) ne doit pas
        # figer un périmètre orphelin : il reste rectifiable à l'envoi.
        perimetre_provisoire = not conversation_connue

    try:
        return await indexer_avec_suivi(
            request.path,
            est_deconnecte=http_request.is_disconnected,
            scope=scope,
            scope_id=scope_id,
            perimetre_provisoire=perimetre_provisoire,
        )
    except IndexationAbandonnee as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.get("/{file_id}", response_model=FileResponse)
async def get_file(
    file_id: str,
    session: AsyncSession = Depends(get_session),
):
    """Get file metadata."""
    result = await session.execute(
        select(FileMetadata).where(FileMetadata.id == file_id)
    )
    file_meta = result.scalar_one_or_none()

    if not file_meta:
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(
        id=file_meta.id,
        path=file_meta.path,
        name=file_meta.name,
        extension=file_meta.extension,
        size=file_meta.size,
        mime_type=file_meta.mime_type,
        chunk_count=file_meta.chunk_count,
        indexed_at=file_meta.indexed_at,
        created_at=file_meta.created_at,
        scope=file_meta.scope,
        scope_id=file_meta.scope_id,
    )


@router.delete("/{file_id}")
async def delete_file(
    file_id: str,
    session: AsyncSession = Depends(get_session),
):
    """Remove a file from the index (does not delete the actual file)."""
    result = await session.execute(
        select(FileMetadata).where(FileMetadata.id == file_id)
    )
    file_meta = result.scalar_one_or_none()

    if not file_meta:
        raise HTTPException(status_code=404, detail="File not found")

    # 0.45 : retrait par le service fail-closed. CHANGEMENT VOLONTAIRE de
    # comportement sur erreur : l'ancien code avalait l'échec Qdrant puis
    # supprimait quand même la ligne - des vecteurs orphelins restaient servis
    # par la recherche, sans plus aucune métadonnée pour les retrouver. Une
    # erreur Qdrant répond désormais 500 et la ligne reste : l'état demeure
    # réparable en réessayant.
    from app.services.retrait_index import retirer_de_lindex

    try:
        await retirer_de_lindex(file_id_attendu=file_id)
    except Exception as e:
        logger.error(f"Retrait d'index en échec pour {file_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Le retrait de l'index a échoué, rien n'a été supprimé - réessaie.",
        )

    return {"deleted": True, "id": file_id}


@router.get("/{file_id}/content")
async def get_file_content(
    file_id: str,
    session: AsyncSession = Depends(get_session),
):
    """
    Get the extracted content of an indexed file.

    Returns the parsed text content (not the raw file).
    """
    result = await session.execute(
        select(FileMetadata).where(FileMetadata.id == file_id)
    )
    file_meta = result.scalar_one_or_none()

    if not file_meta:
        raise HTTPException(status_code=404, detail="File not found")

    file_path = Path(file_meta.path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File no longer exists on disk")

    # Utiliser extract_text() (déjà importé) pour supporter PDF, DOCX, XLSX, etc.
    # Hors boucle d'événements (finding F3 de la revue du 27/07) : relire un gros
    # PDF gelait l'application au même titre que l'indexation.
    try:
        content = await extract_text_async(file_path)
        # extract_text() retourne None pour les formats non supportés ou fichiers vides
        if content is None:
            content = ""
    except ValueError as e:
        # ex : fichier > 50 Mo → HTTP 413
        raise HTTPException(status_code=413, detail=str(e))
    except Exception as e:
        logger.error(f"Error reading file {file_path}: {e}")
        raise HTTPException(status_code=500, detail="Error reading file content")

    return {
        "id": file_id,
        "path": file_meta.path,
        "name": file_meta.name,
        "content": content[:10000],  # Limit content size
        "truncated": len(content) > 10000,
    }


# Extensions autorisées pour l'upload vers un projet
ALLOWED_UPLOAD_EXTENSIONS = {".md", ".txt", ".csv", ".xlsx", ".pdf", ".docx"}


@router.post("/upload", response_model=FileResponse)
async def upload_file(
    file: UploadFile,
    http_request: Request,
    project_id: str = Form(...),
    session: AsyncSession = Depends(get_session),
):
    """
    Upload un fichier et l'associe à un projet.

    Le fichier est sauvegardé dans ~/.therese/projects/{project_id}/files/
    puis indexé dans Qdrant pour la recherche sémantique.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="Nom de fichier manquant")

    # Valider l'extension
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_UPLOAD_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Extension {ext} non supportée. Extensions autorisées : {', '.join(sorted(ALLOWED_UPLOAD_EXTENSIONS))}",
        )

    # Vérifier que le projet existe
    from app.models.entities import Project
    result = await session.execute(
        select(Project).where(Project.id == project_id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Projet non trouvé")

    # Créer le dossier de stockage
    # Revue 0.40.1 (F3) : suit THERESE_DATA_DIR (prod inchangée : ~/.therese)
    therese_dir = Path(settings.data_dir) / "projects" / project_id / "files"
    therese_dir.mkdir(parents=True, exist_ok=True)

    # Sauvegarder le fichier (copie disque hors boucle d'événements - finding F3
    # de la revue du 27/07 : une pièce jointe de projet volumineuse gelait
    # l'application exactement comme l'indexation du chat).
    # Dépôt + indexation par le service central (0.45) : la copie disque
    # entre SOUS le verrou du chemin - elle se faisait avant toute prise de
    # verrou, et ce pipeline maison dupliquait le cœur avec deux défauts :
    # transaction longue pendant l'extraction, et vecteurs supprimés AVANT que
    # le nouveau contenu soit prêt (l'inverse de l'invariant N1). Déposer un
    # fichier DANS un projet est un geste explicite : périmètre voulu.
    dest_path = therese_dir / file.filename
    temporaire = dest_path.with_name(dest_path.name + ".therese-tmp")

    def _copier_vers_temporaire() -> None:
        with temporaire.open("wb") as f:
            shutil.copyfileobj(file.file, f)

    def _remplacer() -> None:
        # Écriture ATOMIQUE : une erreur de copie ne doit jamais tronquer le
        # fichier en place pendant que son index reste servi (revue jalon).
        os.replace(temporaire, dest_path)

    def _deposer_avec_abandon(abandonnee):
        async def _deposer() -> None:
            try:
                await run_in_threadpool(_copier_vers_temporaire)
                # Passe 2 de revue (P2-8) : le VRAI point de non-retour est
                # os.replace. La copie d'un gros fichier est longue - un
                # arrêt posé pendant doit préserver la version en place.
                if abandonnee is not None and await abandonnee():
                    raise IndexationAbandonnee(
                        f"Dépôt de {dest_path.name} abandonné avant le "
                        "remplacement"
                    )
                await run_in_threadpool(_remplacer)
            except IndexationAbandonnee:
                raise
            except Exception as e:
                logger.error(f"Erreur sauvegarde fichier : {e}")
                raise HTTPException(
                    status_code=500,
                    detail="Erreur lors de la sauvegarde du fichier",
                )
            finally:
                temporaire.unlink(missing_ok=True)

        return _deposer

    try:
        return await _executer_avec_suivi(
            label=dest_path.name,
            entity_id=str(dest_path),
            project_id=project_id,
            est_deconnecte=http_request.is_disconnected,
            executer=lambda abandonnee: remplacer_puis_indexer(
                str(dest_path), _deposer_avec_abandon(abandonnee),
                est_abandonnee=abandonnee,
                scope="project", scope_id=project_id,
            ),
        )
    except IndexationAbandonnee as e:
        raise HTTPException(status_code=409, detail=str(e))
