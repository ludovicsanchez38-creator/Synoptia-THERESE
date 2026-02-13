"""
THÉRÈSE v2 - Embeddings Service

Generates embeddings for semantic search using sentence-transformers.
"""

import asyncio
import logging
from functools import lru_cache
from typing import Sequence

from app.config import settings
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


class EmbeddingsService:
    """Service for generating text embeddings."""

    _instance: "EmbeddingsService | None" = None
    _model: SentenceTransformer | None = None

    def __new__(cls) -> "EmbeddingsService":
        """Singleton pattern for embedding model."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @property
    def model(self) -> SentenceTransformer:
        """Lazy load the embedding model."""
        if self._model is None:
            logger.info(f"Loading embedding model: {settings.embedding_model}")
            self._model = SentenceTransformer(
                settings.embedding_model,
                trust_remote_code=True,  # Required for nomic models
                device="cpu",  # Force CPU : MPS (Metal) crash silencieusement sur certains Mac (M4 Max)
            )
            logger.info("Embedding model loaded successfully")
        return self._model

    def embed_text(self, text: str) -> list[float]:
        """
        Generate embedding for a single text.

        Args:
            text: Text to embed

        Returns:
            Embedding vector as list of floats
        """
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding.tolist()

    def embed_texts(self, texts: Sequence[str]) -> list[list[float]]:
        """
        Generate embeddings for multiple texts.

        Args:
            texts: Texts to embed

        Returns:
            List of embedding vectors
        """
        embeddings = self.model.encode(list(texts), convert_to_numpy=True)
        return embeddings.tolist()

    def get_dimension(self) -> int:
        """Get the embedding dimension."""
        return self.model.get_sentence_embedding_dimension()


@lru_cache
def get_embeddings_service() -> EmbeddingsService:
    """Get cached embeddings service instance."""
    return EmbeddingsService()


# Convenience functions (synchronous)
def embed_text(text: str) -> list[float]:
    """Generate embedding for a single text."""
    return get_embeddings_service().embed_text(text)


def embed_texts(texts: Sequence[str]) -> list[list[float]]:
    """Generate embeddings for multiple texts."""
    return get_embeddings_service().embed_texts(texts)


# Async convenience functions (Sprint 2 - PERF-2.5)
async def embed_text_async(text: str) -> list[float]:
    """
    Generate embedding for a single text asynchronously.

    Uses asyncio.to_thread to avoid blocking the event loop
    since SentenceTransformer.encode() is CPU-bound.
    """
    service = get_embeddings_service()
    return await asyncio.to_thread(service.embed_text, text)


async def embed_texts_async(texts: Sequence[str]) -> list[list[float]]:
    """
    Generate embeddings for multiple texts asynchronously.

    Uses asyncio.to_thread to avoid blocking the event loop
    since SentenceTransformer.encode() is CPU-bound.
    """
    service = get_embeddings_service()
    return await asyncio.to_thread(service.embed_texts, texts)


async def preload_embedding_model() -> None:
    """
    Pre-charge le modele d'embeddings au demarrage de l'application.

    Evite le blocage de 5-10s lors du premier appel utilisateur.
    Utilise asyncio.to_thread car le chargement est CPU-bound.
    """
    def _load():
        service = get_embeddings_service()
        # Acces a la property .model pour declencher le lazy loading
        _ = service.model
        return service.get_dimension()

    dim = await asyncio.to_thread(_load)
    logger.info(f"Embedding model pre-loaded (dimension={dim})")
