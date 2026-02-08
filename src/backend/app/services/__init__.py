"""
THÉRÈSE v2 - Services Package

Business logic and external service integrations.
"""

from app.services.embeddings import (
    EmbeddingsService,
    embed_text,
    embed_texts,
    get_embeddings_service,
)
from app.services.llm import (
    ContextWindow,
    LLMConfig,
    LLMProvider,
    LLMService,
    get_llm_service,
)
from app.services.llm import (
    Message as LLMMessage,
)
from app.services.qdrant import (
    QdrantService,
    close_qdrant,
    get_qdrant_service,
    init_qdrant,
)
from app.services.skills import (
    SkillsRegistry,
    close_skills,
    get_skills_registry,
    init_skills,
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
