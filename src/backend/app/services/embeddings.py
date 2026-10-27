"""
THÉRÈSE v2 - Embeddings Service

Generates embeddings for semantic search using sentence-transformers.
"""

import asyncio
import logging
from functools import lru_cache
from typing import TYPE_CHECKING, Any, Sequence

from app.config import settings

if TYPE_CHECKING:
    from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

# B-1337 : le code distant d'un modèle s'exécute avec les droits de
# l'utilisateur. Seul le modèle par défaut a une révision auditée (cycle 15,
# docs/SECURITE-DEPENDANCES-CYCLE15.md) : modèle et code y sont épinglés, le
# code de nomic-ai/nomic-bert-2048 vivant dans un autre dépôt (code_revision).
_REVISIONS_AUDITEES: dict[str, tuple[str, str]] = {
    "nomic-ai/nomic-embed-text-v1.5": (
        "e9b6763023c676ca8431644204f50c2b100d9aab",  # modèle
        "7710840340a098cfb869c4f65e87cf2b1b70caca",  # code (nomic-bert-2048)
    ),
}


def _options_de_chargement(nom_modele: str) -> dict[str, Any]:
    """Révisions épinglées du modèle audité ; aucun code distant pour un autre."""
    revisions = _REVISIONS_AUDITEES.get(nom_modele)
    if revisions is None:
        logger.warning(
            "Modèle d'embeddings sans révision auditée (%s) : chargé sans code distant",
            nom_modele,
        )
        return {"trust_remote_code": False}
    revision_modele, revision_code = revisions
    return {
        "trust_remote_code": True,
        "revision": revision_modele,
        "model_kwargs": {"code_revision": revision_code},
        "config_kwargs": {"code_revision": revision_code},
    }


class EmbeddingsService:
    """Service for generating text embeddings."""

    _instance: "EmbeddingsService | None" = None
    _model: "SentenceTransformer | None" = None

    def __new__(cls) -> "EmbeddingsService":
        """Singleton pattern for embedding model."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @property
    def model(self) -> "SentenceTransformer":
        """Lazy load the embedding model.

        US-016 : l'import de sentence_transformers (qui tire torch, plusieurs
        secondes + centaines de Mo) est différé ICI - importer le module
        embeddings ne coûte plus rien tant qu'on n'embedde pas.
        """
        if self._model is None:
            from sentence_transformers import SentenceTransformer

            logger.info(f"Loading embedding model: {settings.embedding_model}")
            self._model = SentenceTransformer(
                settings.embedding_model,
                device="cpu",  # Force CPU : MPS (Metal) crash silencieusement sur certains Mac (M4 Max)
                **_options_de_chargement(settings.embedding_model),
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
