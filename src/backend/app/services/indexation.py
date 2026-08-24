"""Service d'indexation documentaire - LE producteur unique (0.45).

Extrait de `routers/files.py` (déplacement pur, comportement constant, gelé
par tests/test_caracterisation_indexation.py). Motif du challenge de design
V2 : le verrou par chemin et le sémaphore ne protégeaient que la route
`/api/files/index` - `upload_file` avait son propre pipeline non verrouillé,
le trombone du chat aussi. Tout producteur d'index passe désormais par ici,
et les tests patchent CE module, plus le routeur.
"""
import asyncio
import logging
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.models.database import get_session_context
from app.models.entities import FileMetadata
from app.models.schemas import FileResponse
from app.services.file_parser import chunk_text, extract_text, get_file_metadata
from app.services.path_security import validate_indexable_file
from app.services.qdrant import get_qdrant_service
from fastapi import HTTPException
from sqlmodel import select
from starlette.concurrency import run_in_threadpool

logger = logging.getLogger(__name__)


class ContenuModifieDepuisLePlan(Exception):
    """Le fichier ne correspond plus à l'empreinte attendue : rien n'est écrit.

    Mode sync (0.45) : on n'indexe jamais une version différente de celle
    montrée dans le plan approuvé - l'opération devient `obsolete` et un
    nouveau plan la reprendra."""


class ConflitDePerimetre(Exception):
    """Le chemin appartient, de façon voulue, à un autre périmètre.

    Vérifié AVANT toute écriture (correction 1 du challenge V2.1) : un
    fichier global ou d'un autre projet est un conflit montré, jamais un
    reclassement silencieux."""



# BUG-155 (27/07/2026) : extraction et découpage sont des traitements CPU/disque
# synchrones. Appelés directement depuis une route `async`, ils bloquaient la
# boucle d'événements : pendant l'indexation d'un gros document, plus aucune
# requête n'était servie (chat, emails, agenda) et l'application semblait figée.
# On les déporte dans le pool de threads.


# Un dépôt massif lançait autant d'encodages simultanés que de fichiers
# (revue du 27/07, finding F4). Deux à la fois suffisent sur une machine de
# bureau et laissent de la place au reste de l'application.
MAX_INDEXATIONS_SIMULTANEES = 2
INDEX_SEMAPHORE = asyncio.Semaphore(MAX_INDEXATIONS_SIMULTANEES)

# `FileMetadata.path` est UNIQUE : deux demandes sur le même fichier en même
# temps levaient une contrainte d'intégrité (finding F1).
# Chaque entrée porte son verrou et le nombre de demandes qui s'y rattachent :
# purger sur `locked()` seul supprimerait le verrou alors qu'un appel attend
# encore, et le suivant en créerait un second pour le même chemin.
_verrous_par_chemin: dict[str, list[Any]] = {}


@asynccontextmanager
async def _verrou_de_chemin(chemin: str) -> AsyncIterator[None]:
    entree = _verrous_par_chemin.get(chemin)
    if entree is None:
        entree = [asyncio.Lock(), 0]
        _verrous_par_chemin[chemin] = entree
    entree[1] += 1
    try:
        async with entree[0]:
            yield
    finally:
        entree[1] -= 1
        if entree[1] == 0 and _verrous_par_chemin.get(chemin) is entree:
            _verrous_par_chemin.pop(chemin, None)


async def extract_text_async(file_path: Path) -> str:
    """Extrait le texte d'un fichier sans bloquer la boucle d'événements."""
    return await run_in_threadpool(extract_text, file_path)


async def chunk_text_async(text: str, chunk_size: int = 1000, overlap: int = 200) -> list[str]:
    """Découpe le texte en fragments sans bloquer la boucle d'événements."""
    return await run_in_threadpool(
        lambda: list(chunk_text(text, chunk_size=chunk_size, overlap=overlap))
    )


async def _consigner_resultat(
    file_id: str,
    chunk_count: int,
    indexed_at: datetime,
    figer_perimetre: bool = False,
) -> None:
    """Enregistre l'issue de l'indexation dans une transaction courte.

    `figer_perimetre` n'est honoré qu'ICI, après l'écriture réelle des
    fragments : tant qu'ils n'existent pas, le document reste rectifiable
    plutôt que de figer un cloisonnement que la recherche n'applique pas.
    """
    async with get_session_context() as session:
        a_jour = await session.get(FileMetadata, file_id)
        if a_jour is None:
            # N2 : le fichier a été supprimé pendant le traitement. Ne pas
            # laisser de vecteurs orphelins ni annoncer un succès.
            await get_qdrant_service().async_delete_by_entity(file_id)
            raise HTTPException(
                status_code=409,
                detail="Le fichier a été supprimé pendant son indexation.",
            )
        a_jour.chunk_count = chunk_count
        a_jour.indexed_at = indexed_at
        if figer_perimetre:
            a_jour.scope_provisoire = False
        await session.commit()


def construire_items_indexation(
    *,
    chunks: list[str],
    file_id: str,
    file_name: str,
    chemin: str,
    scope: str,
    scope_id: str | None,
) -> list[dict[str, Any]]:
    """Construit les items Qdrant d'un document. UN SEUL endroit.

    Contre-vérification Soso : `index_payload` écrivait bien le périmètre, mais
    `upload_file` — le chemin réel d'une pièce jointe de projet — construisait
    ses items séparément, avec un `project_id` ad hoc et sans `scope`. Le filtre
    de recherche traitait alors ces documents comme GLOBAUX (branche
    `IsEmptyCondition` prévue pour les documents antérieurs) : un fichier versé
    dans le projet A pouvait ressortir dans une recherche du projet B.

    Deux constructeurs pour un même payload, c'est une divergence garantie.
    """
    return [
        {
            "text": fragment,
            "memory_type": "file",
            "entity_id": file_id,
            "metadata": {
                "name": file_name,
                "path": chemin,
                "chunk_index": i,
                "total_chunks": len(chunks),
                # Sans ces deux clés, le filtre par périmètre ne peut rien
                # retrouver : le champ n'existe pas côté vectoriel.
                "scope": scope,
                "scope_id": scope_id,
                # Conservé pour les lecteurs existants de cette clé.
                **({"project_id": scope_id} if scope == "project" else {}),
            },
        }
        for i, fragment in enumerate(chunks)
    ]


async def index_payload(
    path: str,
    est_abandonnee: Callable[[], Awaitable[bool]] | None = None,
    scope: str = "global",
    scope_id: str | None = None,
    perimetre_provisoire: bool = False,
    sha256_attendu: str | None = None,
) -> FileResponse:
    """Indexe un fichier sans jamais tenir la base ni la boucle d'événements.

    Remédiation de la revue du 27/07/2026 (findings F1, F2 et F4) :

    - La métadonnée est écrite et **committée** avant le travail lourd. Elle
      restait auparavant dans une transaction ouverte pendant l'extraction et
      les embeddings ; SQLite n'ayant qu'un seul écrivain (busy_timeout de 5 s),
      une écriture concurrente - l'enregistrement d'un message de chat, par
      exemple - pouvait échouer pendant l'indexation d'un gros document.
    - Un verrou par chemin sérialise deux demandes portant sur le même fichier
      (`FileMetadata.path` est UNIQUE : la course levait une contrainte).
    - Un sémaphore borne les encodages simultanés : un dépôt massif lançait
      autant d'encodages que de fichiers.
    - `est_abandonnee` permet de renoncer avant l'étape la plus coûteuse quand
      plus personne n'attend la réponse. L'extraction déjà lancée, elle, va à
      son terme : un thread ne s'interrompt pas.

    J2 (31/07/2026) : `scope` et `scope_id` sont écrits DANS LE PAYLOAD, pas
    seulement en base. Le filtrage par périmètre existait des deux côtés mais
    n'était branché ni à l'écriture ni à la lecture — le contexte du chat
    cherchait donc sans aucune cloison, et un document de projet pouvait
    ressortir dans une conversation étrangère.
    """
    # Validation securite du chemin + type de fichier (SEC-002/003)
    try:
        file_path = validate_indexable_file(path)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not file_path.is_file():
        raise HTTPException(status_code=400, detail="Path is not a file")

    async with _verrou_de_chemin(str(file_path)):
        return await _indexer_sous_verrou(
            file_path, est_abandonnee, scope, scope_id, perimetre_provisoire,
            sha256_attendu=sha256_attendu,
        )


async def remplacer_puis_indexer(
    chemin: str,
    deposer: Callable[[], Awaitable[None]],
    *,
    scope: str = "global",
    scope_id: str | None = None,
    perimetre_provisoire: bool = False,
) -> FileResponse:
    """Dépose (ou remplace) le fichier PUIS l'indexe, sous LE MÊME verrou.

    Challenge du design 0.45 : `upload_file` remplaçait le fichier sur disque
    AVANT toute prise de verrou - une indexation concurrente du même chemin
    pouvait lire un contenu à moitié écrit. Le dépôt entre dans la section
    critique, et l'indexation qui suit est le même cœur que la route.
    """
    async with _verrou_de_chemin(chemin):
        await deposer()
        return await _indexer_sous_verrou(
            Path(chemin), None, scope, scope_id, perimetre_provisoire
        )


async def _indexer_sous_verrou(
    file_path: Path,
    est_abandonnee: Callable[[], Awaitable[bool]] | None,
    scope: str,
    scope_id: str | None,
    perimetre_provisoire: bool,
    sha256_attendu: str | None = None,
) -> FileResponse:
    """Le cœur de l'indexation. Le verrou du chemin est DÉJÀ tenu.

    La lecture des métadonnées vit ici, sous le verrou (challenge V2 : lue
    avant l'acquisition, elle pouvait être périmée quand la demande avait
    attendu une indexation précédente du même chemin).
    """
    metadata = get_file_metadata(file_path)

    # Mode sync (0.45) : les ATTENDUS se vérifient sous le verrou, AVANT toute
    # écriture. La copie stable garantit que les octets extraits sont
    # exactement les octets vérifiés - rsync ne connaît pas notre verrou.
    copie_stable: Path | None = None
    if sha256_attendu is not None:
        async with get_session_context() as session:
            result = await session.execute(
                select(FileMetadata).where(FileMetadata.path == str(file_path))
            )
            existant = result.scalar_one_or_none()
        if (
            existant is not None
            and not existant.scope_provisoire
            and (existant.scope, existant.scope_id) != (scope, scope_id)
        ):
            raise ConflitDePerimetre(
                f"{file_path} appartient au périmètre "
                f"{existant.scope}/{existant.scope_id}"
            )
        copie_stable = await run_in_threadpool(
            _copier_si_conforme, file_path, sha256_attendu
        )
        if copie_stable is None:
            raise ContenuModifieDepuisLePlan(
                f"{file_path} ne correspond plus à l'empreinte du plan"
            )

    try:
        return await _indexer_apres_verifications(
            file_path, est_abandonnee, scope, scope_id, perimetre_provisoire,
            metadata, source_extraction=copie_stable or file_path,
        )
    finally:
        if copie_stable is not None:
            copie_stable.unlink(missing_ok=True)


def _copier_si_conforme(source: Path, sha256_attendu: str) -> Path | None:
    """Copie le fichier en hashant AU FIL de la lecture : la copie rendue
    porte exactement les octets vérifiés. None si l'empreinte diverge."""
    import hashlib
    import tempfile

    h = hashlib.sha256()
    descripteur, chemin_copie = tempfile.mkstemp(prefix="therese-sync-")
    copie = Path(chemin_copie)
    try:
        with source.open("rb") as src, open(descripteur, "wb") as dst:
            for bloc in iter(lambda: src.read(1 << 20), b""):
                h.update(bloc)
                dst.write(bloc)
    except OSError:
        copie.unlink(missing_ok=True)
        raise
    if h.hexdigest() != sha256_attendu:
        copie.unlink(missing_ok=True)
        return None
    return copie


async def _indexer_apres_verifications(
    file_path: Path,
    est_abandonnee: Callable[[], Awaitable[bool]] | None,
    scope: str,
    scope_id: str | None,
    perimetre_provisoire: bool,
    metadata: dict,
    source_extraction: Path,
) -> FileResponse:

    # 1. Transaction COURTE : enregistrer le fichier, puis rendre la main.
    async with get_session_context() as session:
        result = await session.execute(
            select(FileMetadata).where(FileMetadata.path == str(file_path))
        )
        existing = result.scalar_one_or_none()
        if existing:
            existing.size = metadata["size"]
            existing.mime_type = metadata["mime_type"]
            existing.updated_at = datetime.now(UTC)
            # Revue Soso, finding critique : la condition précédente
            # laissait un document du projet A devenir propriété du projet B
            # au simple fait d'être joint à une conversation de B, et
            # confisquait un document que l'utilisateur avait délibérément
            # rendu général.
            #
            # Règle : un périmètre VOULU ne se réécrit jamais tout seul.
            # Seul un périmètre provisoire — posé par défaut parce que la
            # conversation n'était pas encore connue — peut être rectifié.
            if existing.scope_provisoire:
                existing.scope = scope
                existing.scope_id = scope_id
                # Revue Soso, passe 2 : NE PAS éteindre le drapeau ici. Ce
                # commit précède l'écriture des fragments ; un abandon
                # entre les deux laissait la base annoncer un périmètre que
                # l'index n'appliquait pas, et le document devenait
                # définitif donc irrattrapable. Le drapeau ne s'éteint
                # qu'une fois les fragments réellement écrits.
                _perimetre_a_figer = not perimetre_provisoire
            else:
                _perimetre_a_figer = False
            file_meta = existing
            reindexation = True
            # Mémorisés pour ne rien détruire si le nouveau traitement
            # n'aboutit pas (N1).
            chunk_count_existant = existing.chunk_count or 0
            indexed_at_existant = existing.indexed_at
        else:
            file_meta = FileMetadata(
                path=str(file_path),
                name=metadata["name"],
                extension=metadata["extension"],
                size=metadata["size"],
                mime_type=metadata["mime_type"],
                scope=scope,
                scope_id=scope_id,
                # Idem à la naissance : provisoire jusqu'à ce que les
                # fragments existent réellement.
                scope_provisoire=True,
            )
            _perimetre_a_figer = not perimetre_provisoire
            session.add(file_meta)
            reindexation = False
            chunk_count_existant = 0
            indexed_at_existant = None
        await session.commit()
        await session.refresh(file_meta)
        file_id = file_meta.id
        file_name = file_meta.name
        created_at = file_meta.created_at
        extension = file_meta.extension
        # Le périmètre EFFECTIF, relu après commit : en réindexation sans
        # périmètre explicite, c'est celui déjà enregistré qui fait foi.
        perimetre = file_meta.scope
        perimetre_id = file_meta.scope_id

    # 2. Travail lourd, hors transaction et hors boucle d'événements.
    #
    # Contre-vérification du 27/07 (N1) : les anciens vecteurs étaient
    # supprimés AVANT l'extraction. Une annulation ou une extraction en
    # échec laissait alors un fichier sans aucun vecteur, présenté comme
    # indexé. La suppression n'a lieu qu'une fois le nouveau contenu prêt
    # et l'écriture décidée : jusque-là, l'index existant reste valide.
    text_content = await extract_text_async(source_extraction)
    chunk_count = chunk_count_existant
    indexed_at = indexed_at_existant
    ecriture_faite = False

    if text_content and not (est_abandonnee and await est_abandonnee()):
        chunks = await chunk_text_async(text_content, chunk_size=1000, overlap=200)
        items = construire_items_indexation(
            chunks=chunks,
            file_id=file_id,
            file_name=file_name,
            chemin=str(file_path),
            scope=perimetre,
            scope_id=perimetre_id,
        )
        if items and not (est_abandonnee and await est_abandonnee()):
            async with INDEX_SEMAPHORE:
                # L'attente du sémaphore peut durer : re-consulter l'abandon
                # juste avant d'écrire (finding F1 resté ouvert).
                if not (est_abandonnee and await est_abandonnee()):
                    if reindexation:
                        await get_qdrant_service().async_delete_by_entity(file_id)
                    try:
                        await get_qdrant_service().async_add_memories(items)
                    except Exception:
                        # Les anciens fragments viennent d'être retirés :
                        # l'index est vide. Le consigner avant de propager,
                        # sinon la base promettrait un contenu introuvable.
                        await _consigner_resultat(file_id, 0, datetime.now(UTC))
                        raise
                    logger.info(f"Indexed {len(chunks)} chunks for file {file_name}")
                    chunk_count = len(chunks)
                    indexed_at = datetime.now(UTC)
                    ecriture_faite = True
    elif not text_content and not (est_abandonnee and await est_abandonnee()):
        # 3e passe de revue : ce chemin détruisait l'index sans consulter
        # l'abandon. Une demande retirée ne doit rien effacer.
        logger.warning(f"No text extracted from {file_path}")
        if reindexation:
            await get_qdrant_service().async_delete_by_entity(file_id)
        chunk_count = 0
        indexed_at = datetime.now(UTC)
        ecriture_faite = True

    # 3. Transaction COURTE : consigner le résultat. Rien à écrire si la
    # demande a été abandonnée : l'état précédent reste la vérité.
    if ecriture_faite:
        await _consigner_resultat(
            file_id, chunk_count, indexed_at, figer_perimetre=_perimetre_a_figer
        )

    return FileResponse(
    id=file_id,
    path=str(file_path),
    name=file_name,
    extension=extension,
    size=metadata["size"],
    mime_type=metadata["mime_type"],
    chunk_count=chunk_count,
    indexed_at=indexed_at,
    created_at=created_at,
    scope=perimetre,
    scope_id=perimetre_id,
    )
