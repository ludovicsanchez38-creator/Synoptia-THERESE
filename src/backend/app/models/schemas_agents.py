"""
THÉRÈSE v2 - Agent System Schemas

Pydantic models for the agent API endpoints.
"""

from datetime import datetime

from pydantic import BaseModel


class AgentRequest(BaseModel):
    """Demande utilisateur au swarm d'agents."""

    message: str
    source_path: str | None = None  # Chemin du repo local (optionnel, utilise la config sinon)


class AgentTaskResponse(BaseModel):
    """Réponse détaillée d'une tâche agent."""

    id: str
    title: str
    description: str | None = None
    status: str
    branch_name: str | None = None
    diff_summary: str | None = None
    files_changed: list[str] | None = None
    agent_model: str | None = None
    tokens_used: int = 0
    cost_eur: float = 0.0
    error: str | None = None
    created_at: datetime
    updated_at: datetime
    merged_at: datetime | None = None


class AgentTaskListResponse(BaseModel):
    """Liste de tâches agents."""

    tasks: list[AgentTaskResponse]
    total: int


class AgentStreamChunk(BaseModel):
    """Chunk SSE envoyé pendant le traitement d'une demande agent."""

    type: str  # agent_start, agent_chunk, agent_done, handoff, tool_use, test_result, review_ready, explanation, done, error
    agent: str | None = None  # "katia" ou "zezette"
    content: str = ""
    task_id: str | None = None
    phase: str | None = None  # spec, analysis, implementation, testing, review, done
    branch: str | None = None
    files_changed: list[str] | None = None
    tool_name: str | None = None
    diff_summary: str | None = None


class DiffFileResponse(BaseModel):
    """Diff d'un fichier individuel."""

    file_path: str
    change_type: str
    diff_hunk: str | None = None
    explanation: str | None = None
    additions: int = 0
    deletions: int = 0


class DiffResponse(BaseModel):
    """Réponse de diff complète pour review."""

    task_id: str
    branch_name: str | None = None
    summary: str | None = None
    files: list[DiffFileResponse]
    total_additions: int = 0
    total_deletions: int = 0


class AgentModelInfo(BaseModel):
    """Informations sur un modèle disponible."""

    id: str
    name: str
    provider: str
    recommended: bool = False


class AgentConfigResponse(BaseModel):
    """Configuration des agents."""

    katia_enabled: bool = True
    zezette_enabled: bool = True
    katia_model: str = "claude-sonnet-4-6"
    zezette_model: str = "claude-sonnet-4-6"
    source_path: str | None = None
    available_models: list[AgentModelInfo] = []


class AgentConfigUpdate(BaseModel):
    """Mise à jour de la configuration des agents."""

    katia_enabled: bool | None = None
    zezette_enabled: bool | None = None
    katia_model: str | None = None
    zezette_model: str | None = None
    source_path: str | None = None


class AgentStatusResponse(BaseModel):
    """Statut du système d'agents."""

    git_available: bool = False
    repo_detected: bool = False
    repo_path: str | None = None
    current_branch: str | None = None
    active_tasks: int = 0
    katia_ready: bool = False
    zezette_ready: bool = False
