"""
THÉRÈSE v2 - Services Package

Business logic and external service integrations.
"""

from app.services.embeddings import (
    EmbeddingsService,
    get_embeddings_service,
    embed_text,
    embed_texts,
)
from app.services.qdrant import (
    QdrantService,
    get_qdrant_service,
    init_qdrant,
    close_qdrant,
)
from app.services.llm import (
    LLMService,
    LLMConfig,
    LLMProvider,
    ContextWindow,
    Message as LLMMessage,
    get_llm_service,
)
from app.services.skills import (
    init_skills,
    close_skills,
    get_skills_registry,
    SkillsRegistry,
)

__all__ = [
    # Embeddings
    "EmbeddingsService",
    "get_embeddings_service",
    "embed_text",
    "embed_texts",
    # Qdrant
    "QdrantService",
    "get_qdrant_service",
    "init_qdrant",
    "close_qdrant",
    # LLM
    "LLMService",
    "LLMConfig",
    "LLMProvider",
    "ContextWindow",
    "LLMMessage",
    "get_llm_service",
    # Skills
    "init_skills",
    "close_skills",
    "get_skills_registry",
    "SkillsRegistry",
]
