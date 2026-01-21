# Story E3-02 : Créer le service d'embedding (texte → vecteur)

## Description

En tant que **développeur**,
Je veux **transformer du texte en vecteurs**,
Afin de **permettre la recherche sémantique dans la mémoire**.

## Contexte technique

- **Composants impactés** : Backend Python
- **Dépendances** : E1-04 (Qdrant)
- **Fichiers concernés** :
  - `src/backend/therese/services/embedding.py` (nouveau)
  - `pyproject.toml` (màj)

## Critères d'acceptation

- [ ] Service d'embedding avec nomic-embed-text (768 dim)
- [ ] Support batch pour plusieurs textes
- [ ] Cache des embeddings récents
- [ ] Fallback vers sentence-transformers si API down
- [ ] Performance < 100ms pour un texte court
- [ ] Tests unitaires passent

## Notes techniques

### Dépendances

```bash
uv add httpx sentence-transformers
```

### Service Embedding

```python
# therese/services/embedding.py
from functools import lru_cache
import httpx
from sentence_transformers import SentenceTransformer

EMBEDDING_DIM = 768
NOMIC_MODEL = "nomic-embed-text-v1.5"
FALLBACK_MODEL = "all-MiniLM-L6-v2"  # 384 dim, rapide


class EmbeddingService:
    def __init__(self):
        self._local_model: SentenceTransformer | None = None
        self._cache: dict[str, list[float]] = {}
        self._max_cache_size = 1000

    @property
    def local_model(self) -> SentenceTransformer:
        """Lazy load du modèle local"""
        if self._local_model is None:
            self._local_model = SentenceTransformer(FALLBACK_MODEL)
        return self._local_model

    async def embed(self, text: str) -> list[float]:
        """Génère un embedding pour un texte"""
        # Check cache
        cache_key = hash(text[:100])  # Hash sur les 100 premiers chars
        if cache_key in self._cache:
            return self._cache[cache_key]

        try:
            # Essayer l'API Nomic
            embedding = await self._embed_nomic(text)
        except Exception:
            # Fallback local
            embedding = self._embed_local(text)

        # Update cache
        self._update_cache(cache_key, embedding)
        return embedding

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Génère des embeddings pour plusieurs textes"""
        try:
            return await self._embed_nomic_batch(texts)
        except Exception:
            return self._embed_local_batch(texts)

    async def _embed_nomic(self, text: str) -> list[float]:
        """Embedding via API Nomic"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api-atlas.nomic.ai/v1/embedding/text",
                json={
                    "texts": [text],
                    "model": NOMIC_MODEL,
                    "task_type": "search_document"
                },
                headers={"Authorization": f"Bearer {self._get_nomic_key()}"},
                timeout=10.0
            )
            response.raise_for_status()
            return response.json()["embeddings"][0]

    async def _embed_nomic_batch(self, texts: list[str]) -> list[list[float]]:
        """Batch embedding via API Nomic"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api-atlas.nomic.ai/v1/embedding/text",
                json={
                    "texts": texts,
                    "model": NOMIC_MODEL,
                    "task_type": "search_document"
                },
                headers={"Authorization": f"Bearer {self._get_nomic_key()}"},
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()["embeddings"]

    def _embed_local(self, text: str) -> list[float]:
        """Embedding via modèle local"""
        embedding = self.local_model.encode(text)
        # Pad to 768 if needed (fallback model is 384)
        if len(embedding) < EMBEDDING_DIM:
            embedding = list(embedding) + [0.0] * (EMBEDDING_DIM - len(embedding))
        return list(embedding)

    def _embed_local_batch(self, texts: list[str]) -> list[list[float]]:
        """Batch embedding via modèle local"""
        embeddings = self.local_model.encode(texts)
        result = []
        for emb in embeddings:
            if len(emb) < EMBEDDING_DIM:
                emb = list(emb) + [0.0] * (EMBEDDING_DIM - len(emb))
            result.append(list(emb))
        return result

    def _update_cache(self, key: int, embedding: list[float]):
        """Met à jour le cache avec éviction LRU"""
        if len(self._cache) >= self._max_cache_size:
            # Remove oldest entry
            oldest = next(iter(self._cache))
            del self._cache[oldest]
        self._cache[key] = embedding

    def _get_nomic_key(self) -> str:
        """Récupère la clé API Nomic"""
        import os
        return os.environ.get("NOMIC_API_KEY", "")


# Singleton
embedding_service = EmbeddingService()
```

### Tests

```python
# tests/test_embedding.py
import pytest
from therese.services.embedding import embedding_service

@pytest.mark.asyncio
async def test_embed_single():
    text = "THÉRÈSE est une assistante IA"
    embedding = await embedding_service.embed(text)
    assert len(embedding) == 768
    assert all(isinstance(x, float) for x in embedding)

@pytest.mark.asyncio
async def test_embed_batch():
    texts = ["Premier texte", "Deuxième texte", "Troisième texte"]
    embeddings = await embedding_service.embed_batch(texts)
    assert len(embeddings) == 3
    assert all(len(e) == 768 for e in embeddings)

@pytest.mark.asyncio
async def test_embed_cache():
    text = "Test cache"
    # First call
    emb1 = await embedding_service.embed(text)
    # Second call should hit cache
    emb2 = await embedding_service.embed(text)
    assert emb1 == emb2
```

## Estimation

- **Complexité** : M
- **Points** : 5

## Definition of Done

- [ ] Service fonctionnel avec Nomic
- [ ] Fallback local testé
- [ ] Cache actif
- [ ] Performance < 100ms
- [ ] Tests passent

---

*Sprint : 3*
*Assigné : Agent Dev Backend*
