"""
THÉRÈSE v2 - Qdrant Vector Store Service

Manages vector storage for semantic memory search.
"""

import asyncio
import logging
from pathlib import Path
from typing import Any
from uuid import uuid4

from app.config import settings
from app.services.embeddings import embed_text, embed_texts
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PointStruct,
    VectorParams,
)

logger = logging.getLogger(__name__)


class QdrantService:
    """Service for Qdrant vector database operations."""

    _instance: "QdrantService | None" = None
    _client: QdrantClient | None = None
    _initialized: bool = False

    def __new__(cls) -> "QdrantService":
        """Singleton pattern for Qdrant client."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @property
    def client(self) -> QdrantClient:
        """Get the Qdrant client, initializing if needed."""
        if self._client is None:
            self._init_client()
        return self._client  # type: ignore

    def _init_client(self) -> None:
        """Initialize Qdrant client in embedded mode."""
        qdrant_path = settings.qdrant_path
        if qdrant_path is None:
            qdrant_path = settings.data_dir / "qdrant"

        # Ensure directory exists
        qdrant_dir = Path(qdrant_path)
        qdrant_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Initializing Qdrant at {qdrant_path}")
        try:
            self._client = QdrantClient(path=str(qdrant_path))
        except RuntimeError as e:
            if "already accessed" in str(e):
                # Lock stale laissé par un ancien process non tué proprement
                lock_file = qdrant_dir / ".lock"
                if lock_file.exists():
                    logger.warning("Qdrant verrouillé par un ancien process, suppression du lock stale")
                    lock_file.unlink()
                # Réessayer après nettoyage
                self._client = QdrantClient(path=str(qdrant_path))
            else:
                raise
        self._ensure_collection()
        self._initialized = True
        logger.info("Qdrant initialized successfully")

    def _ensure_collection(self) -> None:
        """Ensure the memory collection exists."""
        collection_name = settings.qdrant_collection
        collections = self.client.get_collections().collections
        exists = any(c.name == collection_name for c in collections)

        if not exists:
            logger.info(f"Creating collection: {collection_name}")
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=settings.embedding_dimensions,
                    distance=Distance.COSINE,
                ),
            )
            logger.info(f"Collection {collection_name} created")

    def add_memory(
        self,
        text: str,
        memory_type: str,
        entity_id: str,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """
        Add a memory to the vector store.

        Args:
            text: Text content to embed and store
            memory_type: Type of memory (contact, project, conversation, etc.)
            entity_id: ID of the related entity in SQLite
            metadata: Additional metadata

        Returns:
            ID of the created point
        """
        point_id = str(uuid4())
        embedding = embed_text(text)

        payload = {
            "text": text,
            "type": memory_type,
            "entity_id": entity_id,
            **(metadata or {}),
        }

        self.client.upsert(
            collection_name=settings.qdrant_collection,
            points=[
                PointStruct(
                    id=point_id,
                    vector=embedding,
                    payload=payload,
                )
            ],
        )

        logger.debug(f"Added memory {point_id} for {memory_type}:{entity_id}")
        return point_id

    def add_memories(
        self,
        items: list[dict[str, Any]],
    ) -> list[str]:
        """
        Add multiple memories in batch.

        Args:
            items: List of dicts with keys: text, memory_type, entity_id, metadata

        Returns:
            List of created point IDs
        """
        if not items:
            return []

        texts = [item["text"] for item in items]
        embeddings = embed_texts(texts)
        point_ids = []

        points = []
        for item, embedding in zip(items, embeddings, strict=True):
            point_id = str(uuid4())
            point_ids.append(point_id)

            payload = {
                "text": item["text"],
                "type": item["memory_type"],
                "entity_id": item["entity_id"],
                **(item.get("metadata") or {}),
            }

            points.append(
                PointStruct(
                    id=point_id,
                    vector=embedding,
                    payload=payload,
                )
            )

        self.client.upsert(
            collection_name=settings.qdrant_collection,
            points=points,
        )

        logger.info(f"Added {len(points)} memories in batch")
        return point_ids

    def search(
        self,
        query: str,
        memory_types: list[str] | None = None,
        limit: int = 10,
        score_threshold: float = 0.7,
        scope: str | None = None,
        scope_id: str | None = None,
        include_global: bool = True,
    ) -> list[dict[str, Any]]:
        """
        Search for similar memories with scope filtering (E3-05).

        Args:
            query: Search query text
            memory_types: Filter by memory types (None = all types)
            limit: Maximum results to return
            score_threshold: Minimum similarity score
            scope: Filter by scope (global, project, conversation)
            scope_id: Filter by scope_id (required if scope != global)
            include_global: Include global items when filtering by scope

        Returns:
            List of matching memories with scores
        """
        embedding = embed_text(query)

        # Build filter conditions
        conditions = []

        # Filter by memory types
        if memory_types:
            conditions.append(
                Filter(
                    should=[
                        FieldCondition(key="type", match=MatchValue(value=t))
                        for t in memory_types
                    ]
                )
            )

        # Filter by scope (E3-05)
        if scope:
            scope_conditions = [
                Filter(
                    must=[
                        FieldCondition(key="scope", match=MatchValue(value=scope)),
                        FieldCondition(key="scope_id", match=MatchValue(value=scope_id or "")),
                    ]
                )
            ]
            if include_global:
                scope_conditions.append(
                    FieldCondition(key="scope", match=MatchValue(value="global"))
                )
            conditions.append(Filter(should=scope_conditions))

        # Combine all conditions
        query_filter = None
        if conditions:
            query_filter = Filter(must=conditions)

        # Use query_points (qdrant-client >= 1.7)
        results = self.client.query_points(
            collection_name=settings.qdrant_collection,
            query=embedding,
            query_filter=query_filter,
            limit=limit,
            score_threshold=score_threshold,
        ).points

        return [
            {
                "id": str(hit.id),
                "score": hit.score,
                "text": hit.payload.get("text") if hit.payload else None,
                "type": hit.payload.get("type") if hit.payload else None,
                "entity_id": hit.payload.get("entity_id") if hit.payload else None,
                "scope": hit.payload.get("scope") if hit.payload else None,
                "scope_id": hit.payload.get("scope_id") if hit.payload else None,
                "metadata": {
                    k: v
                    for k, v in (hit.payload or {}).items()
                    if k not in ("text", "type", "entity_id", "scope", "scope_id")
                },
            }
            for hit in results
        ]

    def delete_by_entity(self, entity_id: str) -> int:
        """
        Delete all memories for an entity.

        Args:
            entity_id: Entity ID to delete memories for

        Returns:
            Number of deleted points
        """
        # First search for matching points
        results = self.client.scroll(
            collection_name=settings.qdrant_collection,
            scroll_filter=Filter(
                must=[FieldCondition(key="entity_id", match=MatchValue(value=entity_id))]
            ),
            limit=1000,
        )[0]

        if not results:
            return 0

        point_ids = [str(r.id) for r in results]
        self.client.delete(
            collection_name=settings.qdrant_collection,
            points_selector=point_ids,
        )

        logger.info(f"Deleted {len(point_ids)} memories for entity {entity_id}")
        return len(point_ids)

    def delete_by_scope(self, scope: str, scope_id: str) -> int:
        """
        Delete all memories for a specific scope (E3-06).

        Args:
            scope: Scope type (project, conversation, contact)
            scope_id: ID of the scoped entity

        Returns:
            Number of deleted points
        """
        results = self.client.scroll(
            collection_name=settings.qdrant_collection,
            scroll_filter=Filter(
                must=[
                    FieldCondition(key="scope", match=MatchValue(value=scope)),
                    FieldCondition(key="scope_id", match=MatchValue(value=scope_id)),
                ]
            ),
            limit=1000,
        )[0]

        if not results:
            return 0

        point_ids = [str(r.id) for r in results]
        self.client.delete(
            collection_name=settings.qdrant_collection,
            points_selector=point_ids,
        )

        logger.info(f"Deleted {len(point_ids)} memories for scope {scope}:{scope_id}")
        return len(point_ids)

    def get_stats(self) -> dict[str, Any]:
        """Get collection statistics."""
        info = self.client.get_collection(settings.qdrant_collection)
        return {
            "points_count": info.points_count,
            "status": info.status.name if info.status else "unknown",
        }

    # --- Async wrappers (Phase 2.4) ---

    async def async_add_memory(
        self,
        text: str,
        memory_type: str,
        entity_id: str,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Async wrapper for add_memory."""
        return await asyncio.to_thread(
            self.add_memory, text, memory_type, entity_id, metadata
        )

    async def async_add_memories(
        self,
        items: list[dict[str, Any]],
    ) -> list[str]:
        """Async wrapper for add_memories."""
        return await asyncio.to_thread(self.add_memories, items)

    async def async_search(
        self,
        query: str,
        memory_types: list[str] | None = None,
        limit: int = 10,
        score_threshold: float = 0.7,
        scope: str | None = None,
        scope_id: str | None = None,
        include_global: bool = True,
    ) -> list[dict[str, Any]]:
        """Async wrapper for search."""
        return await asyncio.to_thread(
            self.search, query, memory_types, limit, score_threshold,
            scope, scope_id, include_global
        )

    async def async_delete_by_entity(self, entity_id: str) -> int:
        """Async wrapper for delete_by_entity."""
        return await asyncio.to_thread(self.delete_by_entity, entity_id)

    async def async_delete_by_scope(self, scope: str, scope_id: str) -> int:
        """Async wrapper for delete_by_scope."""
        return await asyncio.to_thread(self.delete_by_scope, scope, scope_id)

    def close(self) -> None:
        """Close the Qdrant client."""
        if self._client:
            self._client.close()
            self._client = None
            self._initialized = False
            logger.info("Qdrant client closed")


# Global instance
_qdrant_service: QdrantService | None = None


def get_qdrant_service() -> QdrantService:
    """Get the Qdrant service instance."""
    global _qdrant_service
    if _qdrant_service is None:
        _qdrant_service = QdrantService()
    return _qdrant_service


async def init_qdrant() -> None:
    """Initialize Qdrant (called at startup)."""
    service = get_qdrant_service()
    # Access client to trigger initialization
    _ = service.client


async def close_qdrant() -> None:
    """Close Qdrant (called at shutdown)."""
    global _qdrant_service
    if _qdrant_service:
        _qdrant_service.close()
        _qdrant_service = None
