"""Service de retrait d'index - idempotent et fail-closed (0.45).

Challenge du design V2 (bloquant 3) : `delete_file` avalait toute erreur
Qdrant puis supprimait quand même la ligne SQLite - des vecteurs orphelins
restaient servis par la recherche, sans plus aucune métadonnée pour les
retrouver. Et `delete_by_entity` plafonnait à 1000 points (corrigé par la
suppression par filtre serveur).

Le contrat, dans l'ordre :
1. verrou du chemin (le même que l'indexation - une suppression ne
   s'intercale jamais dans une indexation du même fichier) ;
2. si un `file_id_attendu` est fourni et que le chemin désigne une AUTRE
   entité, c'est un conflit : rien n'est supprimé (entre un plan et son
   apply, un fichier supprimé puis réindexé est une nouvelle entité) ;
3. Qdrant d'abord, EN ENTIER ; une erreur interrompt tout, la ligne SQLite
   reste - l'état demeure réparable par une reprise ;
4. la base ensuite ; une entité déjà absente est un SUCCÈS de reprise, et
   ses vecteurs éventuels (crash entre les deux suppressions) sont nettoyés
   quand même.
"""
import logging
from dataclasses import dataclass

from app.models.database import get_session_context
from app.models.entities import FileMetadata
from app.services import indexation
from app.services.indexation import _verrou_de_chemin
from sqlmodel import select

logger = logging.getLogger(__name__)


@dataclass
class RetraitResultat:
    retire: bool
    deja_absent: bool = False
    conflit: bool = False
    file_id: str | None = None


async def retirer_de_lindex(*, file_id_attendu: str) -> RetraitResultat:
    """Retire une entité désignée par son id. Idempotent."""
    async with get_session_context() as session:
        result = await session.execute(
            select(FileMetadata).where(FileMetadata.id == file_id_attendu)
        )
        meta = result.scalar_one_or_none()

    if meta is None:
        # Succès de reprise : plus de métadonnée, mais un crash entre les deux
        # suppressions a pu laisser des vecteurs - on nettoie quand même.
        await indexation.get_qdrant_service().async_delete_by_entity(file_id_attendu)
        return RetraitResultat(retire=True, deja_absent=True, file_id=file_id_attendu)

    return await _retirer_sous_verrou(meta.path, file_id_attendu)


async def retirer_par_chemin(
    chemin: str, *, file_id_attendu: str | None = None
) -> RetraitResultat:
    """Retire l'entité d'un chemin, en vérifiant son identité si fournie."""
    return await _retirer_sous_verrou(chemin, file_id_attendu)


async def _retirer_sous_verrou(
    chemin: str, file_id_attendu: str | None
) -> RetraitResultat:
    async with _verrou_de_chemin(chemin):
        async with get_session_context() as session:
            result = await session.execute(
                select(FileMetadata).where(FileMetadata.path == chemin)
            )
            meta = result.scalar_one_or_none()

        if meta is None:
            if file_id_attendu:
                await indexation.get_qdrant_service().async_delete_by_entity(file_id_attendu)
            return RetraitResultat(
                retire=True, deja_absent=True, file_id=file_id_attendu
            )

        if file_id_attendu is not None and meta.id != file_id_attendu:
            logger.warning(
                "Retrait refusé pour %s : l'entité attendue %s a été remplacée "
                "par %s - le chemin a changé d'identité depuis le plan",
                chemin, file_id_attendu, meta.id,
            )
            return RetraitResultat(retire=False, conflit=True, file_id=meta.id)

        # Qdrant d'abord, en entier. Une erreur propage : la ligne reste.
        supprimes = await indexation.get_qdrant_service().async_delete_by_entity(meta.id)
        logger.info("Retrait index : %s vecteurs pour %s", supprimes, meta.id)

        async with get_session_context() as session:
            result = await session.execute(
                select(FileMetadata).where(FileMetadata.id == meta.id)
            )
            ligne = result.scalar_one_or_none()
            if ligne is not None:
                await session.delete(ligne)
            # Revue jalon (B5) : un retrait manuel doit aussi retirer l'entrée
            # de référence sync - sinon le plan suivant annonce « inchangé »
            # un fichier qui n'est plus indexé.
            from app.models.entities_sync import ProjectSyncEntry

            result = await session.execute(
                select(ProjectSyncEntry).where(ProjectSyncEntry.chemin == chemin)
            )
            for entree in result.scalars():
                await session.delete(entree)
            await session.commit()

        return RetraitResultat(retire=True, file_id=meta.id)
