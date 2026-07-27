"""
THÉRÈSE v2 - Files Router

Endpoints for file management and indexing.
"""

import asyncio
import logging
import shutil
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.config import settings
from app.models.database import get_session, get_session_context
from app.models.entities import FileMetadata
from app.models.schemas import FileIndexRequest, FileResponse
from app.services.file_parser import chunk_text, extract_text, get_file_metadata
from app.services.path_security import validate_indexable_file
from app.services.qdrant import get_qdrant_service
from fastapi import APIRouter, Depends, Form, HTTPException, Query, Request, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from starlette.concurrency import run_in_threadpool

logger = logging.getLogger(__name__)

router = APIRouter()


# BUG-155 (27/07/2026) : extraction et découpage sont des traitements CPU/disque
# synchrones. Appelés directement depuis une route `async`, ils bloquaient la
# boucle d'événements : pendant l'indexation d'un gros document, plus aucune
# requête n'était servie (chat, emails, agenda) et l'application semblait figée.
# On les déporte dans le pool de threads.


# Un dépôt massif lançait autant d'encodages simultanés que de fichiers
# (revue du 27/07, finding F4). Deux à la fois suffisent sur une machine de
# bureau et laissent de la place au reste de l'application.
MAX_INDEXATIONS_SIMULTANEES = 2
INDEX_SEMAPHORE = asyncio.Semaphore(MAX_INDEXATIONS_SIMULTANEES)

# `FileMetadata.path` est UNIQUE : deux demandes sur le même fichier en même
# temps levaient une contrainte d'intégrité (finding F1).
# Chaque entrée porte son verrou et le nombre de demandes qui s'y rattachent :
# purger sur `locked()` seul supprimerait le verrou alors qu'un appel attend
# encore, et le suivant en créerait un second pour le même chemin.
_verrous_par_chemin: dict[str, list[Any]] = {}


@asynccontextmanager
async def _verrou_de_chemin(chemin: str) -> AsyncIterator[None]:
    entree = _verrous_par_chemin.get(chemin)
    if entree is None:
        entree = [asyncio.Lock(), 0]
        _verrous_par_chemin[chemin] = entree
    entree[1] += 1
    try:
        async with entree[0]:
            yield
    finally:
        entree[1] -= 1
        if entree[1] == 0 and _verrous_par_chemin.get(chemin) is entree:
            _verrous_par_chemin.pop(chemin, None)


async def extract_text_async(file_path: Path) -> str:
    """Extrait le texte d'un fichier sans bloquer la boucle d'événements."""
    return await run_in_threadpool(extract_text, file_path)


async def chunk_text_async(text: str, chunk_size: int = 1000, overlap: int = 200) -> list[str]:
    """Découpe le texte en fragments sans bloquer la boucle d'événements."""
    return await run_in_threadpool(
        lambda: list(chunk_text(text, chunk_size=chunk_size, overlap=overlap))
    )


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
        )
        for f in files
    ]


async def index_payload(
    path: str,
    est_abandonnee: Callable[[], Awaitable[bool]] | None = None,
) -> FileResponse:
    """Indexe un fichier sans jamais tenir la base ni la boucle d'événements.

    Remédiation de la revue du 27/07/2026 (findings F1, F2 et F4) :

    - La métadonnée est écrite et **committée** avant le travail lourd. Elle
      restait auparavant dans une transaction ouverte pendant l'extraction et
      les embeddings ; SQLite n'ayant qu'un seul écrivain (busy_timeout de 5 s),
      une écriture concurrente - l'enregistrement d'un message de chat, par
      exemple - pouvait échouer pendant l'indexation d'un gros document.
    - Un verrou par chemin sérialise deux demandes portant sur le même fichier
      (`FileMetadata.path` est UNIQUE : la course levait une contrainte).
    - Un sémaphore borne les encodages simultanés : un dépôt massif lançait
      autant d'encodages que de fichiers.
    - `est_abandonnee` permet de renoncer avant l'étape la plus coûteuse quand
      plus personne n'attend la réponse. L'extraction déjà lancée, elle, va à
      son terme : un thread ne s'interrompt pas.
    """
    # Validation securite du chemin + type de fichier (SEC-002/003)
    try:
        file_path = validate_indexable_file(path)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not file_path.is_file():
        raise HTTPException(status_code=400, detail="Path is not a file")

    metadata = get_file_metadata(file_path)

    async with _verrou_de_chemin(str(file_path)):
        # 1. Transaction COURTE : enregistrer le fichier, puis rendre la main.
        async with get_session_context() as session:
            result = await session.execute(
                select(FileMetadata).where(FileMetadata.path == str(file_path))
            )
            existing = result.scalar_one_or_none()
            if existing:
                existing.size = metadata["size"]
                existing.mime_type = metadata["mime_type"]
                existing.updated_at = datetime.now(UTC)
                file_meta = existing
                reindexation = True
                # Mémorisés pour ne rien détruire si le nouveau traitement
                # n'aboutit pas (N1).
                chunk_count_existant = existing.chunk_count or 0
                indexed_at_existant = existing.indexed_at
            else:
                file_meta = FileMetadata(
                    path=str(file_path),
                    name=metadata["name"],
                    extension=metadata["extension"],
                    size=metadata["size"],
                    mime_type=metadata["mime_type"],
                )
                session.add(file_meta)
                reindexation = False
                chunk_count_existant = 0
                indexed_at_existant = None
            await session.commit()
            await session.refresh(file_meta)
            file_id = file_meta.id
            file_name = file_meta.name
            created_at = file_meta.created_at
            extension = file_meta.extension

        # 2. Travail lourd, hors transaction et hors boucle d'événements.
        #
        # Contre-vérification du 27/07 (N1) : les anciens vecteurs étaient
        # supprimés AVANT l'extraction. Une annulation ou une extraction en
        # échec laissait alors un fichier sans aucun vecteur, présenté comme
        # indexé. La suppression n'a lieu qu'une fois le nouveau contenu prêt
        # et l'écriture décidée : jusque-là, l'index existant reste valide.
        text_content = await extract_text_async(file_path)
        chunk_count = chunk_count_existant
        indexed_at = indexed_at_existant
        ecriture_faite = False

        if text_content and not (est_abandonnee and await est_abandonnee()):
            chunks = await chunk_text_async(text_content, chunk_size=1000, overlap=200)
            items = [
                {
                    "text": chunk,
                    "memory_type": "file",
                    "entity_id": file_id,
                    "metadata": {
                        "name": file_name,
                        "path": str(file_path),
                        "chunk_index": i,
                        "total_chunks": len(chunks),
                    },
                }
                for i, chunk in enumerate(chunks)
            ]
            if items and not (est_abandonnee and await est_abandonnee()):
                async with INDEX_SEMAPHORE:
                    # L'attente du sémaphore peut durer : re-consulter l'abandon
                    # juste avant d'écrire (finding F1 resté ouvert).
                    if not (est_abandonnee and await est_abandonnee()):
                        if reindexation:
                            await get_qdrant_service().async_delete_by_entity(file_id)
                        await get_qdrant_service().async_add_memories(items)
                        logger.info(f"Indexed {len(chunks)} chunks for file {file_name}")
                        chunk_count = len(chunks)
                        indexed_at = datetime.now(UTC)
                        ecriture_faite = True
        elif not text_content:
            logger.warning(f"No text extracted from {file_path}")
            if reindexation:
                await get_qdrant_service().async_delete_by_entity(file_id)
            chunk_count = 0
            indexed_at = datetime.now(UTC)
            ecriture_faite = True

        # 3. Transaction COURTE : consigner le résultat. Rien à écrire si la
        # demande a été abandonnée : l'état précédent reste la vérité.
        if ecriture_faite:
            async with get_session_context() as session:
                a_jour = await session.get(FileMetadata, file_id)
                if a_jour is None:
                    # N2 : le fichier a été supprimé pendant le traitement. Ne
                    # pas laisser de vecteurs orphelins ni annoncer un succès.
                    await get_qdrant_service().async_delete_by_entity(file_id)
                    raise HTTPException(
                        status_code=409,
                        detail="Le fichier a été supprimé pendant son indexation.",
                    )
                a_jour.chunk_count = chunk_count
                a_jour.indexed_at = indexed_at
                await session.commit()

    return FileResponse(
        id=file_id,
        path=str(file_path),
        name=file_name,
        extension=extension,
        size=metadata["size"],
        mime_type=metadata["mime_type"],
        chunk_count=chunk_count,
        indexed_at=indexed_at,
        created_at=created_at,
    )


@router.post("/index", response_model=FileResponse)
async def index_file(
    request: FileIndexRequest,
    http_request: Request,
):
    """
    Index a file for RAG.

    Extracts content, chunks it, and stores embeddings in Qdrant.
    """
    return await index_payload(request.path, est_abandonnee=http_request.is_disconnected)


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

    # Contre-vérification du 27/07 (N2) : sans ce verrou, la suppression pouvait
    # s'intercaler pendant une indexation du même fichier - la ligne disparaissait
    # et l'indexation écrivait ensuite ses vecteurs, restés orphelins.
    async with _verrou_de_chemin(file_meta.path):
        # Remove embeddings from Qdrant
        try:
            qdrant = get_qdrant_service()
            deleted_count = await qdrant.async_delete_by_entity(file_id)
            logger.info(f"Deleted {deleted_count} embeddings for file {file_id}")
        except Exception as e:
            logger.warning(f"Failed to delete embeddings: {e}")

        await session.delete(file_meta)
        await session.commit()

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
    dest_path = therese_dir / file.filename

    def _copier_sur_disque() -> None:
        with dest_path.open("wb") as f:
            shutil.copyfileobj(file.file, f)

    try:
        await run_in_threadpool(_copier_sur_disque)
    except Exception as e:
        logger.error(f"Erreur sauvegarde fichier : {e}")
        raise HTTPException(status_code=500, detail="Erreur lors de la sauvegarde du fichier")

    # Récupérer les métadonnées
    metadata = get_file_metadata(dest_path)

    # Créer ou mettre à jour l'entrée en base
    result = await session.execute(
        select(FileMetadata).where(FileMetadata.path == str(dest_path))
    )
    existing = result.scalar_one_or_none()

    if existing:
        qdrant = get_qdrant_service()
        await qdrant.async_delete_by_entity(existing.id)
        existing.size = metadata["size"]
        existing.mime_type = metadata["mime_type"]
        existing.scope = "project"
        existing.scope_id = project_id
        existing.updated_at = datetime.now(UTC)
        file_meta = existing
    else:
        file_meta = FileMetadata(
            path=str(dest_path),
            name=metadata["name"],
            extension=metadata["extension"],
            size=metadata["size"],
            mime_type=metadata["mime_type"],
            scope="project",
            scope_id=project_id,
        )
        session.add(file_meta)
        await session.flush()

    # Extraire et indexer le contenu (hors boucle d'événements - finding F3)
    text_content = await extract_text_async(dest_path)
    if text_content:
        chunks = await chunk_text_async(text_content, chunk_size=1000, overlap=200)
        qdrant = get_qdrant_service()
        items = []
        for i, chunk in enumerate(chunks):
            items.append({
                "text": chunk,
                "memory_type": "file",
                "entity_id": file_meta.id,
                "metadata": {
                    "name": file_meta.name,
                    "path": str(dest_path),
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                    "project_id": project_id,
                },
            })
        if items:
            await qdrant.async_add_memories(items)
            logger.info(f"Indexé {len(chunks)} chunks pour {file_meta.name} (projet {project_id})")
        file_meta.chunk_count = len(chunks)
    else:
        file_meta.chunk_count = 0

    file_meta.indexed_at = datetime.now(UTC)
    await session.commit()
    await session.refresh(file_meta)

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
    )
