"""
THÉRÈSE v2 - Agent Message Bus

Bus de messages inter-agents basé sur asyncio.Queue.
Zero dépendance externe (pas de Redis, pas de RabbitMQ).
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class AgentMessage:
    """Message échangé entre agents ou avec l'utilisateur."""

    sender: str  # "user", "katia", "zezette", "system"
    recipient: str  # "user", "katia", "zezette", "swarm"
    type: str  # "request", "spec", "implementation_result", "review", "feedback", "clarification"
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))


class AgentMessageBus:
    """Bus de messages asynchrone pour la communication inter-agents."""

    def __init__(self) -> None:
        self._queues: dict[str, asyncio.Queue[AgentMessage | None]] = {}

    def _get_queue(self, agent_id: str) -> asyncio.Queue[AgentMessage | None]:
        if agent_id not in self._queues:
            self._queues[agent_id] = asyncio.Queue()
        return self._queues[agent_id]

    async def send(self, message: AgentMessage) -> None:
        """Envoie un message à un agent."""
        queue = self._get_queue(message.recipient)
        await queue.put(message)
        logger.debug(f"Bus: {message.sender} → {message.recipient} ({message.type})")

    async def receive(self, agent_id: str, timeout: float | None = None) -> AgentMessage | None:
        """Attend un message pour un agent. Retourne None si timeout ou signal d'arrêt."""
        queue = self._get_queue(agent_id)
        try:
            if timeout:
                return await asyncio.wait_for(queue.get(), timeout=timeout)
            return await queue.get()
        except asyncio.TimeoutError:
            return None

    async def stop(self, agent_id: str) -> None:
        """Envoie un signal d'arrêt à un agent."""
        queue = self._get_queue(agent_id)
        await queue.put(None)

    def clear(self) -> None:
        """Vide toutes les queues."""
        self._queues.clear()
