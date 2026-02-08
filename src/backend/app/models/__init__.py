"""
THÉRÈSE v2 - Models Package

SQLModel entities and Pydantic schemas.
"""

from app.models.entities import (
    Contact,
    Conversation,
    FileMetadata,
    Message,
    Preference,
    Project,
)
from app.models.schemas import (
    ChatRequest,
    ChatResponse,
    MemorySearchRequest,
    MemorySearchResponse,
)

__all__ = [
    "Contact",
    "Project",
    "Conversation",
    "Message",
    "FileMetadata",
    "Preference",
    "ChatRequest",
    "ChatResponse",
    "MemorySearchRequest",
    "MemorySearchResponse",
]
