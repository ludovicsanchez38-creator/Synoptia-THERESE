"""
THÉRÈSE - Registre des traitements longs (J1a, 31/07/2026).

Deux couches, volontairement séparées :

- **durable** : `ProcessingTask` en base, ce qui survit à un redémarrage ;
- **runtime** : ce module, qui garde le moyen d'ARRÊTER un traitement vivant.

Le dépôt contenait déjà quatre registres en mémoire, chacun avec sa propre
mécanique d'annulation et aucun lien entre eux :

| Registre | Fichier | Mécanique |
|---|---|---|
| `_active_generations` | `routers/chat.py:90` | drapeau consulté entre deux chunks |
| `_running_agent_tasks` | `routers/agents.py:63` | `asyncio.Task.cancel()` |
| `ActionRunner._tasks` | `services/action_agents.py:509` | `asyncio.Event` coopératif |
| flux du Board | `services/board.py:452` | annulation à la fermeture du flux |

Ces mécaniques ne sont PAS interchangeables : on ne les remplace pas, on les
enveloppe derrière un adaptateur commun.
"""
import asyncio
import logging
import uuid
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from typing import Protocol

from app.models.processing import EtatTache, ProcessingTask
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

logger = logging.getLogger(__name__)

# Identifiant de CETTE exécution du sidecar. Une tâche portant une autre
# instance et un état actif est forcément orpheline : son processus est mort.
_INSTANCE_COURANTE = uuid.uuid4().hex


def instance_courante() -> str:
    return _INSTANCE_COURANTE


class AdaptateurAnnulation(Protocol):
    """Sait interrompre un traitement d'une famille donnée."""

    async def annuler(self) -> bool:
        """Demande l'arrêt. Retourne True si le travail est réellement coupé.

        False signifie « demande transmise, arrêt non garanti » : l'appelant
        doit alors laisser la tâche en `cancel_requested`, jamais la marquer
        `cancelled`.
        """
        ...


class AnnulationParTacheAsyncio:
    """Atelier : `asyncio.Task.cancel()` coupe vraiment (`agents.py:229`)."""

    def __init__(self, tache: "asyncio.Task[object]") -> None:
        self._tache = tache

    async def annuler(self) -> bool:
        if self._tache.done():
            return True
        self._tache.cancel()
        return True


class AnnulationCooperative:
    """Actions : un drapeau consulté entre les étapes (`action_agents.py:515`).

    L'étape en cours va à son terme : l'arrêt n'est pas immédiat, donc False.
    """

    def __init__(self, poser_drapeau: Callable[[], None]) -> None:
        self._poser = poser_drapeau

    async def annuler(self) -> bool:
        self._poser()
        return False


class AnnulationParFlux:
    """Board : fermer le flux annule les conseillers (`board.py:452`)."""

    def __init__(self, fermer: Callable[[], Awaitable[None]]) -> None:
        self._fermer = fermer

    async def annuler(self) -> bool:
        await self._fermer()
        return True


class TravailNonInterruptible:
    """Extraction de fichier : un thread ne s'interrompt pas.

    `run_in_threadpool` s'appuie sur AnyIO en `abandon_on_cancel=False` : le
    traitement déjà lancé ira à son terme. On note la demande, et les étapes
    suivantes (encodage, écriture vectorielle) la consulteront.
    """

    def __init__(self, poser_drapeau: Callable[[], None]) -> None:
        self._poser = poser_drapeau

    async def annuler(self) -> bool:
        self._poser()
        return False


_adaptateurs: dict[str, AdaptateurAnnulation] = {}


def inscrire(task_id: str, adaptateur: AdaptateurAnnulation) -> None:
    _adaptateurs[task_id] = adaptateur


def retirer(task_id: str) -> None:
    _adaptateurs.pop(task_id, None)


def est_vivante(task_id: str) -> bool:
    return task_id in _adaptateurs


async def demander_annulation(task_id: str) -> bool:
    """Demande l'arrêt d'un traitement. True si le travail est réellement coupé."""
    adaptateur = _adaptateurs.get(task_id)
    if adaptateur is None:
        return False
    return await adaptateur.annuler()


async def recuperer_taches_orphelines(session: AsyncSession) -> int:
    """Passe en `interrupted` les tâches d'une exécution précédente.

    Sans ce ménage, une tâche restée « en cours » après un arrêt brutal reste
    affichée comme active pour toujours. Sur les missions d'Atelier, elle bloque
    même toute nouvelle mission (`agents.py:199`) sans pouvoir être annulée
    (409 si le processus n'est plus là, `agents.py:546`).
    """
    resultat = await session.execute(
        select(ProcessingTask).where(
            ProcessingTask.state.in_(tuple(EtatTache.actifs())),
            ProcessingTask.run_instance_id != _INSTANCE_COURANTE,
        )
    )
    orphelines = list(resultat.scalars().all())
    if not orphelines:
        return 0

    maintenant = datetime.now(UTC)
    for tache in orphelines:
        tache.state = EtatTache.INTERRUPTED
        tache.finished_at = maintenant
        tache.error = "Traitement interrompu par l'arrêt de l'application."
    await session.commit()
    logger.info("Traitements orphelins repris : %d", len(orphelines))
    return len(orphelines)
