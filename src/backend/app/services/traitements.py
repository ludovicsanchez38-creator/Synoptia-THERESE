"""Le cycle de vie des traitements longs - handle explicite (0.46).

Design V2.1 challengé deux fois. Les règles qui ne se devinent pas :

- **l'état terminal appartient au producteur.** `demander_arret()` ne pose
  jamais `cancelled` sur une running, jamais `interrupted` (réservé au
  récupérateur de redémarrage). Elle fait UNE chose : la transition atomique
  vers `cancel_requested` + la transmission à l'adaptateur.
- **une `queued` s'annule par CAS direct** vers `cancelled` - sans
  producteur, elle resterait `cancel_requested` pour toujours - et son
  `demarrer()` ultérieur est refusé (`AnnuleAvantDemarrage`).
- **`lier_adaptateur()` rejoue une demande antérieure** : la fenêtre entre
  création et enrôlement est fermée.
- **`can_cancel` devient faux dès la demande** : un second clic n'a rien à
  couper de plus.
- Pas de context manager qui infère l'état final : les familles (requête
  directe, SSE paresseux, tâche de fond) n'ont ni la même session, ni le
  même sens de `CancelledError`.
"""
import logging
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

from app.models.database import get_session_context
from app.models.processing import EtatTache, ProcessingTask
from app.services import task_registry
from app.services.task_registry import AdaptateurAnnulation
from sqlalchemy import update
from sqlmodel import select

logger = logging.getLogger(__name__)

# Seuil de VISIBILITÉ (jamais de création différée) : les générations de
# chat trop brèves n'apparaissent pas au panneau - sauf échec ou annulation.
SEUIL_VISIBILITE_S = 2
TYPES_A_SEUIL = {"chat", "deep-research", "indexation"}

# Demandes d'arrêt posées avant l'enrôlement de l'adaptateur, à rejouer.
_demandes_en_attente: set[str] = set()


class AnnuleAvantDemarrage(Exception):
    """La tâche a été annulée pendant qu'elle était en file : ne pas démarrer."""


@dataclass
class ResultatArret:
    state: str
    # accepted = demande transmise, arrêt non garanti ; stopped = coupé
    # confirmé par l'adaptateur ; unavailable = aucun adaptateur vivant.
    resultat: str
    transmise: bool


class TraitementHandle:
    def __init__(self, task_id: str) -> None:
        self.id = task_id

    async def demarrer(self) -> None:
        # Revue jalon (F1) : SELECT puis commit n'est pas un CAS - une
        # annulation intercalée laissait l'état final `running`. L'UPDATE
        # conditionnel fait foi : rowcount 0 = la transition a perdu.
        async with get_session_context() as session:
            resultat = await session.execute(
                update(ProcessingTask)
                .where(
                    ProcessingTask.id == self.id,
                    ProcessingTask.state == EtatTache.QUEUED,
                )
                .values(state=EtatTache.RUNNING, started_at=datetime.now(UTC))
            )
            await session.commit()
            if resultat.rowcount == 1:
                return
            ligne = await _ligne(session, self.id)
        if ligne is None or ligne.state == EtatTache.CANCELLED:
            raise AnnuleAvantDemarrage(
                f"Traitement {self.id} annulé avant démarrage"
            )
        raise RuntimeError(f"Démarrage refusé depuis l'état {ligne.state}")

    async def lier_adaptateur(self, adaptateur: AdaptateurAnnulation) -> None:
        task_registry.inscrire(self.id, adaptateur)
        # Revue jalon (F2) : le set volatile n'est qu'une optimisation - la
        # VÉRITÉ est l'état durable, relu APRÈS l'inscription. Une demande
        # commitée avant l'enrôlement est toujours transmise, même si le set
        # a été perdu entre-temps.
        rejouer = self.id in _demandes_en_attente
        if not rejouer:
            ligne = await lire(self.id)
            rejouer = ligne is not None and ligne.state == EtatTache.CANCEL_REQUESTED
        if rejouer:
            _demandes_en_attente.discard(self.id)
            await task_registry.demander_annulation(self.id)

    async def progresser(
        self, *, step: str | None = None, progress: float | None = None
    ) -> None:
        async with get_session_context() as session:
            ligne = await _ligne(session, self.id)
            if ligne is None:
                return
            if step is not None:
                ligne.step = step
            if progress is not None:
                ligne.progress = progress
            await session.commit()

    async def annulation_demandee(self) -> bool:
        """Pour les producteurs à drapeau coopératif : consulter l'état."""
        async with get_session_context() as session:
            ligne = await _ligne(session, self.id)
        return ligne is not None and ligne.state == EtatTache.CANCEL_REQUESTED

    async def _ecrire_etat_terminal(self, etat: str, *, error: str | None) -> None:
        async with get_session_context() as session:
            await session.execute(
                update(ProcessingTask)
                .where(
                    ProcessingTask.id == self.id,
                    ProcessingTask.state.not_in(tuple(EtatTache.terminaux())),
                )
                .values(
                    state=etat, error=error, finished_at=datetime.now(UTC)
                )
            )
            await session.commit()
            # Le retrait vit ICI, collé au commit, et c'est la seule place
            # correcte. En asyncio une coroutine ne rend la main qu'à un
            # point d'attente : entre le retour de `commit()` et ces deux
            # lignes, il n'y en a aucun, donc aucune demande d'arrêt ne peut
            # s'intercaler. Le remonter d'un cran (après le `async with`)
            # rouvre la fenêtre - sortir du contexte EST un await, et une
            # demande passée là couperait un producteur déjà terminé, en
            # répondant « arrêté » alors que la base dit `done`.
            task_registry.retirer(self.id)
            _demandes_en_attente.discard(self.id)

    async def terminer(self, etat: str, *, error: str | None = None) -> None:
        """SEUL le producteur pose l'état terminal, après son nettoyage réel.

        L'ÉCRITURE D'ABORD, le retrait ensuite. L'ordre inverse paraissait
        anodin et ne l'est pas : SQLite est mono-écrivain (`busy_timeout`
        5 s), donc le commit peut échouer. Le registre étant déjà vidé, la
        ligne restait `running` avec `can_cancel` faux - une tâche affichée
        comme active que plus personne ne pouvait arrêter, et qu'une demande
        d'annulation figeait en `cancel_requested` pour toujours.

        En écrivant d'abord, un échec laisse la tâche exactement dans l'état
        où elle était : encore annulable. L'exception remonte (le Board la
        traite avec `_terminer_sans_masquer`, qui préserve le message métier
        sans masquer le fait que la ligne n'a pas été fermée).
        """
        assert etat in EtatTache.terminaux(), etat
        await self._ecrire_etat_terminal(etat, error=error)


async def creer_traitement(
    *,
    type: str,
    label: str,
    project_id: str | None = None,
    conversation_id: str | None = None,
    entity_id: str | None = None,
) -> TraitementHandle:
    async with get_session_context() as session:
        ligne = ProcessingTask(
            type=type,
            label=label,
            state=EtatTache.QUEUED,
            project_id=project_id,
            conversation_id=conversation_id,
            entity_id=entity_id,
            run_instance_id=task_registry.instance_courante(),
        )
        session.add(ligne)
        await session.commit()
        await session.refresh(ligne)
        return TraitementHandle(ligne.id)


async def demander_arret(task_id: str) -> ResultatArret | None:
    """La transition d'annulation - jamais l'état terminal d'une running."""
    async with get_session_context() as session:
        ligne = await _ligne(session, task_id)
        if ligne is None:
            return None
        if ligne.state in EtatTache.terminaux():
            return ResultatArret(
                state=ligne.state, resultat="unavailable", transmise=False
            )
        if ligne.state == EtatTache.QUEUED:
            # CAS direct : sans producteur, cancel_requested ne se résoudrait
            # jamais. rowcount 0 = un demarrer() a gagné la course - on
            # retombe alors sur le chemin running.
            resultat_cas = await session.execute(
                update(ProcessingTask)
                .where(
                    ProcessingTask.id == task_id,
                    ProcessingTask.state == EtatTache.QUEUED,
                )
                .values(
                    state=EtatTache.CANCELLED, finished_at=datetime.now(UTC)
                )
            )
            await session.commit()
            if resultat_cas.rowcount == 1:
                return ResultatArret(
                    state=EtatTache.CANCELLED, resultat="stopped", transmise=False
                )
        # running -> cancel_requested, en CAS : un producteur qui vient de
        # terminer done ne doit JAMAIS être régressé (revue jalon, F1).
        resultat_cas = await session.execute(
            update(ProcessingTask)
            .where(
                ProcessingTask.id == task_id,
                ProcessingTask.state == EtatTache.RUNNING,
            )
            .values(state=EtatTache.CANCEL_REQUESTED)
        )
        await session.commit()
        if resultat_cas.rowcount == 0:
            ligne = await _ligne(session, task_id)
            if ligne is not None and ligne.state in EtatTache.terminaux():
                return ResultatArret(
                    state=ligne.state, resultat="unavailable", transmise=False
                )
        # cancel_requested (déjà ou à l'instant) : transmettre.

    if task_registry.est_vivante(task_id):
        coupe = await task_registry.demander_annulation(task_id)
        return ResultatArret(
            state=EtatTache.CANCEL_REQUESTED,
            resultat="stopped" if coupe else "accepted",
            transmise=True,
        )
    # Aucun adaptateur : fenêtre d'enrôlement, traitement non annulable ou
    # nettoyage en cours - on ne conclut RIEN, on retient la demande pour
    # la rejouer si un adaptateur arrive.
    _demandes_en_attente.add(task_id)
    return ResultatArret(
        state=EtatTache.CANCEL_REQUESTED, resultat="unavailable", transmise=False
    )


async def lire(task_id: str) -> ProcessingTask | None:
    async with get_session_context() as session:
        return await _ligne(session, task_id)


async def dto(task_id: str) -> dict[str, Any] | None:
    ligne = await lire(task_id)
    if ligne is None:
        return None
    return _dto(ligne)


def _dto(ligne: ProcessingTask) -> dict[str, Any]:
    return {
        "id": ligne.id,
        "type": ligne.type,
        "label": ligne.label,
        "state": ligne.state,
        "step": ligne.step,
        "progress": ligne.progress,
        "project_id": ligne.project_id,
        "conversation_id": ligne.conversation_id,
        "error": ligne.error,
        "created_at": ligne.created_at.isoformat() if ligne.created_at else None,
        "started_at": ligne.started_at.isoformat() if ligne.started_at else None,
        "finished_at": ligne.finished_at.isoformat() if ligne.finished_at else None,
        # Faux dès la demande posée : un second clic n'a rien à couper.
        # Une queued est TOUJOURS annulable (CAS direct, sans adaptateur).
        "can_cancel": (
            ligne.state == EtatTache.QUEUED
            or (
                ligne.state == EtatTache.RUNNING
                and task_registry.est_vivante(ligne.id)
            )
        ),
    }


async def lister(*, actives: bool | None = None, limit: int = 50) -> list[dict[str, Any]]:
    """La liste servie au panneau - seuil de visibilité appliqué ICI, côté
    serveur, avant `limit` (design V2.1 : chat/deep-research seulement,
    échecs et annulations toujours visibles)."""
    async with get_session_context() as session:
        requete = select(ProcessingTask).order_by(ProcessingTask.created_at.desc())
        if actives is True:
            requete = requete.where(
                ProcessingTask.state.in_(tuple(EtatTache.actifs()))
            )
        elif actives is False:
            requete = requete.where(
                ProcessingTask.state.in_(tuple(EtatTache.terminaux()))
            )
        # Le filtre de visibilité s'applique APRÈS cette lecture : le cap
        # interne doit être largement supérieur à `limit` pour ne pas manger
        # des lignes visibles derrière des masquées (revue jalon). 2000 lignes
        # = très au-delà d'un usage réel avec rétention 30 jours.
        resultat = await session.execute(requete.limit(2000))
        lignes = list(resultat.scalars().all())

    maintenant = datetime.now(UTC)
    visibles: list[dict[str, Any]] = []
    for ligne in lignes:
        if ligne.type in TYPES_A_SEUIL:
            cree = ligne.created_at
            if cree is not None and cree.tzinfo is None:
                cree = cree.replace(tzinfo=UTC)
            if ligne.state in (EtatTache.RUNNING, EtatTache.QUEUED, EtatTache.CANCEL_REQUESTED):
                if cree and (maintenant - cree).total_seconds() < SEUIL_VISIBILITE_S:
                    continue
            elif ligne.state == EtatTache.DONE:
                fini = ligne.finished_at
                if fini is not None and fini.tzinfo is None:
                    fini = fini.replace(tzinfo=UTC)
                if (
                    cree and fini
                    and (fini - cree).total_seconds() < SEUIL_VISIBILITE_S
                ):
                    continue
            # échecs, annulations, interrupted : toujours visibles
        visibles.append(_dto(ligne))
        if len(visibles) >= limit:
            break
    return visibles


async def purger_les_terminees(*, retention_jours: int = 30) -> int:
    """Rétention : les terminées anciennes partent, les actives JAMAIS -
    une active antique finira `interrupted` au récupérateur, pas ici."""
    seuil = datetime.now(UTC) - timedelta(days=retention_jours)
    async with get_session_context() as session:
        resultat = await session.execute(
            select(ProcessingTask).where(
                ProcessingTask.state.in_(tuple(EtatTache.terminaux())),
                ProcessingTask.created_at < seuil,
            )
        )
        anciennes = list(resultat.scalars().all())
        for ligne in anciennes:
            await session.delete(ligne)
        await session.commit()
    if anciennes:
        logger.info("Rétention traitements : %d lignes purgées", len(anciennes))
    return len(anciennes)


async def _ligne(session: Any, task_id: str) -> ProcessingTask | None:
    resultat = await session.execute(
        select(ProcessingTask).where(ProcessingTask.id == task_id)
    )
    return resultat.scalar_one_or_none()
