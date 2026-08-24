"""
THÉRÈSE - Traitements longs (J1a, 31/07/2026).

Couche DURABLE du socle des tâches. Elle ne remplace pas les `asyncio.Task` :
une ligne en base ne s'annule pas. Le registre runtime
(`services/task_registry.py`) porte les adaptateurs d'annulation ; cette table
porte ce qui doit survivre à un redémarrage.

Généralise le patron d'`agent_tasks` (`entities_agents.py`), seul cycle de vie
persisté du dépôt jusqu'ici. `agent_tasks` n'est pas absorbée : elle garde sa
branche, son diff et ses événements, et référencera une tâche de traitement.
"""
from datetime import UTC, datetime

from sqlalchemy import Index
from sqlmodel import Field, SQLModel

from .entities import generate_uuid


class EtatTache:
    """États d'un traitement long.

    `CANCEL_REQUESTED` et `CANCELLED` sont volontairement distincts : demander
    l'arrêt n'est pas l'obtenir. `ActionRunner` marque aujourd'hui CANCELLED
    alors que l'appel au modèle continue (`action_agents.py:411`) - l'utilisateur
    croit le traitement arrêté pendant qu'il consomme encore. Cette confusion ne
    doit pas être généralisée au reste de l'application.
    """

    QUEUED = "queued"
    RUNNING = "running"
    CANCEL_REQUESTED = "cancel_requested"
    CANCELLED = "cancelled"
    INTERRUPTED = "interrupted"
    DONE = "done"
    FAILED = "failed"

    @classmethod
    def terminaux(cls) -> set[str]:
        """États où plus rien ne tourne. `CANCEL_REQUESTED` n'en fait pas partie."""
        return {cls.CANCELLED, cls.INTERRUPTED, cls.DONE, cls.FAILED}

    @classmethod
    def actifs(cls) -> set[str]:
        return {cls.QUEUED, cls.RUNNING, cls.CANCEL_REQUESTED}


class ProcessingTask(SQLModel, table=True):
    """Un traitement long, visible et interruptible par l'utilisateur."""

    __tablename__ = "processing_tasks"
    __table_args__ = (
        # Le panneau trie par created_at et la retention filtre dessus (0.46).
        Index("ix_processing_tasks_created_at", "created_at"),
    )

    id: str = Field(default_factory=generate_uuid, primary_key=True)

    # Nature et présentation
    type: str = Field(index=True)  # indexation | board | atelier | image | export | import | backup...
    label: str  # ce que lit l'utilisateur : « rapport.pdf », « Délibération »
    state: str = Field(default=EtatTache.QUEUED, index=True)
    step: str | None = None  # étape courante, affichée telle quelle
    progress: float | None = None  # 0..1, None = progression non mesurable

    # Rattachements (le journal et le temps par projet s'appuieront dessus)
    project_id: str | None = Field(default=None, index=True)
    conversation_id: str | None = Field(default=None, index=True)
    entity_id: str | None = None  # id métier : fichier indexé, décision, mission...

    # Cycle de vie
    run_instance_id: str = Field(index=True)  # exécution du sidecar qui l'a lancée
    heartbeat_at: datetime | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    started_at: datetime | None = None
    finished_at: datetime | None = None

    # Issue
    error: str | None = None
    resumable: bool = Field(default=False)  # vrai seulement si le type est idempotent
