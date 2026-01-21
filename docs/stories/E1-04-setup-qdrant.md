# Story E1-04 : Intégrer Qdrant en mode embedded

## Description

En tant que **développeur**,
Je veux **avoir Qdrant configuré en mode embedded**,
Afin de **stocker et rechercher les embeddings de la mémoire**.

## Contexte technique

- **Composants impactés** : Backend Python, Module mémoire
- **Dépendances** : E1-02 (Backend FastAPI)
- **Fichiers concernés** :
  - `src/backend/therese/vector/` (nouveau)
  - `pyproject.toml` (màj)

## Critères d'acceptation

- [ ] qdrant-client installé
- [ ] Mode embedded configuré (pas de serveur séparé)
- [ ] Collection "memories" créée avec dimension 768
- [ ] Index/search fonctionnel avec vecteurs de test
- [ ] Données stockées dans `~/.therese/data/qdrant/`
- [ ] Performance search < 100ms pour 10k vecteurs

## Notes techniques

### Installation

```bash
uv add qdrant-client
```

### Configuration Qdrant embedded

```python
# therese/vector/client.py
from pathlib import Path
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

EMBEDDING_DIM = 768  # nomic-embed-text

def get_qdrant_path() -> Path:
    qdrant_dir = Path.home() / ".therese" / "data" / "qdrant"
    qdrant_dir.mkdir(parents=True, exist_ok=True)
    return qdrant_dir

def get_qdrant_client() -> QdrantClient:
    return QdrantClient(path=str(get_qdrant_path()))

def init_collections(client: QdrantClient):
    collections = ["memories", "files", "conversations"]

    for collection in collections:
        if not client.collection_exists(collection):
            client.create_collection(
                collection_name=collection,
                vectors_config=VectorParams(
                    size=EMBEDDING_DIM,
                    distance=Distance.COSINE
                )
            )
```

### Service vectoriel

```python
# therese/vector/service.py
from qdrant_client.models import PointStruct, Filter
import uuid

class VectorService:
    def __init__(self, client: QdrantClient):
        self.client = client

    async def upsert(
        self,
        collection: str,
        vector: list[float],
        payload: dict
    ) -> str:
        point_id = str(uuid.uuid4())
        self.client.upsert(
            collection_name=collection,
            points=[PointStruct(
                id=point_id,
                vector=vector,
                payload=payload
            )]
        )
        return point_id

    async def search(
        self,
        collection: str,
        query_vector: list[float],
        limit: int = 5,
        filter: Filter | None = None
    ) -> list[dict]:
        results = self.client.search(
            collection_name=collection,
            query_vector=query_vector,
            limit=limit,
            query_filter=filter
        )
        return [
            {"id": r.id, "score": r.score, "payload": r.payload}
            for r in results
        ]

    async def delete(self, collection: str, point_id: str):
        self.client.delete(
            collection_name=collection,
            points_selector=[point_id]
        )
```

### Test de performance

```python
# tests/test_qdrant_perf.py
import time
import random

def test_search_performance(vector_service):
    # Insert 10k vectors
    for i in range(10000):
        vector = [random.random() for _ in range(768)]
        vector_service.upsert("memories", vector, {"test": i})

    # Search
    query = [random.random() for _ in range(768)]
    start = time.time()
    results = vector_service.search("memories", query, limit=5)
    elapsed = time.time() - start

    assert elapsed < 0.1  # < 100ms
    assert len(results) == 5
```

## Estimation

- **Complexité** : M
- **Points** : 5

## Definition of Done

- [ ] Qdrant embedded fonctionne
- [ ] Collections créées au démarrage
- [ ] CRUD vecteurs testé
- [ ] Performance validée (< 100ms pour 10k)

---

*Sprint : 1*
*Assigné : Agent Dev*
