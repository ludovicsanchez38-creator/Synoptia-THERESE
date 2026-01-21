# Story E3-04 : Créer la recherche hybride (keyword + semantic)

## Description

En tant que **utilisateur**,
Je veux **rechercher dans ma mémoire par mots-clés et par sens**,
Afin de **retrouver les informations pertinentes rapidement**.

## Contexte technique

- **Composants impactés** : Backend Python, SQLite FTS5, Qdrant
- **Dépendances** : E1-03, E3-02, E3-03
- **Fichiers concernés** :
  - `src/backend/therese/services/memory_search.py` (nouveau)
  - `src/backend/therese/api/routes/search.py` (nouveau)

## Critères d'acceptation

- [ ] Recherche sémantique via Qdrant (cosine similarity)
- [ ] Recherche keyword via SQLite FTS5
- [ ] Fusion des résultats avec RRF (Reciprocal Rank Fusion)
- [ ] Filtres par type, catégorie, dates
- [ ] Performance < 200ms pour requête complète
- [ ] Top-k configurable (défaut 5)

## Notes techniques

### Configuration SQLite FTS5

```sql
-- Migration pour FTS5
CREATE VIRTUAL TABLE memories_fts USING fts5(
    content,
    content=memories,
    content_rowid=rowid
);

-- Triggers pour sync
CREATE TRIGGER memories_ai AFTER INSERT ON memories BEGIN
    INSERT INTO memories_fts(rowid, content) VALUES (new.rowid, new.content);
END;

CREATE TRIGGER memories_ad AFTER DELETE ON memories BEGIN
    INSERT INTO memories_fts(memories_fts, rowid, content) VALUES('delete', old.rowid, old.content);
END;

CREATE TRIGGER memories_au AFTER UPDATE ON memories BEGIN
    INSERT INTO memories_fts(memories_fts, rowid, content) VALUES('delete', old.rowid, old.content);
    INSERT INTO memories_fts(rowid, content) VALUES (new.rowid, new.content);
END;
```

### Service de recherche

```python
# therese/services/memory_search.py
from dataclasses import dataclass
from qdrant_client.models import Filter, FieldCondition, MatchValue, Range
from .embedding import embedding_service
from ..vector.client import get_qdrant_client
from ..database.connection import get_session

@dataclass
class SearchResult:
    memory_id: str
    content: str
    type: str
    score: float
    source: str  # "semantic" | "keyword" | "hybrid"


class MemorySearchService:
    def __init__(self):
        self.qdrant = get_qdrant_client()

    async def search(
        self,
        query: str,
        limit: int = 5,
        type_filter: str | None = None,
        category_filter: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        hybrid: bool = True
    ) -> list[SearchResult]:
        """Recherche hybride dans la mémoire"""

        if hybrid:
            # Exécuter les deux recherches en parallèle
            import asyncio
            semantic_task = self._search_semantic(
                query, limit * 2, type_filter, category_filter
            )
            keyword_task = self._search_keyword(
                query, limit * 2, type_filter, category_filter
            )
            semantic_results, keyword_results = await asyncio.gather(
                semantic_task, keyword_task
            )

            # Fusionner avec RRF
            return self._rrf_fusion(semantic_results, keyword_results, limit)
        else:
            return await self._search_semantic(
                query, limit, type_filter, category_filter
            )

    async def _search_semantic(
        self,
        query: str,
        limit: int,
        type_filter: str | None = None,
        category_filter: str | None = None
    ) -> list[SearchResult]:
        """Recherche sémantique via Qdrant"""
        # Générer l'embedding de la query
        query_embedding = await embedding_service.embed(query)

        # Construire les filtres
        filter_conditions = []
        if type_filter:
            filter_conditions.append(
                FieldCondition(key="type", match=MatchValue(value=type_filter))
            )
        if category_filter:
            filter_conditions.append(
                FieldCondition(key="category", match=MatchValue(value=category_filter))
            )

        query_filter = Filter(must=filter_conditions) if filter_conditions else None

        # Rechercher
        results = self.qdrant.search(
            collection_name="memories",
            query_vector=query_embedding,
            limit=limit,
            query_filter=query_filter
        )

        return [
            SearchResult(
                memory_id=r.payload["memory_id"],
                content=r.payload["content_preview"],
                type=r.payload["type"],
                score=r.score,
                source="semantic"
            )
            for r in results
        ]

    async def _search_keyword(
        self,
        query: str,
        limit: int,
        type_filter: str | None = None,
        category_filter: str | None = None
    ) -> list[SearchResult]:
        """Recherche keyword via SQLite FTS5"""
        with get_session() as session:
            # Construire la requête FTS5
            sql = """
                SELECT m.id, m.content, m.type, bm25(memories_fts) as score
                FROM memories_fts
                JOIN memories m ON memories_fts.rowid = m.rowid
                WHERE memories_fts MATCH ?
            """
            params = [query]

            if type_filter:
                sql += " AND m.type = ?"
                params.append(type_filter)
            if category_filter:
                sql += " AND m.category = ?"
                params.append(category_filter)

            sql += f" ORDER BY score LIMIT {limit}"

            results = session.execute(sql, params).fetchall()

            return [
                SearchResult(
                    memory_id=r[0],
                    content=r[1][:200],
                    type=r[2],
                    score=abs(r[3]),  # BM25 retourne des scores négatifs
                    source="keyword"
                )
                for r in results
            ]

    def _rrf_fusion(
        self,
        semantic_results: list[SearchResult],
        keyword_results: list[SearchResult],
        limit: int,
        k: int = 60  # Constante RRF
    ) -> list[SearchResult]:
        """Fusionne les résultats avec Reciprocal Rank Fusion"""
        scores: dict[str, float] = {}
        results_map: dict[str, SearchResult] = {}

        # Scores sémantiques
        for rank, result in enumerate(semantic_results):
            rrf_score = 1 / (k + rank + 1)
            scores[result.memory_id] = scores.get(result.memory_id, 0) + rrf_score
            results_map[result.memory_id] = result

        # Scores keyword
        for rank, result in enumerate(keyword_results):
            rrf_score = 1 / (k + rank + 1)
            scores[result.memory_id] = scores.get(result.memory_id, 0) + rrf_score
            if result.memory_id not in results_map:
                results_map[result.memory_id] = result

        # Trier par score fusionné
        sorted_ids = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)

        return [
            SearchResult(
                memory_id=mid,
                content=results_map[mid].content,
                type=results_map[mid].type,
                score=scores[mid],
                source="hybrid"
            )
            for mid in sorted_ids[:limit]
        ]


# Singleton
memory_search_service = MemorySearchService()
```

### Route API

```python
# therese/api/routes/search.py
from fastapi import APIRouter, Query

router = APIRouter(prefix="/search", tags=["search"])

@router.get("/memories")
async def search_memories(
    q: str = Query(..., min_length=1),
    limit: int = Query(5, ge=1, le=20),
    type: str | None = None,
    category: str | None = None,
    hybrid: bool = True
):
    results = await memory_search_service.search(
        query=q,
        limit=limit,
        type_filter=type,
        category_filter=category,
        hybrid=hybrid
    )
    return {"results": results}
```

## Estimation

- **Complexité** : M
- **Points** : 5

## Definition of Done

- [ ] Recherche sémantique fonctionne
- [ ] Recherche keyword fonctionne
- [ ] Fusion RRF retourne des résultats pertinents
- [ ] Performance < 200ms
- [ ] Tests E2E passent

---

*Sprint : 3*
*Assigné : Agent Dev Backend*
