# Story E3-03 : Implémenter l'indexation dans Qdrant

## Description

En tant que **système**,
Je veux **indexer les mémoires dans Qdrant**,
Afin de **permettre la recherche sémantique rapide**.

## Contexte technique

- **Composants impactés** : Backend Python, Qdrant
- **Dépendances** : E1-04, E3-01, E3-02
- **Fichiers concernés** :
  - `src/backend/therese/services/memory_index.py` (nouveau)
  - `src/backend/therese/vector/client.py` (màj)

## Critères d'acceptation

- [ ] Service d'indexation mémoire → Qdrant
- [ ] Payload structuré (id, type, content, tags, dates)
- [ ] Upsert (création ou mise à jour)
- [ ] Suppression synchronisée avec SQLite
- [ ] Batch indexation pour import
- [ ] Performance < 50ms par indexation

## Notes techniques

### Service d'indexation

```python
# therese/services/memory_index.py
from qdrant_client.models import PointStruct, Filter, FieldCondition, MatchValue
from .embedding import embedding_service
from ..vector.client import get_qdrant_client

COLLECTION_NAME = "memories"


class MemoryIndexService:
    def __init__(self):
        self.client = get_qdrant_client()

    async def index_memory(self, memory: "Memory") -> str:
        """Indexe une mémoire dans Qdrant"""
        # Générer l'embedding
        embedding = await embedding_service.embed(memory.content)

        # Préparer le payload
        payload = {
            "memory_id": memory.id,
            "type": memory.type,
            "category": memory.category,
            "content_preview": memory.content[:200],
            "tags": memory.tags,
            "contact_id": memory.contact_id,
            "project_id": memory.project_id,
            "source": memory.source,
            "confidence": memory.confidence,
            "created_at": memory.created_at.isoformat(),
        }

        # Upsert dans Qdrant
        point_id = memory.embedding_id or memory.id
        self.client.upsert(
            collection_name=COLLECTION_NAME,
            points=[PointStruct(
                id=point_id,
                vector=embedding,
                payload=payload
            )]
        )

        return point_id

    async def index_batch(self, memories: list["Memory"]) -> list[str]:
        """Indexe plusieurs mémoires en batch"""
        if not memories:
            return []

        # Générer tous les embeddings en batch
        contents = [m.content for m in memories]
        embeddings = await embedding_service.embed_batch(contents)

        # Préparer les points
        points = []
        point_ids = []
        for memory, embedding in zip(memories, embeddings):
            point_id = memory.embedding_id or memory.id
            point_ids.append(point_id)
            points.append(PointStruct(
                id=point_id,
                vector=embedding,
                payload={
                    "memory_id": memory.id,
                    "type": memory.type,
                    "category": memory.category,
                    "content_preview": memory.content[:200],
                    "tags": memory.tags,
                    "contact_id": memory.contact_id,
                    "project_id": memory.project_id,
                    "source": memory.source,
                    "confidence": memory.confidence,
                    "created_at": memory.created_at.isoformat(),
                }
            ))

        # Upsert batch
        self.client.upsert(
            collection_name=COLLECTION_NAME,
            points=points
        )

        return point_ids

    async def delete_memory(self, memory_id: str):
        """Supprime une mémoire de l'index"""
        self.client.delete(
            collection_name=COLLECTION_NAME,
            points_selector=[memory_id]
        )

    async def delete_by_filter(
        self,
        contact_id: str | None = None,
        project_id: str | None = None
    ):
        """Supprime les mémoires liées à un contact ou projet"""
        conditions = []
        if contact_id:
            conditions.append(
                FieldCondition(key="contact_id", match=MatchValue(value=contact_id))
            )
        if project_id:
            conditions.append(
                FieldCondition(key="project_id", match=MatchValue(value=project_id))
            )

        if conditions:
            self.client.delete(
                collection_name=COLLECTION_NAME,
                points_selector=Filter(must=conditions)
            )

    async def reindex_all(self, memories: list["Memory"]):
        """Réindexe toute la mémoire (pour migration)"""
        # Vider la collection
        self.client.delete(
            collection_name=COLLECTION_NAME,
            points_selector=Filter(must=[])  # Tous les points
        )
        # Réindexer par batch de 100
        batch_size = 100
        for i in range(0, len(memories), batch_size):
            batch = memories[i:i + batch_size]
            await self.index_batch(batch)


# Singleton
memory_index_service = MemoryIndexService()
```

### Hook SQLModel pour synchronisation auto

```python
# therese/models/memory.py
from sqlmodel import event

@event.listens_for(Memory, "after_insert")
def after_memory_insert(mapper, connection, target):
    """Indexe automatiquement après insertion"""
    import asyncio
    asyncio.create_task(memory_index_service.index_memory(target))

@event.listens_for(Memory, "after_update")
def after_memory_update(mapper, connection, target):
    """Réindexe après mise à jour"""
    import asyncio
    asyncio.create_task(memory_index_service.index_memory(target))

@event.listens_for(Memory, "after_delete")
def after_memory_delete(mapper, connection, target):
    """Supprime de l'index après suppression"""
    import asyncio
    asyncio.create_task(memory_index_service.delete_memory(target.id))
```

### Tests

```python
# tests/test_memory_index.py
import pytest
from therese.services.memory_index import memory_index_service
from therese.models.memory import Memory

@pytest.mark.asyncio
async def test_index_memory():
    memory = Memory(
        type="fact",
        content="Ludo utilise Claude Code",
        tags=["IA", "tools"]
    )
    point_id = await memory_index_service.index_memory(memory)
    assert point_id == memory.id

@pytest.mark.asyncio
async def test_index_batch():
    memories = [
        Memory(type="fact", content=f"Mémoire {i}")
        for i in range(10)
    ]
    point_ids = await memory_index_service.index_batch(memories)
    assert len(point_ids) == 10
```

## Estimation

- **Complexité** : M
- **Points** : 5

## Definition of Done

- [ ] Indexation unitaire fonctionne
- [ ] Batch indexation fonctionne
- [ ] Suppression synchronisée
- [ ] Hooks SQLModel actifs
- [ ] Tests passent

---

*Sprint : 3*
*Assigné : Agent Dev Backend*
