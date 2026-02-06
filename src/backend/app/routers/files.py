"""
THÉRÈSE v2 - Files Router

Endpoints for file management and indexing.
"""

import logging
from datetime import UTC, datetime
from pathlib import Path

from app.models.database import get_session
from app.models.entities import FileMetadata
from app.models.schemas import FileIndexRequest, FileResponse
from app.services.file_parser import chunk_text, extract_text, get_file_metadata
from app.services.path_security import validate_indexable_file
from app.services.qdrant import get_qdrant_service
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

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
        )
        for f in files
    ]


@router.post("/index", response_model=FileResponse)
async def index_file(
    request: FileIndexRequest,
    session: AsyncSession = Depends(get_session),
):
    """
    Index a file for RAG.

    Extracts content, chunks it, and stores embeddings in Qdrant.
    """
    # Validation securite du chemin + type de fichier (SEC-002/003)
    try:
        file_path = validate_indexable_file(request.path)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not file_path.is_file():
        raise HTTPException(status_code=400, detail="Path is not a file")

    # Get file info
    metadata = get_file_metadata(file_path)

    # Check if already indexed
    result = await session.execute(
        select(FileMetadata).where(FileMetadata.path == str(file_path))
    )
    existing = result.scalar_one_or_none()

    if existing:
        # Delete old embeddings
        qdrant = get_qdrant_service()
        await qdrant.async_delete_by_entity(existing.id)

        # Update existing entry
        existing.size = metadata["size"]
        existing.mime_type = metadata["mime_type"]
        existing.updated_at = datetime.now(UTC)
        file_meta = existing
    else:
        # Create new entry
        file_meta = FileMetadata(
            path=str(file_path),
            name=metadata["name"],
            extension=metadata["extension"],
            size=metadata["size"],
            mime_type=metadata["mime_type"],
        )
        session.add(file_meta)
        await session.flush()  # Get the ID

    # Extract text content
    text_content = extract_text(file_path)

    if text_content:
        # Chunk the content
        chunks = list(chunk_text(text_content, chunk_size=1000, overlap=200))

        # Store embeddings in Qdrant
        qdrant = get_qdrant_service()
        items = []

        for i, chunk in enumerate(chunks):
            items.append({
                "text": chunk,
                "memory_type": "file",
                "entity_id": file_meta.id,
                "metadata": {
                    "name": file_meta.name,
                    "path": str(file_path),
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                },
            })

        if items:
            await qdrant.async_add_memories(items)
            logger.info(f"Indexed {len(chunks)} chunks for file {file_meta.name}")

        file_meta.chunk_count = len(chunks)
    else:
        file_meta.chunk_count = 0
        logger.warning(f"No text extracted from {file_path}")

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

    # TODO: Implement proper file parsing based on extension
    # For now, just read text files
    try:
        if file_meta.extension in [".txt", ".md", ".py", ".js", ".ts", ".json"]:
            content = file_path.read_text(encoding="utf-8")
        else:
            content = f"[Content extraction not yet implemented for {file_meta.extension} files]"
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
