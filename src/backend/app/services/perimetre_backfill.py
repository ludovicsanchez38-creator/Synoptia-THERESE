"""
THÉRÈSE - Reclassement des payloads vectoriels sans périmètre (0.43).

Le périmètre documentaire (`scope` / `scope_id`) n'est écrit dans les payloads
Qdrant que depuis la 0.42. Tout ce qui a été indexé avant en est dépourvu.

Le filtre de recherche accepte ces payloads sans périmètre pour ne pas faire
disparaître d'un coup toute la mémoire existante. Effet de bord relevé en
revue : un document du projet A indexé en 0.41 est alors traité comme GLOBAL,
et remonte dans une conversation du projet B. La cloison ne le couvre pas.

La base, elle, sait : `FileMetadata.scope` / `scope_id` sont renseignés depuis
longtemps. Seul le payload vectoriel l'ignore. On le reclasse donc depuis la
base — sans toucher aux vecteurs, donc sans réencoder quoi que ce soit, et sans
jamais rien supprimer.

Ce qui reste inclassable (un point sans ligne en base) est marqué
`SCOPE_INCLASSABLE` plutôt que promu global : un document dont on ignore le
rattachement ne doit pas devenir visible dans tous les projets. Il reste
consultable dans les recherches non cloisonnées, et récupérable — rien n'est
détruit.
"""
import logging

from app.models.entities import FileMetadata
from app.services.qdrant import get_qdrant_service
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

logger = logging.getLogger(__name__)

#: Périmètre des points dont le rattachement ne peut pas être déterminé.
#: Volontairement distinct de `global` : il exclut des recherches cloisonnées
#: sans prétendre que le document appartient à tout le monde.
SCOPE_INCLASSABLE = "legacy_unclassified"


async def reclasser_payloads_sans_perimetre(session: AsyncSession) -> int:
    """Écrit le périmètre manquant dans les payloads vectoriels.

    Retourne le nombre de points reclassés. Idempotent : les points déjà
    classés ne sont pas relus.
    """
    qdrant = get_qdrant_service()
    try:
        orphelins = qdrant.points_sans_perimetre()
    except Exception as e:
        # Un ménage de démarrage ne doit jamais empêcher l'application de se
        # lancer : au pire les anciens points restent traités comme globaux,
        # c'est-à-dire l'état d'avant ce correctif.
        logger.warning("Reclassement du périmètre ignoré : %s", e)
        return 0

    if not orphelins:
        return 0

    # Regrouper par document : un fichier a plusieurs fragments, une seule
    # écriture de payload suffit pour tous.
    par_entite: dict[str, list[str]] = {}
    for point_id, payload in orphelins:
        entity_id = payload.get("entity_id")
        if entity_id:
            par_entite.setdefault(str(entity_id), []).append(point_id)

    if not par_entite:
        return 0

    resultat = await session.execute(
        select(FileMetadata).where(FileMetadata.id.in_(tuple(par_entite)))
    )
    connus = {ligne.id: ligne for ligne in resultat.scalars().all()}

    reclasses = 0
    for entity_id, point_ids in par_entite.items():
        ligne = connus.get(entity_id)
        if ligne is None:
            scope, scope_id = SCOPE_INCLASSABLE, None
        else:
            scope, scope_id = (ligne.scope or "global"), ligne.scope_id
        try:
            qdrant.definir_perimetre(point_ids, scope, scope_id)
            reclasses += len(point_ids)
        except Exception as e:
            logger.warning("Reclassement impossible pour %s : %s", entity_id, e)

    if reclasses:
        logger.info("Périmètre reclassé sur %d fragments documentaires", reclasses)
    return reclasses
