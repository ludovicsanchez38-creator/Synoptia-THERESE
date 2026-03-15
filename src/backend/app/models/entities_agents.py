"""
THÉRÈSE v2 - Agent System Entities

Database models for the embedded AI agent system (Atelier).
"""

from datetime import UTC, datetime

from app.models.entities import generate_uuid
from sqlmodel import Field, SQLModel


class AgentTask(SQLModel, table=True):
    """Tâche traitée par le swarm d'agents."""

    __tablename__ = "agent_tasks"

    id: str = Field(default_factory=generate_uuid, primary_key=True)
    title: str
    description: str | None = None
    status: str = Field(default="pending", index=True)  # pending, in_progress, review, approved, rejected, merged
    branch_name: str | None = None
    source_path: str | None = None
    diff_summary: str | None = None
    diff_patch: str | None = None  # Unified diff complet
    files_changed: str | None = None  # JSON array de chemins
    agent_model: str | None = None
    tokens_used: int = Field(default=0)
    cost_eur: float = Field(default=0.0)
    error: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    merged_at: datetime | None = None


class AgentMessage(SQLModel, table=True):
    """Message dans une conversation agent (user, thérèse, zézette, system)."""

    __tablename__ = "agent_messages"

    id: str = Field(default_factory=generate_uuid, primary_key=True)
    task_id: str = Field(foreign_key="agent_tasks.id", index=True)
    agent: str  # "katia", "zezette", "user", "system"
    role: str  # "user", "assistant", "system"
    content: str
    tool_calls: str | None = None  # JSON array
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class CodeChange(SQLModel, table=True):
    """Changement de fichier individuel dans une tâche agent."""

    __tablename__ = "code_changes"

    id: str = Field(default_factory=generate_uuid, primary_key=True)
    task_id: str = Field(foreign_key="agent_tasks.id", index=True)
    file_path: str
    change_type: str  # added, modified, deleted
    diff_hunk: str | None = None
    explanation: str | None = None
    approved: bool | None = None  # None = en attente, True = approuvé, False = rejeté
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
