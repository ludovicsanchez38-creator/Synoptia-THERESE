"""
THERESE v2 - Chat Router

Endpoints for chat and conversation management.
"""

import asyncio
import contextlib
import json
import logging
import re
import time
from pathlib import Path
from typing import Any, AsyncGenerator

from app.models.database import get_session
from app.models.entities import Contact, Conversation, FileMetadata, Message, Project
from app.models.processing import EtatTache as EtatTacheTraitement
from app.models.schemas import (
    ChatRequest,
    ChatResponse,
    ConversationCreate,
    ConversationProjectUpdate,
    ConversationResponse,
    MessageResponse,
    StreamChunk,
)
from app.services.chat_actions import (
    ParsedChatAction,
    available_actions_text,
    parse_action_message,
)
from app.services.cloisonnement import souvenirs_globaux_visibles
from app.services.contexte_execution import ContexteExecution
from app.services.entity_extractor import (
    get_entity_extractor,
)
from app.services.error_handler import message_pour_ecran
from app.services.file_parser import extract_text
from app.services.indexation import IndexationAbandonnee
from app.services.llm import (
    ContextWindow,
    LLMService,
    ToolCall,
    ToolResult,
    ToolTurn,
    convert_markdown_tables_to_bullets,
    get_llm_service,
)
from app.services.llm import (
    Message as LLMMessage,
)
from app.services.mcp_service import get_mcp_service
from app.services.memory_tools import MEMORY_TOOL_NAMES, MEMORY_TOOLS, execute_memory_tool
from app.services.path_security import validate_file_path
from app.services.performance import get_performance_monitor, get_search_index
from app.services.qdrant import get_qdrant_service
from app.services.skills.base import SkillExecuteRequest
from app.services.slash_commands import (
    execute_slash_command_outcome,
    parse_inline_commands,
    parse_slash_command,
)
from app.services.token_tracker import detect_uncertainty, get_token_tracker
from app.services.tool_confirmations import (
    _base_tool_name,
    canoniser_arguments,
    empreinte_action,
    pop_pending,
    register_pending,
    requires_confirmation,
)
from app.services.web_search import (
    execute_browser_action,
    execute_web_search,
    web_tools,
)
from app.services.workspace_tools import (
    WORKSPACE_TOOL_NAMES,
    WORKSPACE_TOOLS,
    execute_workspace_tool,
)
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from starlette.concurrency import run_in_threadpool

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================
# Generation Cancellation (US-ERR-04)
# ============================================================

# 0.47 (fencing) : le token par GÉNÉRATION est l'autorité. La table par
# conversation ne sert plus qu'à la compat lecture (façade /cancel, drapeau
# historique) : elle pointe vers le contexte de la génération COURANTE.
_active_generations: dict[str, ContexteExecution] = {}
# Timestamps pour detecter les entrees orphelines (client deconnecte)
_generation_timestamps: dict[str, float] = {}
# Duree max avant nettoyage automatique (5 minutes)
_GENERATION_TIMEOUT_S = 300


def _register_generation(
    conversation_id: str, generation_id: str | None = None
) -> ContexteExecution:
    """Crée le contexte de CETTE génération et en fait la courante."""
    contexte = ContexteExecution(generation_id=generation_id)
    _active_generations[conversation_id] = contexte
    _generation_timestamps[conversation_id] = time.monotonic()
    # Nettoyage opportuniste des entrees orphelines
    _cleanup_stale_generations()
    return contexte


def _cancel_generation(conversation_id: str) -> bool:
    """Pose le token de la génération COURANTE de la conversation."""
    contexte = _active_generations.get(conversation_id)
    if contexte is not None:
        contexte.demander_arret()
        return True
    return False


def _is_cancelled(conversation_id: str) -> bool:
    """Compat lecture : le drapeau par conversation lit le token courant."""
    contexte = _active_generations.get(conversation_id)
    return contexte is not None and contexte.annulation_observee()


def _unregister_generation(
    conversation_id: str,
    generation_id: str | None = None,
    contexte: ContexteExecution | None = None,
) -> None:
    """Remove a generation from tracking - seulement si on la possède encore.

    Revue jalon (F2) : l'identité par OBJET fait foi. Le guard par
    generation_id laissait une fenêtre - une génération neuve dont l'id
    n'est pas encore affecté (creer_traitement en cours) se faisait
    retirer par la fin de la précédente, et la façade /cancel ne trouvait
    plus rien à arrêter.
    """
    courante = _active_generations.get(conversation_id)
    if contexte is not None:
        if courante is not contexte:
            return
    elif (
        generation_id is not None
        and courante is not None
        and courante.generation_id != generation_id
    ):
        # Une génération plus récente a repris l'entrée : ne pas la casser.
        return
    _active_generations.pop(conversation_id, None)
    _generation_timestamps.pop(conversation_id, None)


def _cleanup_stale_generations() -> None:
    """
    Supprime les entrees plus vieilles que _GENERATION_TIMEOUT_S.

    Appele de maniere opportuniste a chaque nouvelle generation
    pour eviter les fuites memoire si un client se deconnecte
    sans que le stream ne se termine proprement.
    """
    now = time.monotonic()
    stale_ids = [
        cid for cid, ts in _generation_timestamps.items()
        if now - ts > _GENERATION_TIMEOUT_S
    ]
    for cid in stale_ids:
        logger.warning(f"Cleanup generation orpheline: {cid} (age > {_GENERATION_TIMEOUT_S}s)")
        _active_generations.pop(cid, None)
        _generation_timestamps.pop(cid, None)


# ============================================================
# Slash Command Patterns
# ============================================================

# Pattern for /fichier [path] or /analyse [path]
FILE_COMMAND_PATTERN = re.compile(
    r'^/(fichier|analyse)\s+(.+)$',
    re.IGNORECASE | re.MULTILINE
)


def _parse_file_commands(message: str) -> list[tuple[str, str]]:
    """
    Parse /fichier and /analyse commands from message.

    Returns list of (command, path) tuples.
    """
    commands = []
    for match in FILE_COMMAND_PATTERN.finditer(message):
        command = match.group(1).lower()
        path = match.group(2).strip()
        # Remove quotes if present
        if (path.startswith('"') and path.endswith('"')) or \
           (path.startswith("'") and path.endswith("'")):
            path = path[1:-1]
        commands.append((command, path))
    return commands


# Passe 2 de revue (P2-6) : rattrapages de périmètre en vol (détachés).
_rattrapages_en_cours: set["asyncio.Task[None]"] = set()


async def _rattraper_perimetre(
    file_id: str, chemin: str, scope: str, scope_id: str | None
) -> None:
    """Rattrape le périmètre d'un document déjà indexé (BUG-165) - geste
    complet et insensible à l'annulation du chat qui l'a déclenché.

    Passe 3 de revue (P3-2) : SOUS le verrou de chemin, avec REVALIDATION -
    deux conversations pouvaient lire « provisoire » toutes les deux et
    rattraper vers deux projets différents (SQLite disait A, Qdrant servait
    B). Le premier gagne, le second constate et ne touche à rien.

    L'INDEX D'ABORD, la base ensuite. L'ordre inverse annonçait un
    périmètre que la recherche n'appliquait pas encore : en cas d'échec,
    la base affirme le statu quo (document visible dans le périmètre
    général), jamais une fuite nouvelle.
    """
    from app.models.database import get_session_context as _ctx
    from app.services.indexation import _verrou_de_chemin

    nom = Path(chemin).name
    async with _verrou_de_chemin(chemin):
        async with _ctx() as session:
            ligne = (await session.execute(
                select(FileMetadata).where(FileMetadata.id == file_id)
            )).scalar_one_or_none()
            if ligne is None or not ligne.scope_provisoire:
                # Déjà rattrapé (ou disparu) : ne rien réécrire.
                return
        try:
            await run_in_threadpool(
                get_qdrant_service().definir_perimetre_entite,
                file_id, scope, scope_id,
            )
        except Exception:
            logger.warning(
                "Périmètre non appliqué à l'index pour %s : le document "
                "reste dans son périmètre actuel plutôt que d'être annoncé "
                "cloisonné sans l'être", nom, exc_info=True,
            )
            return
        try:
            async with _ctx() as session:
                ligne = (await session.execute(
                    select(FileMetadata).where(FileMetadata.id == file_id)
                )).scalar_one_or_none()
                if ligne is None:
                    return
                ligne.scope = scope
                ligne.scope_id = scope_id
                ligne.scope_provisoire = False
                await session.commit()
        except Exception:
            logger.warning(
                "Périmètre appliqué à l'index mais pas consigné en base "
                "pour %s", nom, exc_info=True,
            )


async def _get_file_context(
    file_path: str,
    session: AsyncSession,
    command: str = "fichier",
    scope: str = "global",
    scope_id: str | None = None,
    contexte: ContexteExecution | None = None,
) -> tuple[str | None, str | None]:
    """
    Get file content for context injection.

    Args:
        file_path: Path to the file
        session: Database session
        command: Command type ('fichier' or 'analyse')

    Returns:
        Tuple of (context_string, error_message)
    """
    # Validation securite du chemin (SEC-002)
    try:
        path = validate_file_path(file_path)
    except PermissionError as e:
        return None, str(e)
    except FileNotFoundError as e:
        return None, str(e)

    if not path.is_file():
        return None, f"Ce n'est pas un fichier: {file_path}"

    try:
        # Extract text content, hors boucle d'événements : joindre un gros
        # document au chat gelait l'application au même titre que l'indexation
        # depuis le composeur (BUG-155, troisième chemin trouvé en revue).
        text_content = await run_in_threadpool(extract_text, path)

        if not text_content:
            return None, f"Impossible d'extraire le contenu de: {path.name}"

        # Check if file is already indexed
        result = await session.execute(
            select(FileMetadata).where(FileMetadata.path == str(path))
        )
        existing = result.scalar_one_or_none()

        # BUG-165 : rattrapage du périmètre d'un fichier DÉJÀ indexé.
        #
        # Le composeur indexe la pièce jointe dès l'attachement, donc `existing`
        # est presque toujours trouvé ici et tout le bloc `if not existing:`
        # ci-dessous — celui qui pose le périmètre — restait du code mort. Une
        # pièce jointe déposée dans la conversation d'un client demeurait ainsi
        # globale, lisible depuis tous les autres dossiers.
        #
        # Le rattrapage ne remonte JAMAIS un fichier : il ne touche qu'un
        # document encore global, et seulement quand la conversation porte un
        # périmètre. Un document indexé volontairement pour tous les dossiers
        # depuis l'explorateur garde donc sa portée, et un document déjà
        # rattaché à un projet ne peut pas être capté par un autre.
        # Revue Soso : le rattrapage ne touche QUE les périmètres provisoires,
        # ceux posés par défaut lors du pré-index parce que la conversation
        # n'existait pas encore. Un document rendu général depuis l'explorateur,
        # ou déjà rattaché à un projet, n'est jamais capté ni confisqué.
        if (
            existing and scope and scope != "global"
            and existing.scope_provisoire
            # Revue jalon (F7) : le rattrapage mute Qdrant + SQLite - c'est
            # un effet métier local, il respecte la promesse du fencing.
            and not (contexte is not None and contexte.annulation_observee())
        ):
            # Passe 2 de revue (P2-6) : le geste part en tâche DÉTACHÉE avec
            # sa propre session - une annulation en vol (pendant le thread
            # Qdrant) coupait la coroutine entre les deux écritures et
            # laissait les vecteurs re-périmétrés avec une base restée
            # globale. Détaché, le geste finit les DEUX côtés ou aucun.
            rattrapage = asyncio.create_task(
                _rattraper_perimetre(existing.id, str(path), scope, scope_id)
            )
            _rattrapages_en_cours.add(rattrapage)
            rattrapage.add_done_callback(_rattrapages_en_cours.discard)
            await asyncio.shield(rattrapage)
            await session.refresh(existing)

        # Index if not already done
        if not existing:
            # 0.47 : le chemin de secours passe par le MÊME cœur que la
            # route et l'upload (verrou de chemin, invariant N1, périmètre
            # dans le payload) et par le MÊME signal - le token de SA
            # génération. Le corps historique dupliquait le cœur avec son
            # propre découpage : deux constructeurs pour un même index,
            # c'était une divergence garantie.
            from app.services import indexation

            async def _abandonnee() -> bool:
                return (
                    contexte is not None and contexte.annulation_observee()
                )

            await indexation.index_payload(
                str(path),
                est_abandonnee=_abandonnee,
                scope=scope,
                scope_id=scope_id,
            )

        # Build context string
        file_name = path.name
        file_size = path.stat().st_size
        size_str = (
            f"{file_size} B" if file_size < 1024
            else f"{file_size / 1024:.1f} KB" if file_size < 1024 * 1024
            else f"{file_size / (1024 * 1024):.1f} MB"
        )

        # Truncate content if too long
        max_chars = 15000
        if len(text_content) > max_chars:
            text_content = text_content[:max_chars] + f"\n\n[... contenu tronque, {len(text_content)} caracteres au total ...]"

        context = f"""--- FICHIER: {file_name} ({size_str}) ---
Chemin: {path}

{text_content}

--- FIN DU FICHIER ---"""

        return context, None

    except IndexationAbandonnee:
        # 0.47 : l'utilisateur a retiré sa demande - la déguiser en
        # « Erreur lors de la lecture » mentait deux fois (au journal et
        # à l'utilisateur). L'appelant sait quoi faire d'un abandon.
        raise
    except Exception as e:
        logger.error(f"Error processing file {file_path}: {e}")
        return None, f"Erreur lors de la lecture de {path.name}: {str(e)}"


# ============================================================
# Memory Context Helper
# ============================================================


# Périmètre sentinelle : ne correspond à AUCUN document. Sert quand le
# rattachement d'une conversation est illisible — mieux vaut répondre sans
# contexte documentaire qu'avec le contexte d'un autre client (échec fermé).
_PERIMETRE_INDETERMINE = "__perimetre_indetermine__"


# ============================================================
# BUG-160 : une pièce jointe appartient à la conversation
# ============================================================
#
# Le contenu d'un fichier joint entre dans le prompt système, qui est
# reconstruit à chaque requête et jamais conservé. Le composeur vide ensuite sa
# liste, et le message enregistré ne mentionne aucun fichier : dès le tour
# suivant, THÉRÈSE n'a plus rien, et répond très correctement qu'elle ne
# dispose d'aucun outil pour lire le document. L'interface, elle, affiche
# « [Fichiers joints: ...] » sous le message, donc l'utilisateur croit le
# contraire.
#
# On rejoue donc les pièces jointes des derniers tours. Deux bornes, parce que
# ce contenu repart chez le fournisseur à CHAQUE message : un nombre de tours
# limité, et un plafond de caractères. `trim_to_fit` ne rogne que les messages
# et jamais le prompt système — un bloc de fichiers qui enfle sacrifierait donc
# l'historique de la conversation en silence.
TOURS_AVEC_PIECES_JOINTES = 3
PLAFOND_PIECES_JOINTES_REJOUEES = 4

# Revue Soso : un plafond en NOMBRE de fichiers ne borne rien. Chaque pièce
# jointe peut peser 15 000 caractères, donc quatre fichiers rejoués plus ceux du
# tour courant dépassaient largement la fenêtre utile — et cette fenêtre est
# parfois bien plus étroite qu'annoncé : le service raisonne sur 32 000 tokens
# quand Ollama en applique 8 192.
#
# Ce plafond porte sur le bloc ENTIER (fichiers du tour + fichiers rejoués). Une
# fois atteint, on cesse d'ajouter : mieux vaut un document de moins qu'un
# historique de conversation sacrifié en silence par `trim_to_fit`, qui ne rogne
# que les messages et jamais le prompt système.
PLAFOND_CARACTERES_FICHIERS = 40000

BLOC_PIECES_JOINTES = """
## Les fichiers joints à cette conversation
Les pièces jointes te sont fournies plus haut, dans le contexte, sous forme de
blocs délimités par `--- FICHIER: nom ---`. Elles restent disponibles pendant
toute la conversation, tu n'as aucun outil à appeler pour les consulter.
N'affirme JAMAIS que tu n'as pas accès à un fichier qui figure dans ce contexte.
Si un bloc porte la mention « contenu tronqué » ou « extrait », tu n'en as reçu
qu'une partie : dis-le clairement à l'utilisateur au lieu de présenter ta
lecture comme complète, et indique-lui que le document dépasse ce que tu peux
recevoir d'un coup."""


def _memoriser_pieces_jointes(message: Message, chemins: list[str] | None) -> None:
    """Consigne les pièces jointes d'un tour sur le message qui les portait."""
    if not chemins:
        return
    from pathlib import Path as _Path

    donnees = json.loads(message.extra_data) if message.extra_data else {}
    donnees["attachments"] = [
        {"path": chemin, "name": _Path(chemin).name} for chemin in chemins
    ]
    message.extra_data = json.dumps(donnees)


def _marquer_deterministe(message: Message) -> None:
    """Marque un message comme déterministe SANS effacer ses autres données.

    Revue Soso, passe 3 : `extra_data` était intégralement remplacé par
    `{"deterministic": true}`. Les pièces jointes qu'on venait d'y consigner
    disparaissaient donc, et comme le composeur avait déjà vidé sa liste, le
    document restait global sans qu'aucun tour suivant ne puisse le retrouver
    ni rectifier son périmètre. Une réattache manuelle était le seul recours.
    """
    donnees = {}
    if message.extra_data:
        try:
            donnees = json.loads(message.extra_data)
        except (ValueError, TypeError):
            donnees = {}
    donnees["deterministic"] = True
    message.extra_data = json.dumps(donnees)


async def _pieces_jointes_recentes(
    conversation_id: str | None,
    session: AsyncSession | None,
    deja_fournis: list[str],
) -> list[str]:
    """Les pièces jointes des derniers tours, à rejouer dans le contexte.

    Un fichier absent du disque est ignoré sans bruit : il vit hors de THÉRÈSE
    et peut avoir été déplacé ou supprimé entre deux messages.
    """
    if not conversation_id or session is None:
        return []

    from pathlib import Path as _Path

    try:
        resultat = await session.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .where(Message.role == "user")
            # Clé secondaire indispensable : deux messages enregistrés dans la
            # même seconde se réordonneraient au hasard en SQLite, et la
            # sélection des pièces jointes à rejouer varierait d'un appel à
            # l'autre (garde `test_order_by_not_single_key`).
            .order_by(Message.created_at.desc(), Message.id.desc())
            .limit(TOURS_AVEC_PIECES_JOINTES)
        )
        messages = list(resultat.scalars().all())
    except Exception:
        logger.warning("Pièces jointes des tours précédents illisibles", exc_info=True)
        return []

    connus = set(deja_fournis)
    rejoues: list[str] = []
    for message in messages:
        if not message.extra_data:
            continue
        try:
            donnees = json.loads(message.extra_data)
        except (ValueError, TypeError):
            continue
        for piece in donnees.get("attachments", []) or []:
            chemin = piece.get("path")
            if not chemin or chemin in connus:
                continue
            if not _Path(chemin).is_file():
                logger.info(
                    "Pièce jointe %s introuvable sur le disque, non rejouée", chemin
                )
                connus.add(chemin)
                continue
            connus.add(chemin)
            rejoues.append(chemin)
            if len(rejoues) >= PLAFOND_PIECES_JOINTES_REJOUEES:
                return rejoues
    return rejoues


def borner_bloc_fichiers(contextes: list[str]) -> tuple[list[str], int]:
    """Coupe le bloc des fichiers au plafond global, sans jamais couper un bloc.

    Renvoie les contextes retenus et le nombre de documents écartés, pour que
    l'utilisateur puisse être averti plutôt que de croire que tout a été lu.
    Le premier document est toujours retenu, même s'il dépasse à lui seul : le
    couper en deux ferait plus de dégâts que de l'admettre entier.
    """
    retenus: list[str] = []
    total = 0
    ecartes = 0
    for contexte in contextes:
        if retenus and total + len(contexte) > PLAFOND_CARACTERES_FICHIERS:
            # Revue Soso, passe 2 : `continue` et non `break`. Un premier gros
            # document ne doit pas faire tomber tous les suivants : un document
            # court qui tient encore garde toutes ses chances, et l'ordre
            # d'arrivée — tour courant d'abord — reste respecté.
            ecartes += 1
            continue
        retenus.append(contexte)
        total += len(contexte)
    return retenus, ecartes


async def _perimetre_de_conversation(
    conversation_id: str | None, session: AsyncSession | None
) -> tuple[str | None, str | None]:
    """Le périmètre documentaire d'une conversation : (scope, scope_id).

    `(None, None)` = aucune cloison, la mémoire entière est consultable. C'est
    le cas d'une conversation libre, et celui de tous les appels qui ne
    connaissent pas leur conversation.
    """
    if not conversation_id or session is None:
        return None, None
    try:
        conversation = await session.get(Conversation, conversation_id)
    except Exception:
        # ÉCHEC FERMÉ (revue 0.43). La version précédente retombait sur une
        # recherche globale : une simple erreur SQLite transitoire transformait
        # alors une conversation cloisonnée en conversation ouverte, sans que
        # rien ne le signale. Une frontière de confidentialité qui s'élargit en
        # silence sur incident n'en est pas une.
        #
        # `_PERIMETRE_INDETERMINE` ne correspond à aucun document : la
        # conversation répond sans contexte documentaire plutôt qu'avec le
        # contexte d'un autre client.
        logger.warning(
            "Périmètre de conversation illisible : aucun contexte documentaire "
            "ne sera injecté (échec fermé)"
        )
        return "project", _PERIMETRE_INDETERMINE
    if conversation is None:
        return None, None

    politique = (conversation.memory_scope or "global").lower()
    # ORDRE VOLONTAIRE (revue) : le rattachement est testé AVANT la politique.
    # Une ligne incohérente — `project_id` posé et `memory_scope='all'` — aurait
    # sinon ouvert toute la mémoire, contrairement à ce que le sélecteur affiche.
    # Aucune contrainte de base ne garantit l'invariant : c'est le résolveur qui
    # le tient, et il tranche toujours dans le sens le plus fermé.
    if conversation.project_id:
        # La politique est DÉRIVÉE du rattachement : poser un projet suffit à
        # cloisonner. Exiger en plus que `memory_scope` soit passé à `project`
        # créerait deux champs à synchroniser, et un rattachement sans effet
        # visible au premier oubli.
        return "project", conversation.project_id
    if politique == "all":
        # « Tous les projets », choix explicite et affiché. Il ouvre les
        # DOSSIERS, pas les souvenirs privés des autres conversations : rendre
        # `(None, None)` retirait toute cloison et laissait remonter les
        # contacts enregistrés dans n'importe quelle conversation (revue de
        # clôture). Le libellé engage — il doit dire vrai.
        return "all", None
    # MOINDRE PRIVILÈGE (défaut) : documents généraux uniquement. Une
    # conversation qui n'a rien demandé ne pioche pas dans les dossiers clients.
    # `include_global` du filtre rend déjà les documents globaux ; passer
    # `scope="global"` suffit à exclure ceux qui portent un projet.
    return "global", None


async def perimetre_de_piece_jointe(
    conversation_id: str | None, session: AsyncSession | None
) -> tuple[str, str | None, bool]:
    """Le périmètre d'un DOCUMENT joint, distinct de celui d'une RECHERCHE.

    Revue Soso : `_perimetre_de_conversation` sert à chercher, et peut rendre
    `all` — un périmètre de lecture transversal. L'écrire sur un document le
    rendait introuvable : le filtre `all` relit `global`, `project` et la
    conversation courante, jamais `all` lui-même. Un fichier ainsi classé
    disparaissait donc de partout une fois la fenêtre de rejeu passée.

    Un document n'a que deux appartenances possibles : le projet de la
    conversation, ou la conversation elle-même. Jamais « tous les projets »,
    qui décrit ce qu'on a le droit de lire, pas ce qu'on possède.

    Le troisième élément dit si la conversation EXISTE réellement en base. Un
    identifiant encore local — le composeur en fabrique un avant que le backend
    n'ait créé la conversation — donnerait sinon un périmètre définitif
    rattaché à une conversation qui n'existera jamais sous cet identifiant : le
    document y resterait prisonnier, sans que rien ne puisse le rectifier.
    """
    conversation = None
    if conversation_id and session is not None:
        try:
            conversation = await session.get(Conversation, conversation_id)
        except Exception:
            logger.warning("Conversation illisible pour le périmètre documentaire")

    scope, scope_id = await _perimetre_de_conversation(conversation_id, session)
    if scope == "project" and scope_id:
        return "project", scope_id, conversation is not None
    if conversation_id:
        return "conversation", conversation_id, conversation is not None
    return "global", None, False


async def _get_memory_context(
    user_message: str,
    limit: int = 8,
    conversation_id: str | None = None,
    session: AsyncSession | None = None,
) -> str | None:
    """
    Search memory for context relevant to the user's message.

    0.43 : la recherche est CLOISONNÉE quand la conversation est rattachée à un
    projet. Jusque-là elle balayait toute la mémoire, si bien qu'un document du
    projet A pouvait être injecté dans une conversation parlant du projet B —
    sans trace à l'écran, ni pour l'utilisateur ni pour le modèle.

    Returns formatted context string or None if no relevant memories found.
    """
    context_parts: list[str] = []
    # Affecté avant le try : il est relu plus bas, hors de sa portée. Un
    # périmètre illisible ne doit pas faire tomber tout le message pour une
    # mention accessoire (relevé par la relecture adversariale).
    scope: str | None = None
    try:
        scope, scope_id = await _perimetre_de_conversation(conversation_id, session)
        qdrant = get_qdrant_service()
        results = await qdrant.async_search(
            query=user_message,
            limit=limit,
            score_threshold=0.35,  # Lower threshold for broader context
            scope=scope,
            scope_id=scope_id,
            # C3 : en mode cabinet, une conversation rattachée à un dossier ne
            # reçoit plus les souvenirs généraux. Le défaut (`True`) est
            # inchangé hors de ce mode. La MÊME politique est lue par
            # `_cloison_contacts` — fermer ici seulement laisserait l'outil
            # `read_contact` recracher la fiche par son nom.
            include_global=souvenirs_globaux_visibles(scope),
            # Les souvenirs rattachés à CETTE conversation y restent
            # consultables, comme côté SQL.
            conversation_id=conversation_id,
        )

        # Format results into context string
        seen_files = set()  # Track seen files to avoid duplicates

        for hit in results:
            memory_type = hit.get("type", "")
            text = hit.get("text", "")
            metadata = hit.get("metadata", {})
            score = hit.get("score", 0)

            if memory_type == "contact":
                name = metadata.get("name", "Inconnu")
                context_parts.append(f"**Contact**: {name}\n{text}")
            elif memory_type == "project":
                name = metadata.get("name", "Sans nom")
                status = metadata.get("status", "")
                context_parts.append(f"**Projet** ({status}): {name}\n{text}")
            elif memory_type == "file":
                file_name = metadata.get("name", "fichier")
                chunk_index = metadata.get("chunk_index", 0)
                total_chunks = metadata.get("total_chunks", 1)

                # Only include first occurrence per file to avoid too much context
                if file_name not in seen_files:
                    seen_files.add(file_name)
                    if total_chunks > 1:
                        context_parts.append(
                            f"**Fichier**: {file_name} (extrait {chunk_index + 1}/{total_chunks})\n{text}"
                        )
                    else:
                        context_parts.append(f"**Fichier**: {file_name}\n{text}")
            else:
                context_parts.append(text)

            logger.debug(f"Memory context hit: {memory_type} (score={score:.2f})")

    except Exception as e:
        logger.warning(f"Failed to get memory context: {e}")

    # RAG juridique : injecter les références légales VÉRIFIÉES (corpus Légifrance)
    # si le message touche un sujet juridique, pour ancrer le modèle au lieu de sa
    # mémoire périmée (cf. 2e passage personas : L441-6 cité au lieu de L441-10).
    try:
        from app.services.legal_corpus import get_legal_context

        legal = get_legal_context(user_message)
        if legal:
            context_parts.append(legal)
    except Exception as e:
        logger.debug(f"Contexte juridique ignoré : {e}")

    # D6 : dire la cloison au lieu de la taire. Une conversation non rattachée
    # applique le moindre privilège : les fichiers d'un dossier synchronisé
    # portent un périmètre de projet et restent hors de portée. Sans cette
    # mention, « rien ne correspond » et « rien n'est consultable ici »
    # produisent le même silence, et le modèle répond comme si ces documents
    # n'existaient pas — devant quelqu'un qui vient d'en indexer mille.
    #
    # La mention décrit le périmètre, jamais le contenu : elle ne franchit pas
    # la cloison qu'elle décrit.
    if scope == "global" and session is not None:
        with contextlib.suppress(Exception):
            hors_perimetre = await _compter_documents_de_projet(session)
            if hors_perimetre:
                context_parts.append(
                    f"**Périmètre documentaire** : cette conversation n'est "
                    f"rattachée à aucun projet, elle ne consulte donc que les "
                    f"documents généraux. {hors_perimetre} document(s) indexé(s) "
                    f"dans des projets sont hors du périmètre et ne te sont pas "
                    f"accessibles. Si l'utilisateur parle de documents que tu ne "
                    f"trouves pas, dis-lui de rattacher la conversation à son "
                    f"projet avec le sélecteur en haut du chat — n'invente jamais "
                    f"leur contenu et ne prétends pas qu'ils n'existent pas."
                )

    if context_parts:
        return "\n\n".join(context_parts)
    return None


async def _compter_documents_de_projet(session: AsyncSession) -> int:
    """Combien de documents indexés vivent dans un projet.

    `chunk_count > 0` n'est pas cosmétique : une indexation qui a échoué laisse
    la ligne en base sans rien avoir écrit dans l'index vectoriel. Les compter
    reviendrait à annoncer des documents introuvables.
    """
    from app.models.entities import FileMetadata

    resultat = await session.execute(
        select(func.count())
        .select_from(FileMetadata)
        .where(FileMetadata.scope == "project", FileMetadata.chunk_count > 0)
    )
    return int(resultat.scalar_one() or 0)


# ============================================================
# Entity Extraction Helper
# ============================================================


async def _get_existing_entity_names(session: AsyncSession) -> tuple[list[str], list[str]]:
    """Get names of existing contacts and projects to avoid duplicates.

    US-016 : requêtes ciblées sur les colonnes de nom (au lieu d'hydrater
    toutes les entités complètes à chaque message) + borne de sécurité - la
    liste ne sert qu'à éviter les doublons dans l'extraction d'entités.
    """
    contact_result = await session.execute(
        select(Contact.first_name, Contact.last_name, Contact.company).limit(2000)
    )
    contact_names = []
    for first_name, last_name, company in contact_result.all():
        name = " ".join(p for p in (first_name, last_name) if p)
        if not name and company:
            name = company
        if name:
            contact_names.append(name)

    project_result = await session.execute(select(Project.name).limit(2000))
    project_names = [name for (name,) in project_result.all() if name]

    # Pas de cap silencieux : au-delà, l'anti-doublons d'extraction devient
    # partiel (doublons possibles), l'utilisateur doit pouvoir le savoir.
    if len(contact_names) >= 2000 or len(project_names) >= 2000:
        logger.warning(
            "Anti-doublons d'extraction borné à 2000 noms (contacts=%d, projets=%d) "
            "- des doublons peuvent passer au-delà",
            len(contact_names), len(project_names),
        )

    return contact_names, project_names


async def _extract_entities_background(
    user_message: str,
    conversation_id: str,
    message_id: str,
) -> None:
    """
    Extrait les entités en arrière-plan (PERF-001).

    Les résultats ne sont plus envoyés via SSE (le stream est déjà fermé).
    À terme, ils pourront être envoyés via WebSocket ou polling endpoint.

    NOTE: Cette coroutine crée sa propre session DB car la session FastAPI
    est fermée après la réponse HTTP.
    """
    try:
        from app.models.database import get_session_context

        async with get_session_context() as session:
            extractor = get_entity_extractor()
            contact_names, project_names = await _get_existing_entity_names(session)

        extraction_result = await extractor.extract_entities(
            user_message=user_message,
            existing_contacts=contact_names,
            existing_projects=project_names,
        )

        if extraction_result.contacts or extraction_result.projects:
            logger.info(
                f"[Background] Detected {len(extraction_result.contacts)} contacts, "
                f"{len(extraction_result.projects)} projects in message {message_id}"
            )
            # TODO: Envoyer via WebSocket ou stocker pour polling
            # Pour l'instant, les entites sont loggees mais pas envoyees au frontend
            # Le frontend devra interroger un endpoint GET /api/chat/{conv_id}/entities

    except Exception as e:
        logger.warning(f"[Background] Entity extraction failed: {e}")


# ============================================================
# Chat Endpoints
# ============================================================


@router.post("/cancel/{conversation_id}")
async def cancel_generation(conversation_id: str):
    """
    Cancel an active generation (US-ERR-04).

    Returns True if generation was cancelled, False if not active.
    """
    # 0.46 : façade compatible J1b. La génération active se résout par sa
    # ProcessingTask, la demande suit le chemin canonique (cancel_requested +
    # adaptateur -> drapeau historique). Repli sur le drapeau seul pendant la
    # fenêtre où la ligne n'existe pas encore.
    from app.models.database import get_session_context as _ctx
    from app.models.processing import ProcessingTask as _PT
    from app.services import traitements as _traitements
    from sqlmodel import select as _select

    async with _ctx() as _session:
        _resultat = await _session.execute(
            _select(_PT).where(
                _PT.type.in_(("chat", "deep-research")),
                _PT.conversation_id == conversation_id,
                _PT.state.in_(tuple(EtatTacheTraitement.actifs())),
            ).order_by(_PT.created_at.desc())
        )
        _generation = _resultat.scalars().first()

    if _generation is not None:
        _arret = await _traitements.demander_arret(_generation.id)
        return {
            "cancelled": _arret is not None
            and _arret.state in (
                EtatTacheTraitement.CANCEL_REQUESTED,
                EtatTacheTraitement.CANCELLED,
            ),
            "conversation_id": conversation_id,
            "generation_id": _generation.id,
        }

    cancelled = _cancel_generation(conversation_id)
    return {
        "cancelled": cancelled,
        "conversation_id": conversation_id,
    }


class DeepResearchRequest(BaseModel):
    """Requête de recherche approfondie."""

    question: str
    conversation_id: str | None = None
    max_queries: int = 6


@router.post("/deep-research")
async def deep_research_endpoint(
    request: DeepResearchRequest,
    session: AsyncSession = Depends(get_session),
):
    """
    Lance une recherche approfondie multi-sources.

    Workflow : décomposition en sous-requêtes -> recherches parallèles -> synthèse LLM.
    Retourne un flux SSE avec la progression et le rapport final.
    """
    from app.services.deep_research import deep_research

    llm_service = get_llm_service()

    # Créer ou récupérer la conversation
    if request.conversation_id:
        result = await session.execute(
            select(Conversation).where(Conversation.id == request.conversation_id)
        )
        conversation = result.scalar_one_or_none()
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
    else:
        conversation = Conversation(title=f"Recherche : {request.question[:40]}")
        session.add(conversation)
        await session.flush()

    # Sauvegarder la question utilisateur
    user_message = Message(
        conversation_id=conversation.id,
        role="user",
        content=f"[Recherche approfondie] {request.question}",
    )
    session.add(user_message)
    await session.commit()

    async def stream_research() -> AsyncGenerator[str, None]:
        """Stream les événements de progression de la recherche."""
        # Envoyer l'ID de conversation pour le frontend
        yield f"data: {json.dumps({'type': 'conversation_id', 'content': conversation.id})}\n\n"

        # 0.46 (revue F7) : la recherche approfondie est un TRAITEMENT -
        # visible au panneau, annulable ENTRE deux étapes (coopératif), avec
        # un état final honnête et le partiel de synthèse persisté à l'arrêt.
        from app.services import task_registry as _registre
        from app.services import traitements as _traitements

        recherche = None
        arret_demande = {"drapeau": False}
        try:
            recherche = await _traitements.creer_traitement(
                type="deep-research",
                label=f"Recherche : {request.question[:70]}",
                conversation_id=conversation.id,
            )
            try:
                await recherche.demarrer()
                await recherche.lier_adaptateur(
                    _registre.AnnulationCooperative(
                        poser_drapeau=lambda: arret_demande.__setitem__("drapeau", True)
                    )
                )
            except _traitements.AnnuleAvantDemarrage:
                # L'annulation a gagné avant le démarrage : ne rien chercher.
                yield f"data: {json.dumps({'type': 'cancelled', 'content': ''})}\n\n"
                return
            except Exception:
                logger.warning("Suivi deep-research en panne", exc_info=True)
                with contextlib.suppress(Exception):
                    await recherche.terminer(
                        EtatTacheTraitement.FAILED,
                        error="suivi en panne à l'initialisation",
                    )
                recherche = None
            else:
                yield (
                    "data: "
                    + json.dumps({
                        "type": "generation",
                        "generation_id": recherche.id,
                        "conversation_id": conversation.id,
                    })
                    + "\n\n"
                )
        except Exception:
            logger.warning("Suivi deep-research indisponible", exc_info=True)
            recherche = None
        etat_recherche = {"etat": EtatTacheTraitement.DONE}

        full_synthesis = ""
        sources_data: list[dict] = []

        try:
            async for progress in deep_research(
                request.question,
                llm_service,
                max_queries=request.max_queries,
            ):
                if arret_demande["drapeau"]:
                    etat_recherche["etat"] = EtatTacheTraitement.CANCELLED
                    await _persister_message_partiel(
                        conversation.id, full_synthesis, llm_service
                    )
                    yield f"data: {json.dumps({'type': 'cancelled', 'content': ''})}\n\n"
                    return
                event_data: dict = {
                    "type": progress.type,
                    "content": progress.content,
                    "step": progress.step,
                    "total_steps": progress.total_steps,
                    "query": progress.query,
                }

                if progress.type == "synthesizing" and progress.content:
                    full_synthesis += progress.content
                    # Streamer le contenu de la synthèse comme du texte
                    yield f"data: {json.dumps({'type': 'text', 'content': progress.content})}\n\n"
                    continue

                if progress.type == "error":
                    etat_recherche["etat"] = EtatTacheTraitement.FAILED
                    etat_recherche["erreur"] = (progress.content or "")[:500]

                if progress.type == "done":
                    full_synthesis = progress.content
                    sources_data = [
                        {"title": s.title, "url": s.url, "snippet": s.snippet}
                        for s in progress.sources
                    ]
                    # Sauvegarder la réponse en base
                    try:
                        async with get_session() as save_session:
                            assistant_message = Message(
                                conversation_id=conversation.id,
                                role="assistant",
                                content=full_synthesis,
                            )
                            save_session.add(assistant_message)
                            await save_session.commit()
                    except Exception as e:
                        logger.error(f"Erreur sauvegarde recherche : {e}")

                    yield f"data: {json.dumps({'type': 'sources', 'content': json.dumps(sources_data)})}\n\n"
                    yield f"data: {json.dumps({'type': 'done', 'content': ''})}\n\n"
                    continue

                yield f"data: {json.dumps(event_data)}\n\n"
        except (GeneratorExit, asyncio.CancelledError):
            etat_recherche["etat"] = EtatTacheTraitement.CANCELLED
            await _persister_message_partiel(
                conversation.id, full_synthesis, llm_service
            )
            raise
        except Exception as e:
            etat_recherche["etat"] = EtatTacheTraitement.FAILED
            etat_recherche["erreur"] = str(e)[:500]
            raise
        finally:
            if recherche is not None:
                with contextlib.suppress(Exception):
                    await recherche.terminer(
                        etat_recherche["etat"],
                        error=etat_recherche.get("erreur"),
                    )

    return StreamingResponse(
        stream_research(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/send")
async def send_message(
    request: ChatRequest,
    session: AsyncSession = Depends(get_session),
):
    """
    Send a message and get a response.

    Supports both streaming (SSE) and non-streaming responses.
    Also handles /fichier and /analyse slash commands.
    """
    # Get or create conversation
    if request.conversation_id:
        result = await session.execute(
            select(Conversation).where(Conversation.id == request.conversation_id)
        )
        conversation = result.scalar_one_or_none()
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
    else:
        conversation = Conversation(title=request.message[:50])
        session.add(conversation)
        await session.flush()

    # Load conversation history for context (BUG-031 : DESC + reversed = 50 DERNIERS messages)
    history_result = await session.execute(
        select(Message)
        .where(Message.conversation_id == conversation.id)
        .order_by(Message.created_at.desc(), Message.id.desc())
        .limit(50)  # Limit history to last 50 messages
    )
    history_messages = list(reversed(history_result.scalars().all()))
    # Tranche 0f Variables V4 (finding Codex 4) : les échanges déterministes
    # (message-action + confirmation locale, commandes /) sont EXCLUS du
    # contexte LLM - bruit aujourd'hui, valeurs de variables demain. Les
    # user legacy (avant le tag) restent : bruit sans risque, documenté.
    history = [
        LLMMessage(role=msg.role, content=msg.content)
        for msg in history_messages
        if msg.model not in ("action-deterministe", "commande-deterministe")
        and not (msg.extra_data and '"deterministic": true' in msg.extra_data)
    ]

    # Save user message
    user_message = Message(
        conversation_id=conversation.id,
        role="user",
        content=request.message,
    )
    # BUG-160 : consigner les pièces jointes du tour. Sans cela, le message
    # part en base sans aucune mention du fichier et la conversation perd le
    # document dès le message suivant.
    _memoriser_pieces_jointes(user_message, request.file_paths)
    session.add(user_message)
    await session.commit()

    # Actions déterministes (tranche 1a, design 2026-07-10) : un message
    # composé UNIQUEMENT de `{action: ...}` s'exécute localement, ZÉRO appel
    # LLM. Action inconnue -> réponse locale listant l'allowlist, jamais
    # transmise au modèle. Un message ordinaire poursuit le flux inchangé.
    parsed_action = parse_action_message(request.message)
    produce_prompt: str | None = None
    if parsed_action is not None and parsed_action.kind == "produce":
        # Tranche 1b : production de fichier déterministe. Le skill est FORCÉ
        # (aucune détection d'intention), le LLM ne fait que rédiger le
        # contenu ; création/statut/erreur suivent le chemin déterministe du
        # 10/07 (skill_file avant done, échec visible). PAS de return.
        # Tranche 0b Variables V4 (finding Codex 1 VÉRIFIÉ) : request.message
        # reste IMMUABLE - le prompt dérivé vit dans produce_prompt et ne
        # repasse par AUCUN parseur déterministe (slash/inline) : une
        # directive [contact: ...] dans le sujet était réellement exécutée.
        # Tranche 3 Variables V4 : le sujet est résolu ({nom} -> valeur,
        # listes en bloc) APRÈS classification - la valeur est une donnée,
        # le skill et le format sont déjà fixés. Erreur de borne -> réponse
        # locale (branche variable), aucun appel LLM.
        produce_subject = parsed_action.subject or ""
        if "{" in produce_subject:
            from app.services.variables_service import (
                VariableError as _VariableError,
            )
            from app.services.variables_service import resolve_message

            try:
                produce_subject, _ = await resolve_message(
                    session, produce_subject, list_mode="block"
                )
            except _VariableError as e:
                parsed_action = ParsedChatAction(
                    kind="variable", raw=parsed_action.raw,
                    var_op="erreur", var_message=str(e),
                )
                produce_subject = None
        if produce_subject is not None:
            request.skill_id = parsed_action.skill_id
            produce_prompt = (
                "Rédige le contenu complet et structuré du document demandé : "
                f"{produce_subject}"
            )
            # Rédaction pure : la boucle d'outils (MCP/workspace) n'apporte
            # rien à la production d'un document et introduit de l'aléa.
            request.disable_tools = True
            parsed_action = None
    if parsed_action is not None:
        client_action: dict[str, str] | None = None
        if parsed_action.kind == "navigate":
            confirmation = f"J'ouvre {parsed_action.label}."
            client_action = {
                "action": "navigate",
                "action_id": parsed_action.action_id,
                "target": parsed_action.target,
            }
        elif parsed_action.kind == "variable":
            # Tranche 2 Variables V4 : verbes variable exécutés localement,
            # zéro LLM (le point de validation vit dans variables_service).
            from app.services.variables_service import execute_chat_variable_action

            confirmation = await execute_chat_variable_action(
                session,
                parsed_action.var_op or "erreur",
                parsed_action.var_name,
                parsed_action.var_value,
                parsed_action.var_is_list,
                parsed_action.var_message,
            )
        elif parsed_action.kind == "help":
            confirmation = (
                "Actions disponibles (exécutées localement, sans IA pour la "
                "navigation) :\n" + available_actions_text()
            )
        else:
            confirmation = (
                f"Action inconnue : « {parsed_action.raw} ». "
                "Actions disponibles :\n" + available_actions_text()
            )
        _marquer_deterministe(user_message)
        assistant_message = Message(
            conversation_id=conversation.id,
            role="assistant",
            content=confirmation,
            model="action-deterministe",
            extra_data=json.dumps(
                {
                    "action_result": {
                        "status": "success" if client_action else "unknown_action",
                        "client_action": client_action,
                    }
                }
            ),
        )
        session.add(assistant_message)
        await session.commit()

        if request.stream:
            async def _action_stream() -> AsyncGenerator[str, None]:
                if client_action is not None:
                    ca_chunk = StreamChunk(
                        type="client_action",
                        content="",
                        conversation_id=conversation.id,
                        client_action=client_action,
                    )
                    yield f"data: {json.dumps(ca_chunk.model_dump())}\n\n"
                text_chunk = StreamChunk(
                    type="text", content=confirmation, conversation_id=conversation.id
                )
                yield f"data: {json.dumps(text_chunk.model_dump())}\n\n"
                done_chunk = StreamChunk(
                    type="done",
                    content="",
                    conversation_id=conversation.id,
                    message_id=assistant_message.id,
                )
                yield f"data: {json.dumps(done_chunk.model_dump())}\n\n"

            return StreamingResponse(
                _action_stream(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no",
                },
            )

        return ChatResponse(
            id=assistant_message.id,
            conversation_id=conversation.id,
            content=confirmation,
            created_at=assistant_message.created_at,
            client_action=client_action,
        )

    # Court-circuit déterministe : /contact et /projet s'exécutent sans LLM ;
    # /rdv prépare une mutation qui reste bloquée derrière la confirmation.
    # Branche produire : aucun parseur ne retouche le message (tranche 0b).
    parsed_cmd = None if produce_prompt is not None else parse_slash_command(request.message)
    if parsed_cmd is not None:
        cmd_name, cmd_rest = parsed_cmd
        # Périmètre de la conversation : une entité créée par une commande
        # (`/contact`) ou une directive inline (`[contact: ...]`) appartient au
        # dossier depuis lequel on l'a saisie, pas à tout l'espace.
        _perim_cmd, _perim_cmd_id = await _perimetre_de_conversation(
            conversation.id, session
        )
        command_outcome = await execute_slash_command_outcome(
            cmd_name, cmd_rest, session,
            scope=_perim_cmd, scope_id=_perim_cmd_id,
            conversation_id=conversation.id,
        )
        confirmation = command_outcome.content
        _marquer_deterministe(user_message)
        assistant_message = Message(
            conversation_id=conversation.id,
            role="assistant",
            content=confirmation,
            model="commande-deterministe",
        )
        session.add(assistant_message)
        await session.commit()

        if request.stream:
            async def _command_stream() -> AsyncGenerator[str, None]:
                if command_outcome.confirmation is not None:
                    confirm_chunk = StreamChunk(
                        type="confirmation_required",
                        content="",
                        conversation_id=conversation.id,
                        tool_name=command_outcome.confirmation["tool_name"],
                        confirmation=command_outcome.confirmation,
                    )
                    yield f"data: {json.dumps(confirm_chunk.model_dump())}\n\n"
                text_chunk = StreamChunk(
                    type="text", content=confirmation, conversation_id=conversation.id
                )
                yield f"data: {json.dumps(text_chunk.model_dump())}\n\n"
                done_chunk = StreamChunk(
                    type="done",
                    content="",
                    conversation_id=conversation.id,
                    message_id=assistant_message.id,
                )
                yield f"data: {json.dumps(done_chunk.model_dump())}\n\n"

            return StreamingResponse(
                _command_stream(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no",
                },
            )

        return ChatResponse(
            id=assistant_message.id,
            conversation_id=conversation.id,
            content=confirmation,
            created_at=assistant_message.created_at,
            confirmations=(
                [command_outcome.confirmation]
                if command_outcome.confirmation is not None
                else None
            ),
        )

    # Directives inline [action: arguments] (suggestion Dr_logic-3D) : les mêmes
    # commandes déterministes, insérables n'importe où dans le prompt et
    # cumulables. Les mutations Agenda sont seulement préparées ; leurs cartes
    # de confirmation s'affichent avant toute exécution.
    inline_preamble = ""
    inline_pending_confirmations: list[dict[str, Any]] = []
    actions_context: str | None = None
    llm_user_message = request.message
    if produce_prompt is not None:
        # Tranche 0b : le prompt de rédaction dérivé du sujet est le texte
        # LLM, et il n'est JAMAIS re-scanné par les directives inline.
        llm_user_message = produce_prompt
        cleaned_message, inline_cmds = request.message, []
    else:
        cleaned_message, inline_cmds = parse_inline_commands(request.message)
    if inline_cmds:
        _perim_inline, _perim_inline_id = await _perimetre_de_conversation(
            conversation.id, session
        )
        command_outcomes = [
            await execute_slash_command_outcome(
                name, rest, session,
                scope=_perim_inline, scope_id=_perim_inline_id,
                conversation_id=conversation.id,
            )
            for name, rest in inline_cmds
        ]
        confirmations = [outcome.content for outcome in command_outcomes]
        inline_pending_confirmations = [
            outcome.confirmation
            for outcome in command_outcomes
            if outcome.confirmation is not None
        ]
        inline_block = (
            "\n".join(f"- {c}" for c in confirmations)
            if len(confirmations) > 1
            else confirmations[0]
        )

        if not cleaned_message:
            # Message composé uniquement de directives : réponse déterministe pure
            _marquer_deterministe(user_message)
            assistant_message = Message(
                conversation_id=conversation.id,
                role="assistant",
                content=inline_block,
                model="commande-deterministe",
            )
            session.add(assistant_message)
            await session.commit()

            if request.stream:
                async def _inline_stream() -> AsyncGenerator[str, None]:
                    for pending_confirmation in inline_pending_confirmations:
                        confirm_chunk = StreamChunk(
                            type="confirmation_required",
                            content="",
                            conversation_id=conversation.id,
                            tool_name=pending_confirmation["tool_name"],
                            confirmation=pending_confirmation,
                        )
                        yield f"data: {json.dumps(confirm_chunk.model_dump())}\n\n"
                    text_chunk = StreamChunk(
                        type="text", content=inline_block, conversation_id=conversation.id
                    )
                    yield f"data: {json.dumps(text_chunk.model_dump())}\n\n"
                    done_chunk = StreamChunk(
                        type="done",
                        content="",
                        conversation_id=conversation.id,
                        message_id=assistant_message.id,
                    )
                    yield f"data: {json.dumps(done_chunk.model_dump())}\n\n"

                return StreamingResponse(
                    _inline_stream(),
                    media_type="text/event-stream",
                    headers={
                        "Cache-Control": "no-cache",
                        "Connection": "keep-alive",
                        "X-Accel-Buffering": "no",
                    },
                )

            return ChatResponse(
                id=assistant_message.id,
                conversation_id=conversation.id,
                content=inline_block,
                created_at=assistant_message.created_at,
                confirmations=inline_pending_confirmations or None,
            )

        # Message mixte : le LLM reçoit le message nettoyé + le récap des actions
        inline_preamble = inline_block + "\n\n"
        llm_user_message = cleaned_message
        actions_context = (
            "RÉSULTATS DES COMMANDES DÉTERMINISTES. Certaines actions peuvent "
            "être seulement préparées et attendre la confirmation humaine ; ne "
            "jamais les présenter comme exécutées :\n" + inline_block
        )

    # Tranche 3 Variables V4 : substitution {nom} sur le SEUL texte destiné
    # au LLM, APRÈS tous les parseurs déterministes (le brut reste la bulle
    # et l'historique - pas de re-résolution rétroactive, finding 10) et
    # AVANT check_prompt_safety (finding 4). La détection de skill reçoit le
    # texte PRÉ-substitution (finding 3 : une valeur ne choisit pas un skill).
    detection_message = llm_user_message
    if produce_prompt is None and "{" in llm_user_message:
        from app.services.variables_service import (
            VariableError as _VariableError,
        )
        from app.services.variables_service import resolve_message

        try:
            llm_user_message, _unknown_vars = await resolve_message(
                session, llm_user_message
            )
        except _VariableError as e:
            borne_message = str(e)
            assistant_message = Message(
                conversation_id=conversation.id,
                role="assistant",
                content=borne_message,
                model="action-deterministe",
            )
            _marquer_deterministe(user_message)
            session.add(assistant_message)
            await session.commit()
            if request.stream:
                async def _borne_stream() -> AsyncGenerator[str, None]:
                    text_chunk = StreamChunk(
                        type="text", content=borne_message,
                        conversation_id=conversation.id,
                    )
                    yield f"data: {json.dumps(text_chunk.model_dump())}\n\n"
                    done_chunk = StreamChunk(
                        type="done", content="",
                        conversation_id=conversation.id,
                        message_id=assistant_message.id,
                    )
                    yield f"data: {json.dumps(done_chunk.model_dump())}\n\n"

                return StreamingResponse(
                    _borne_stream(),
                    media_type="text/event-stream",
                    headers={
                        "Cache-Control": "no-cache",
                        "Connection": "keep-alive",
                        "X-Accel-Buffering": "no",
                    },
                )
            return ChatResponse(
                id=assistant_message.id,
                conversation_id=conversation.id,
                content=borne_message,
                created_at=assistant_message.created_at,
            )

    # Handle streaming response
    if request.stream:
        return StreamingResponse(
            _stream_response(
                conversation.id, llm_user_message, session, history,
                skill_id=request.skill_id, file_paths=request.file_paths,
                disable_tools=request.disable_tools,
                preamble=inline_preamble, actions_context=actions_context,
                pending_confirmations=inline_pending_confirmations,
                allow_file_commands=produce_prompt is None,
                detection_message=detection_message,
            ),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    # Non-streaming response using LLM service
    # SEC : appliquer le filtre anti-injection AUSSI sur le chemin non-stream.
    # Il n'etait applique que dans _stream_response -> en stream=false, le prompt
    # injection passait et le system prompt pouvait etre exfiltre (rapport Syn 14/06).
    # Tranche 0d Variables V4 (finding Codex 4 VÉRIFIÉ) : le contrôle porte sur
    # le texte RÉELLEMENT envoyé au LLM (llm_user_message, prompt produire
    # compris), AVANT toute récupération du service.
    from datetime import UTC, datetime

    from app.services.prompt_security import check_prompt_safety
    security_check = check_prompt_safety(llm_user_message)
    if not security_check.is_safe:
        logger.warning(
            f"Blocked message (non-stream) due to {security_check.threat_type}: "
            f"level={security_check.threat_level.value}"
        )
        return ChatResponse(
            id="",
            conversation_id=conversation.id,
            content="Message bloqué pour raison de sécurité.",
            created_at=datetime.now(UTC),
        )

    llm_service = get_llm_service()
    messages = history + [LLMMessage(role="user", content=llm_user_message)]

    # Get relevant memory context (0d : même texte que le payload LLM,
    # parité avec le chemin stream)
    memory_context = await _get_memory_context(
        llm_user_message, conversation_id=conversation.id, session=session
    )

    # Périmètre de la conversation, appliqué aux pièces jointes qu'elle
    # indexe : un document déposé dans un dossier client lui appartient.
    _perimetre_conv, _perimetre_conv_id = await _perimetre_de_conversation(
        conversation.id, session
    )
    # Même règle que les contacts et les projets : une pièce jointe sans dossier
    # explicite reste dans SA conversation. Elle devenait `global` — donc
    # consultable depuis tous les dossiers — y compris déposée depuis une
    # conversation « Tous les projets » (revue de clôture).
    if _perimetre_conv == "project" and _perimetre_conv_id:
        perimetre_fichiers, perimetre_fichiers_id = "project", _perimetre_conv_id
    else:
        perimetre_fichiers, perimetre_fichiers_id = "conversation", conversation.id


    # Check for file commands and add file context (0e : parité stream,
    # jamais sur un texte dérivé - le prompt produire n'est pas scanné)
    file_commands = (
        [] if produce_prompt is not None else _parse_file_commands(llm_user_message)
    )
    file_contexts = []
    for cmd, path in file_commands:
        file_ctx, error = await _get_file_context(
            path, session, cmd, scope=perimetre_fichiers, scope_id=perimetre_fichiers_id
        )
        if file_ctx:
            file_contexts.append(file_ctx)
        elif error:
            logger.warning(f"File command error: {error}")

    # BUG-044 : Traiter les fichiers joints (drag & drop)
    if request.file_paths:
        for fp in request.file_paths:
            file_ctx, error = await _get_file_context(
                fp, session, "analyse",
                scope=perimetre_fichiers, scope_id=perimetre_fichiers_id,
            )
            if file_ctx:
                file_contexts.append(file_ctx)
            elif error:
                logger.warning(f"Attached file error: {error}")

    # BUG-160 : même rappel que sur le chemin streaming. Pas de contexte
    # ici : le chemin non-stream n'a ni génération ni annulation.
    for fp in await _pieces_jointes_recentes(
        conversation.id, session, deja_fournis=list(request.file_paths or [])
    ):
        file_ctx, error = await _get_file_context(
            fp, session, "analyse",
            scope=perimetre_fichiers, scope_id=perimetre_fichiers_id,
        )
        if file_ctx:
            file_contexts.append(file_ctx)
        elif error:
            logger.info("Pièce jointe d'un tour précédent non rejouée : %s", error)

    # Combine memory and file contexts
    if file_contexts:
        # Revue Soso : borner le bloc ENTIER, sinon quatre documents rejoués à
        # 15 000 caractères chacun évincent l'historique de la conversation
        # sans que rien ne le signale.
        file_contexts, ecartes = borner_bloc_fichiers(file_contexts)
        if ecartes:
            logger.info("%d document(s) écarté(s) du contexte : plafond atteint", ecartes)
            file_contexts.append(
                f"[{ecartes} autre(s) document(s) de cette conversation n'ont pas pu "
                "être transmis : le volume total dépasse ce que le modèle peut "
                "recevoir. Dis-le à l'utilisateur s'il pose une question qui en dépend.]"
            )
        file_context_str = "\n\n".join(file_contexts)
        if memory_context:
            memory_context = f"{memory_context}\n\n{file_context_str}"
        else:
            memory_context = file_context_str

    # Directives inline déjà exécutées : le LLM doit le savoir (pas de re-création)
    if actions_context:
        memory_context = (
            f"{actions_context}\n\n{memory_context}" if memory_context else actions_context
        )

    context = llm_service.prepare_context(messages, memory_context=memory_context)

    # Collect full response (non-streaming)
    # raise_on_error=True : sans ça, un StreamEvent(type="error") d'un provider
    # était avalé -> assistant_content restait vide et le except ne se déclenchait
    # jamais (message assistant VIDE renvoyé au lieu d'une erreur). Rapport Syn 14/06.
    assistant_content = ""
    usage_sink: dict = {}
    try:
        async for chunk in llm_service.stream_response(context, raise_on_error=True, usage_sink=usage_sink):
            assistant_content += chunk
    except Exception as e:
        logger.error(f"LLM error: {e}", exc_info=True)
        # Revue 0.48 p2 (F1) : le message persiste en base et part à l'écran.
        assistant_content = f"Désolée : {message_pour_ecran(e, ou='pendant la génération')}"

    # F-11 : post-processing - convertir les tableaux Markdown résiduels en
    # listes à puces pour les récaps lisibles.
    assistant_content = convert_markdown_tables_to_bullets(assistant_content)

    # Confirmations des directives inline en tête de réponse (vérité d'exécution)
    if inline_preamble:
        assistant_content = inline_preamble + assistant_content

    # BUG-027 : suivi des tokens sur le chemin non-stream (etait absent -> le
    # token tracker restait aveugle et tokens_in/out remontaient null).
    # Usage réel du provider (usage_sink) quand disponible, sinon estimation
    # ~1 mot = 2 tokens en filet (providers pas encore migrés, cf CLAUDE.md).
    input_tokens = usage_sink.get("input_tokens") or len(request.message.split()) * 2
    output_tokens = usage_sink.get("output_tokens") or len(assistant_content.split()) * 2
    get_token_tracker().record_usage(
        conversation_id=conversation.id,
        model=llm_service.config.model,
        provider=llm_service.config.provider.value,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
    )

    assistant_message = Message(
        conversation_id=conversation.id,
        role="assistant",
        content=assistant_content,
        model=llm_service.config.model,
        provider=llm_service.config.provider.value,
        tokens_in=input_tokens,
        tokens_out=output_tokens,
    )
    session.add(assistant_message)
    await session.commit()

    return ChatResponse(
        id=assistant_message.id,
        conversation_id=conversation.id,
        content=assistant_content,
        model=llm_service.config.model,
        provider=llm_service.config.provider.value,
        tokens_in=input_tokens,
        tokens_out=output_tokens,
        created_at=assistant_message.created_at,
        confirmations=inline_pending_confirmations or None,
    )


async def _stream_response(
    conversation_id: str,
    user_message: str,
    session: AsyncSession,
    history: list[LLMMessage] | None = None,
    skill_id: str | None = None,
    file_paths: list[str] | None = None,
    disable_tools: bool = False,
    preamble: str = "",
    actions_context: str | None = None,
    pending_confirmations: list[dict[str, Any]] | None = None,
    allow_file_commands: bool = True,
    detection_message: str | None = None,
) -> AsyncGenerator[str, None]:
    """Stream response chunks as Server-Sent Events with MCP tool support."""

    # 0.46 : chaque génération LLM est un TRAITEMENT - ProcessingTask créée
    # immédiatement (jamais différée : courses garanties), son id EST le
    # generation_id, émis au SSE dès le premier événement. L'adaptateur pose
    # le drapeau historique : le panneau et la façade /cancel convergent.
    from app.services import task_registry as _registre
    from app.services import traitements as _traitements

    generation = None
    annulee_avant_demarrage = False
    # 0.47 : le contexte naît AVANT le handle - l'adaptateur canonique pose
    # directement le token de CETTE génération (aucune fenêtre où une
    # demande rejouée viserait l'entrée d'une génération précédente).
    contexte_execution = _register_generation(conversation_id)
    try:
        generation = await _traitements.creer_traitement(
            type="chat",
            label=(user_message or "Message")[:80],
            conversation_id=conversation_id,
        )
        contexte_execution.generation_id = generation.id
        try:
            await generation.demarrer()
            await generation.lier_adaptateur(
                _registre.AnnulationCooperative(
                    poser_drapeau=contexte_execution.demander_arret
                )
            )
        except _traitements.AnnuleAvantDemarrage:
            # Passe 2 de revue : l'annulation a GAGNÉ la course avant le
            # démarrage - la ligne dit cancelled, produire quand même serait
            # exactement le mensonge que ce chantier corrige.
            annulee_avant_demarrage = True
        except Exception:
            # Échec APRÈS la création : terminer la ligne (failed) plutôt que
            # d'abandonner un running fantôme, puis répondre sans suivi.
            logger.warning("Suivi de génération en panne", exc_info=True)
            with contextlib.suppress(Exception):
                await generation.terminer(
                    EtatTacheTraitement.FAILED,
                    error="suivi en panne à l'initialisation",
                )
            generation = None
    except Exception:
        # Le suivi ne tue JAMAIS le chat : sans base (tests unitaires du
        # wrapper, hoquet au démarrage), on répond quand même - le drapeau
        # historique reste le filet d'annulation.
        logger.warning("Suivi de génération indisponible", exc_info=True)
        generation = None

    if annulee_avant_demarrage:
        _unregister_generation(conversation_id, contexte=contexte_execution)
        yield f"data: {json.dumps({'type': 'cancelled', 'content': ''})}\n\n"
        return
    etat_generation: dict[str, Any] = {"etat": EtatTacheTraitement.DONE}
    if generation is not None:
        yield (
            "data: "
            + json.dumps({
                "type": "generation",
                "generation_id": generation.id,
                "conversation_id": conversation_id,
            })
            + "\n\n"
        )

    # J1b (31/07/2026) : l'annulation ne doit pas attendre le prochain chunk.
    #
    # L'ancienne boucle ne consultait le drapeau qu'APRÈS avoir reçu un morceau.
    # Or c'est précisément quand le fournisseur est lent ou bloqué que
    # l'utilisateur veut arrêter : la boucle restait suspendue sur le `__anext__`
    # et le producteur continuait de consommer des tokens.
    #
    # On met donc la production et la surveillance en concurrence, et on ferme
    # explicitement le générateur pour propager l'interruption au producteur.
    producteur = _do_stream_response(
        conversation_id, user_message, session, history,
        skill_id=skill_id, file_paths=file_paths,
        disable_tools=disable_tools,
        preamble=preamble, actions_context=actions_context,
        pending_confirmations=pending_confirmations,
        allow_file_commands=allow_file_commands,
        detection_message=detection_message,
        contexte=contexte_execution,
    )
    # Déclarées hors de la boucle : le `finally` doit pouvoir les neutraliser
    # même quand c'est le CLIENT qui disparaît en pleine attente (fenêtre
    # fermée, réseau coupé). Starlette referme alors ce générateur, et fermer
    # le producteur pendant que son `__anext__` tourne encore lève
    # `RuntimeError: aclose(): asynchronous generator is already running`.
    prochain: asyncio.Future[str] | None = None
    surveillance: asyncio.Future[None] | None = None
    try:
        while True:
            prochain = asyncio.ensure_future(producteur.__anext__())
            surveillance = asyncio.ensure_future(
                _attendre_annulation(contexte_execution, conversation_id)
            )
            termines, _ = await asyncio.wait(
                {prochain, surveillance}, return_when=asyncio.FIRST_COMPLETED
            )

            if surveillance in termines and not prochain.done():
                # Annuler l'attente du prochain morceau ET la laisser se
                # terminer : `aclose()` refuse de fermer un générateur encore
                # en cours d'exécution.
                prochain.cancel()
                with contextlib.suppress(asyncio.CancelledError, StopAsyncIteration):
                    await prochain
                etat_generation["etat"] = EtatTacheTraitement.CANCELLED
                yield f"data: {json.dumps({'type': 'cancelled', 'content': ''})}\n\n"
                return

            surveillance.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await surveillance
            try:
                chunk = prochain.result()
            except StopAsyncIteration:
                return
            except IndexationAbandonnee:
                # Passe 2 de revue (P2-9) : l'abandon d'une indexation de
                # pièce jointe est une ANNULATION, pas une panne de stream -
                # le client reçoit un cancelled propre.
                etat_generation["etat"] = EtatTacheTraitement.CANCELLED
                yield f"data: {json.dumps({'type': 'cancelled', 'content': ''})}\n\n"
                return

            # Une génération qui produit encore n'est pas orpheline : sans ce
            # rafraîchissement, _cleanup_stale_generations retirait après 5 min
            # l'entrée d'un stream VIVANT (second panel de revue).
            if _active_generations.get(conversation_id) is contexte_execution:
                _generation_timestamps[conversation_id] = time.monotonic()

            if contexte_execution.annulation_observee():
                etat_generation["etat"] = EtatTacheTraitement.CANCELLED
                yield f"data: {json.dumps({'type': 'cancelled', 'content': ''})}\n\n"
                return
            # Revue jalon (F5) : un flux qui émet une erreur puis se termine
            # proprement n'est PAS un succès - le panneau mentirait.
            if '"type": "error"' in chunk:
                etat_generation["etat"] = EtatTacheTraitement.FAILED
                with contextlib.suppress(Exception):
                    etat_generation["erreur"] = json.loads(
                        chunk.removeprefix("data: ").strip()
                    ).get("content", "")[:500]
            yield chunk
    except BaseException as sortie:
        # Déconnexion (GeneratorExit) = travail réellement arrêté ; toute
        # autre sortie non prévue est un échec. L'état terminal reste posé
        # par CE producteur, jamais par l'endpoint d'annulation.
        if isinstance(sortie, GeneratorExit) or contexte_execution.annulation_observee():
            etat_generation["etat"] = EtatTacheTraitement.CANCELLED
        else:
            etat_generation["etat"] = EtatTacheTraitement.FAILED
            logger.error(
                "Génération %s en échec",
                generation.id if generation is not None else conversation_id,
                exc_info=True,
            )
        raise
    finally:
        # Ordre imposé par asyncio :
        #
        # 1. neutraliser les deux tâches encore en vol. Si le client est parti
        #    pendant l'attente, `prochain` exécute toujours le producteur ;
        # 2. seulement ensuite fermer le producteur — `aclose()` REFUSE de
        #    fermer un générateur en cours d'exécution et lèverait un
        #    `RuntimeError` ;
        # 3. et quoi qu'il arrive, retirer l'entrée du registre. Elle y restait
        #    quand `aclose()` levait : l'identifiant paraissait éternellement en
        #    cours de génération et faussait les annulations suivantes.
        try:
            for tache in (prochain, surveillance):
                if tache is not None and not tache.done():
                    tache.cancel()
                    # `CancelledError` n'hérite pas d'`Exception` : les deux
                    # sont nécessaires. Une erreur du producteur pendant sa
                    # fermeture ne doit pas empêcher le nettoyage du registre.
                    with contextlib.suppress(asyncio.CancelledError, Exception):
                        await tache
            with contextlib.suppress(Exception):
                await producteur.aclose()
        finally:
            # Finding 4 : `finish_stream` n'était atteint qu'au bout du chemin
            # nominal. Une annulation ou une déconnexion laissait le flux
            # éternellement « actif » dans Réglages > Performances, et les
            # statistiques ignoraient les flux arrêtés. L'appel est idempotent
            # (`pop` sur le registre) : le doublon avec le chemin nominal est
            # sans effet.
            with contextlib.suppress(Exception):
                get_performance_monitor().finish_stream(conversation_id)
            _unregister_generation(
                conversation_id, contexte=contexte_execution
            )
            if generation is not None:
                with contextlib.suppress(Exception):
                    await generation.terminer(
                        etat_generation["etat"],
                        error=etat_generation.get("erreur"),
                    )


async def _persister_message_partiel(
    conversation_id: str, contenu: str, llm_service: Any
) -> None:
    """Sauve le texte partiel d'une génération arrêtée - une seule fois.

    Session NEUVE : celle de la requête peut être fermée quand on arrive ici
    par la fermeture du générateur (client parti, wrapper aclose)."""
    if not contenu or not contenu.strip():
        return
    try:
        from app.models.database import get_session_context as _ctx

        async with _ctx() as session_partiel:
            deja = await session_partiel.execute(
                select(Message).where(
                    Message.conversation_id == conversation_id,
                    Message.role == "assistant",
                    Message.content == contenu,
                )
            )
            if deja.scalars().first() is not None:
                return
            session_partiel.add(Message(
                conversation_id=conversation_id,
                role="assistant",
                content=contenu,
                model=llm_service.config.model,
                provider=llm_service.config.provider.value,
            ))
            await session_partiel.commit()
    except Exception:
        logger.warning("Message partiel non persisté", exc_info=True)


async def _attendre_annulation(
    contexte: ContexteExecution,
    conversation_id: str | None = None,
    intervalle_s: float = 0.05,
) -> None:
    """Se résout dès que l'annulation de CETTE génération est demandée.

    Passe 2 de revue (P2-11) : rafraîchit aussi le timestamp - une
    génération vivante mais silencieuse (outil long) restait purgeable par
    _cleanup_stale_generations après 5 minutes.
    """
    while not contexte.annulation_observee():
        if (
            conversation_id is not None
            and _active_generations.get(conversation_id) is contexte
        ):
            _generation_timestamps[conversation_id] = time.monotonic()
        await asyncio.sleep(intervalle_s)


def retirer_outils_deja_en_attente(
    tools: list[dict[str, Any]],
    pending_confirmations: list[dict[str, Any]] | None,
) -> list[dict[str, Any]]:
    """Retire les outils sensibles dont une action attend déjà validation.

    Un message mixte (texte + directive inline) prépare l'action par la voie
    déterministe et relaie sa carte, puis appelle le modèle avec le même outil
    encore disponible : le modèle le rappelle, et une seconde carte s'affiche
    pour un seul et même rendez-vous.

    On ne coupe QUE l'outil concerné : le modèle doit garder de quoi lire,
    chercher et répondre. Toute entrée douteuse est ignorée (fail-open) — on
    ne prive pas le modèle d'un outil sur une donnée qu'on ne comprend pas.
    """
    if not pending_confirmations:
        return tools

    bloques = {
        _base_tool_name(entree["tool_name"])
        for entree in pending_confirmations
        if isinstance(entree, dict) and isinstance(entree.get("tool_name"), str)
    }
    if not bloques:
        return tools

    return [
        outil
        for outil in tools
        if _base_tool_name(outil.get("function", {}).get("name", "")) not in bloques
    ]


async def _do_stream_response(
    conversation_id: str,
    user_message: str,
    session: AsyncSession,
    history: list[LLMMessage] | None = None,
    skill_id: str | None = None,
    file_paths: list[str] | None = None,
    disable_tools: bool = False,
    preamble: str = "",
    actions_context: str | None = None,
    pending_confirmations: list[dict[str, Any]] | None = None,
    allow_file_commands: bool = True,
    detection_message: str | None = None,
    contexte: ContexteExecution | None = None,
) -> AsyncGenerator[str, None]:
    """Internal streaming implementation."""

    def _annulation_observee() -> bool:
        # 0.47 : le token de CETTE génération est l'autorité ; le drapeau
        # par conversation n'est que le repli des appels sans contexte.
        if contexte is not None:
            return bool(contexte.annulation_observee())
        return _is_cancelled(conversation_id)

    for pending_confirmation in pending_confirmations or []:
        confirm_chunk = StreamChunk(
            type="confirmation_required",
            content="",
            conversation_id=conversation_id,
            tool_name=pending_confirmation["tool_name"],
            confirmation=pending_confirmation,
        )
        yield f"data: {json.dumps(confirm_chunk.model_dump())}\n\n"
    # BUG-136 : ouvre la collecte des fichiers générés par les OUTILS pendant
    # ce tour (generate_document, appelable N fois par le modèle) - drainée
    # avant `done` pour émettre une carte par fichier.
    from app.services.workspace_tools import (
        drain_generated_files,
        start_generated_files_collection,
    )
    start_generated_files_collection()
    # BUG-093 : Détection automatique de skill + syntaxe {{action: ...}}.
    # Tranche 3 Variables V4 (finding Codex 3 VÉRIFIÉ) : la détection porte
    # sur le texte PRÉ-substitution (detection_message) - une valeur de
    # variable ne peut ni forcer {{action:}} ni déclencher un mot-clé. Le
    # tag éventuel est ensuite retiré du texte LLM résolu.
    from app.services.skills.intent_detector import (
        parse_action_syntax,
        resolve_skill_from_message,
    )
    detection_source = (
        detection_message if detection_message is not None else user_message
    )
    resolved_skill_id, resolved_format, cleaned_detection = (
        resolve_skill_from_message(detection_source, explicit_skill_id=skill_id)
    )
    if detection_message is None:
        user_message = cleaned_detection
    else:
        _tag_llm, user_message = parse_action_syntax(user_message)
    if resolved_skill_id and resolved_skill_id != skill_id:
        logger.info(f"Skill auto-détecté : {resolved_skill_id} (format: {resolved_format})")
    skill_id = resolved_skill_id

    # Sprint 2 - PERF-2.11: Check for prompt injection
    from app.services.prompt_security import check_prompt_safety
    security_check = check_prompt_safety(user_message)
    if not security_check.is_safe:
        logger.warning(
            f"Blocked message due to {security_check.threat_type}: "
            f"level={security_check.threat_level.value}"
        )
        yield f"data: {json.dumps({'type': 'error', 'content': 'Message bloqué pour raison de sécurité.'})}\n\n"
        return

    llm_service = get_llm_service()
    mcp_service = get_mcp_service()

    # Start performance tracking (US-PERF-01)
    perf_monitor = get_performance_monitor()
    stream_metrics = perf_monitor.start_stream(
        conversation_id,
        provider=llm_service.config.provider.value,
        model=llm_service.config.model,
    )
    first_token_recorded = False

    # Build context with conversation history
    messages = history or []
    messages.append(LLMMessage(role="user", content=user_message))

    # Get relevant memory context for the user's message
    memory_context = await _get_memory_context(
        user_message, conversation_id=conversation_id, session=session
    )

    # Périmètre de la conversation, appliqué aux pièces jointes qu'elle
    # indexe : un document déposé dans un dossier client lui appartient.
    _perimetre_conv, _perimetre_conv_id = await _perimetre_de_conversation(
        conversation_id, session
    )
    # Même règle que les contacts et les projets : une pièce jointe sans dossier
    # explicite reste dans SA conversation. Elle devenait `global` — donc
    # consultable depuis tous les dossiers — y compris déposée depuis une
    # conversation « Tous les projets » (revue de clôture).
    if _perimetre_conv == "project" and _perimetre_conv_id:
        perimetre_fichiers, perimetre_fichiers_id = "project", _perimetre_conv_id
    else:
        perimetre_fichiers, perimetre_fichiers_id = "conversation", conversation_id


    # Check for file commands and add file context.
    # Tranche 0e Variables V4 (finding Codex 2 VÉRIFIÉ) : jamais de
    # redétection sur un texte dérivé (prompt produire) - le flag vient du
    # site d'appel qui connaît la provenance du texte.
    file_commands = _parse_file_commands(user_message) if allow_file_commands else []
    file_contexts = []
    file_errors = []

    for cmd, path in file_commands:
        file_ctx, error = await _get_file_context(
            path, session, cmd, scope=perimetre_fichiers,
            scope_id=perimetre_fichiers_id, contexte=contexte,
        )
        if file_ctx:
            file_contexts.append(file_ctx)
        elif error:
            file_errors.append(error)
            logger.warning(f"File command error: {error}")

    # BUG-044 : Traiter les fichiers joints (drag & drop) via file_paths
    if file_paths:
        for fp in file_paths:
            file_ctx, error = await _get_file_context(
                fp, session, "analyse",
                scope=perimetre_fichiers, scope_id=perimetre_fichiers_id,
                contexte=contexte,
            )
            if file_ctx:
                file_contexts.append(file_ctx)
            elif error:
                file_errors.append(error)
                logger.warning(f"Attached file error: {error}")

    # BUG-160 : rejouer les pièces jointes des tours précédents. Le composeur
    # vide sa liste après l'envoi, donc sans ce rappel la conversation perd le
    # document dès le message suivant et THÉRÈSE répond, à juste titre, qu'elle
    # n'a aucun moyen de le lire.
    for fp in await _pieces_jointes_recentes(
        conversation_id, session, deja_fournis=list(file_paths or [])
    ):
        file_ctx, error = await _get_file_context(
            fp, session, "analyse",
            scope=perimetre_fichiers, scope_id=perimetre_fichiers_id,
            contexte=contexte,
        )
        if file_ctx:
            file_contexts.append(file_ctx)
        elif error:
            logger.info("Pièce jointe d'un tour précédent non rejouée : %s", error)

    # Send file processing status if we had file commands or attached files
    if file_commands or file_paths:
        status_msg = f"Traitement de {len(file_commands) + len(file_paths or [])} fichier(s)..."
        if file_contexts:
            status_msg += f" {len(file_contexts)} charge(s)."
        if file_errors:
            status_msg += f" {len(file_errors)} erreur(s)."

        status_data = StreamChunk(
            type="status",
            content=status_msg,
            conversation_id=conversation_id,
        )
        yield f"data: {json.dumps(status_data.model_dump())}\n\n"

    # Combine memory and file contexts
    if file_contexts:
        # Revue Soso : borner le bloc ENTIER, sinon quatre documents rejoués à
        # 15 000 caractères chacun évincent l'historique de la conversation
        # sans que rien ne le signale.
        file_contexts, ecartes = borner_bloc_fichiers(file_contexts)
        if ecartes:
            logger.info("%d document(s) écarté(s) du contexte : plafond atteint", ecartes)
            file_contexts.append(
                f"[{ecartes} autre(s) document(s) de cette conversation n'ont pas pu "
                "être transmis : le volume total dépasse ce que le modèle peut "
                "recevoir. Dis-le à l'utilisateur s'il pose une question qui en dépend.]"
            )
        file_context_str = "\n\n".join(file_contexts)
        if memory_context:
            memory_context = f"{memory_context}\n\n{file_context_str}"
        else:
            memory_context = file_context_str

    # Directives inline déjà exécutées : le LLM doit le savoir (pas de re-création)
    if actions_context:
        memory_context = (
            f"{actions_context}\n\n{memory_context}" if memory_context else actions_context
        )

    context = llm_service.prepare_context(messages, memory_context=memory_context)

    # Injecter le system prompt du skill si skill_id fourni (Phase 1 v0.2.4)
    if skill_id:
        try:
            from app.services.skills import get_skills_registry
            registry = get_skills_registry()
            skill = registry.get(skill_id)
            if skill:
                skill_context = skill.get_system_prompt_addition()
                if skill_context:
                    context.system_prompt += f"\n\n{skill_context}"
                    logger.info(f"Injected skill system prompt for: {skill_id}")
            else:
                logger.warning(f"Skill not found: {skill_id}")
        except Exception as e:
            logger.warning(f"Failed to inject skill context for {skill_id}: {e}")

    # BUG-097 : disable_tools pour le mini-chat RFC (pas d'outils = pas de boucle)
    if disable_tools:
        tools: list[dict] = []
        logger.info("Tools disabled for this request (RFC mini-chat)")
    else:
        # Check if web search is enabled
        from app.models.entities import Preference
        result = await session.execute(
            select(Preference).where(Preference.key == "web_search_enabled")
        )
        web_search_pref = result.scalar_one_or_none()
        web_search_enabled = web_search_pref.value.lower() == "true" if web_search_pref else True

        # Get available tools: MCP tools + built-in web search + memory tools
        # Note: For Gemini, web search is handled via native grounding (not tool calling)
        tools = mcp_service.get_tools_for_llm() or []

        # Add memory tools (create_contact, create_project)
        tools = MEMORY_TOOLS + tools

        # Add workspace tools (email, calendar)
        tools = WORKSPACE_TOOLS + tools

        # Add web_search + browser tools for non-Gemini providers (if enabled).
        # BUG-141 : le browser n'est annoncé que si playwright est importable
        # (dépendance optionnelle e2e, absente de l'app packagée).
        if web_search_enabled and llm_service.config.provider.value != "gemini":
            tools = web_tools() + tools

        # Une action sensible déjà en attente ne doit pas être re-proposée au
        # modèle : sinon il la rappelle et une seconde carte s'affiche pour la
        # même action (cf. tests/test_chat_outils_deja_en_attente.py).
        tools = retirer_outils_deja_en_attente(tools, pending_confirmations)

    if tools:
        logger.info(f"Providing {len(tools)} tools to LLM")

        # Injecter dynamiquement les capacités dans le system prompt
        # uniquement quand des tools sont disponibles (pas pour les petits modèles sans tools)
        tool_names = [t.get("function", {}).get("name", "") for t in tools if t.get("type") == "function"]
        capabilities = "\n\n## Tes capacités (outils)\nTu disposes d'outils que tu DOIS utiliser quand c'est pertinent. Ne dis JAMAIS que tu ne peux pas accéder à internet ou que tu ne peux pas faire quelque chose si un outil le permet.\n"
        if "web_search" in tool_names:
            capabilities += "- **web_search** : Recherche sur internet. Utilise-le pour toute question sur l'actualité, analyser un site web, ou trouver des informations récentes.\n"
        if "browser_navigate" in tool_names:
            capabilities += "- **browser_navigate** : Navigue sur une page web, extrait le contenu, interagit (clic, formulaire, liens, screenshot). Utilise-le quand l'utilisateur demande d'aller sur un site précis.\n"
        # Une capacité par outil, chacune gardée par SON nom. Les paires
        # (« read_emails / send_email ») étaient annoncées sous une garde
        # unique : un outil retiré de la liste — parce qu'une action attend
        # confirmation — restait promis au modèle, qui le rappelait. Une
        # promesse qui survit au retrait de l'outil est ce qui produit la
        # seconde carte.
        if "create_contact" in tool_names:
            capabilities += "- **create_contact** : Creer un contact en memoire.\n"
        if "create_project" in tool_names:
            capabilities += "- **create_project** : Creer un projet en memoire.\n"
        if "read_emails" in tool_names:
            capabilities += "- **read_emails** : Lire les emails de l'utilisateur.\n"
        if "send_email" in tool_names:
            capabilities += "- **send_email** : Envoyer un email depuis le compte de l'utilisateur.\n"
        if "search_emails" in tool_names:
            capabilities += "- **search_emails** : Chercher dans les emails de l'utilisateur.\n"
        if "list_calendar_events" in tool_names:
            capabilities += "- **list_calendar_events** : Consulter les evenements du calendrier.\n"
        if "create_calendar_event" in tool_names:
            capabilities += "- **create_calendar_event** : Creer un evenement dans le calendrier.\n"
        if "search_invoices" in tool_names:
            capabilities += "- **search_invoices** : Retrouver une facture, un devis ou un avoir LOCAL par sa reference (ex: FACT-2026-001) ou par client. Utilise-le des qu'une facture ou un devis est mentionne, AU LIEU de dire que tu ne peux pas les chercher, et ne propose JAMAIS de recreer un document existant. Il ne couvre QUE la facturation : ne l'utilise pas pour des fichiers ou des documents indexes. L'envoi d'une facture par email est impossible dans l'application, y compris depuis la vue Facturation : n'utilise pas send_email pour ca et n'affirme jamais un envoi. Le parcours reel est : telecharger le PDF, l'envoyer soi-meme, puis marquer le document « Envoyee » a la main.\n"
        if "invoice_totals" in tool_names:
            capabilities += "- **invoice_totals** : Totalise ce qu'il RESTE A ENCAISSER (factures emises non payees, part en retard, avoirs deduits). Utilise-le pour toute question de tresorerie SANS nom ni reference : « combien il me reste a encaisser », « quelles factures ne sont pas payees », « combien on me doit ». N'utilise PAS search_invoices pour ca : il cherche UN document, il ne totalise rien. `encours_ttc` vaut null des qu'il y a plusieurs devises OU que le net devient negatif (zero est un chiffre valide, pas une absence) : il n'y a alors AUCUN total global, cite `encours_par_devise` montant par montant (le detail est dans `documents`, avoirs compris) sans en fabriquer un. Aucun champ nomme encours ou retard ne porte de negatif ; ce qui est du AU client est dans `du_au_client_par_devise` et ne se presente jamais comme une somme a encaisser.\n"
        if "search_files" in tool_names:
            capabilities += "- **search_files** : Retrouver les FICHIERS INDEXES consultables dans cette conversation (dossier synchronise d'un projet, fichiers de la memoire, pieces jointes). Utilise-le des que l'utilisateur parle de ses fichiers ou de ses documents indexes, AU LIEU de dire que tu ne peux pas les chercher. Il ne couvre PAS les factures et devis (c'est search_invoices) ni les documents rediges dans l'atelier Documents. Si la reponse contient 'hors_perimetre', des fichiers existent dans des projets que cette conversation ne consulte pas : dis-le et propose de rattacher la conversation au projet avec le selecteur en haut du chat.\n"
        if "read_file" in tool_names:
            capabilities += "- **read_file** : Lire le contenu d'un fichier indexe trouve par search_files, un seul par appel. Utilise-le des qu'on te demande ce qu'il y a DANS un fichier. S'il refuse, le fichier n'est pas consultable ici : ne devine JAMAIS son contenu.\n"
        if "read_contact" in tool_names:
            capabilities += "- **read_contact** : Lire une fiche de contact. Elle rend des COORDONNEES (des faits), un `etat_courant` (ce que l'application a enregistre, souvent vide) et des `traces` (ce qui a ete ecrit, date, sans garantie d'actualite). N'affirme QUE `etat_courant`. S'il est vide, dis-le et cite les traces avec leur date. Deux traces qui se contredisent : dis-le, ne tranche pas. Utilise-le AU LIEU d'inventer le contexte client.\n"
        if "generate_document" in tool_names:
            capabilities += "- **generate_document** : Genere un VRAI fichier Word (docx), PowerPoint (pptx) ou Excel (xlsx) telechargeable. Utilise-le DES que l'utilisateur demande de creer/generer un document : appelle l'outil avec tout le contenu, ne redige PAS le document en clair dans le chat et ne fabrique jamais de lien.\n"
        mcp_tools = [n for n in tool_names if n not in ("web_search", "browser_navigate", *MEMORY_TOOL_NAMES, *WORKSPACE_TOOL_NAMES)]
        if mcp_tools:
            capabilities += f"- **Outils externes** : {', '.join(mcp_tools[:10])}{'...' if len(mcp_tools) > 10 else ''}\n"
        context.system_prompt += capabilities

    # BUG-160 : le modèle n'a aucun outil qui lise un fichier local, et la
    # consigne « ne dis jamais que tu ne peux pas SI un outil le permet »
    # l'autorise donc, a contrario, à répondre « je ne peux pas ». Sa réponse
    # était techniquement juste et parfaitement désorientante. On lui dit donc
    # où sont les pièces jointes, et quoi répondre quand il n'en a qu'un extrait.
    if file_contexts:
        context.system_prompt += BLOC_PIECES_JOINTES

    full_content = ""
    # Confirmations des directives inline [action: ...] : émises en tête de
    # réponse (vérité d'exécution) et incluses dans le contenu sauvegardé.
    if preamble:
        full_content = preamble
        preamble_chunk = StreamChunk(
            type="text", content=preamble, conversation_id=conversation_id
        )
        yield f"data: {json.dumps(preamble_chunk.model_dump())}\n\n"
    tool_calls_collected: list[ToolCall] = []
    # 0.48 : content brut du tour (mode reasoning Mistral), a rejouer tel quel
    assistant_brut_collected: list[Any] | None = None
    max_tool_iterations = 5  # Prevent infinite tool loops
    # Usage réel (dette 14/06/2026) : accumulé sur TOUS les tours d'outils (un
    # tour = un appel API = son propre usage). "estimated" passe à True dès
    # qu'un tour n'a pas fourni l'usage réel (provider pas encore migré) - on
    # bascule alors sur l'estimation globale plutôt que de mélanger réel+estimé.
    usage_totals = {"input_tokens": 0, "output_tokens": 0, "estimated": False}
    # BUG-124 : résultats réels des outils exécutés (tous tours confondus). Filet
    # quand un modèle faible enchaîne des outils sans jamais produire de texte :
    # on remonte alors le résultat plutôt qu'une réponse vide et muette.
    tool_outcomes: list[tuple[str, str, bool]] = []

    try:
        # Stream from LLM with tool support
        async for event in llm_service.stream_response_with_tools(context, tools if tools else None):
            if event.type == "text" and event.content:
                # Record first token latency (US-PERF-01)
                if not first_token_recorded:
                    stream_metrics.record_first_token()
                    first_token_recorded = True
                stream_metrics.record_token()

                full_content += event.content
                data = StreamChunk(
                    type="text",
                    content=event.content,
                    conversation_id=conversation_id,
                )
                yield f"data: {json.dumps(data.model_dump())}\n\n"

            elif event.type == "tool_call" and event.tool_call:
                tool_calls_collected.append(event.tool_call)
                if event.assistant_content_brut is not None:
                    assistant_brut_collected = event.assistant_content_brut

            elif event.type == "done":
                if event.input_tokens is not None and event.output_tokens is not None:
                    usage_totals["input_tokens"] += event.input_tokens
                    usage_totals["output_tokens"] += event.output_tokens
                else:
                    usage_totals["estimated"] = True

                # Check if we have tool calls to execute
                if tool_calls_collected and event.stop_reason in ("tool_calls", "tool_use"):
                    # Execute tools and continue
                    async for continued_event in _execute_tools_and_continue(
                        llm_service,
                        mcp_service,
                        context,
                        full_content,
                        tool_calls_collected,
                        tools,
                        conversation_id,
                        max_tool_iterations,
                        session=session,
                        usage_totals=usage_totals,
                        tool_outcomes=tool_outcomes,
                        contexte=contexte,
                        assistant_content_brut=assistant_brut_collected,
                    ):
                        if continued_event.startswith("data:"):
                            # Parse the content to accumulate full response
                            try:
                                event_data = json.loads(continued_event[6:].strip())
                                if event_data.get("type") == "text":
                                    full_content += event_data.get("content", "")
                            except json.JSONDecodeError:
                                pass
                        yield continued_event

            elif event.type == "error":
                error_content = event.content or "Erreur inattendue du fournisseur LLM"
                error_data = StreamChunk(
                    type="error",
                    content=error_content,
                    conversation_id=conversation_id,
                )
                yield f"data: {json.dumps(error_data.model_dump())}\n\n"
                # Persister le message d'erreur en base (BUG-041) pour qu'il ne
                # disparaisse pas au rechargement de la conversation
                try:
                    saved_content = full_content if full_content else f"⚠️ {error_content}"
                    err_msg = Message(
                        conversation_id=conversation_id,
                        role="assistant",
                        content=saved_content,
                        model=llm_service.config.model,
                    )
                    session.add(err_msg)
                    await session.commit()
                except Exception as db_err:
                    logger.warning(f"Impossible de persister le message d'erreur: {db_err}")
                return

    except (GeneratorExit, asyncio.CancelledError):
        # 0.46 : l'annulation arrive par la FERMETURE du générateur (wrapper
        # aclose, client parti) OU par l'annulation du __anext__ en vol
        # (fournisseur bloqué, revue jalon F4) - la garde d'écriture plus bas
        # n'est jamais atteinte. Le texte déjà produit survit ici ; aucun
        # effet (skill, outil) n'est lancé.
        await _persister_message_partiel(conversation_id, full_content, llm_service)
        raise
    except Exception as e:
        logger.error(f"LLM streaming error: {e}", exc_info=True)
        # Revue 0.48 (F4) : jamais str(e) brut dans un chunk SSE destiné à
        # l'écran - le détail vit dans les logs ci-dessus.
        message_erreur = message_pour_ecran(e, ou="pendant la génération")
        error_data = StreamChunk(
            type="error",
            content=message_erreur,
            conversation_id=conversation_id,
        )
        yield f"data: {json.dumps(error_data.model_dump())}\n\n"
        # Persister le message d'erreur en base (BUG-041)
        try:
            err_msg = Message(
                conversation_id=conversation_id,
                role="assistant",
                content=full_content or f"⚠️ {message_erreur}",
                model=llm_service.config.model if llm_service else "unknown",
            )
            session.add(err_msg)
            await session.commit()
        except Exception as db_err:
            logger.warning(f"Impossible de persister le message d'erreur: {db_err}")
        return

    # BUG-124 : un modèle faible peut enchaîner des outils (ex. read_emails) sans
    # jamais produire de texte -> réponse vide et muette côté utilisateur
    # (« aucune réaction »). Filet : si aucun texte n'a été généré mais que des
    # outils ont tourné, on remonte leur résultat réel plutôt qu'une bulle vide.
    if not full_content.strip():
        fallback = _fallback_from_tool_outcomes(tool_outcomes)
        if fallback:
            logger.info(
                "Réponse vide après %d outil(s) : repli sur le résultat réel (BUG-124)",
                len(tool_outcomes),
            )
            full_content = fallback
            fallback_chunk = StreamChunk(
                type="text", content=fallback, conversation_id=conversation_id
            )
            yield f"data: {json.dumps(fallback_chunk.model_dump())}\n\n"

    # Save complete assistant message
    assistant_message = Message(
        conversation_id=conversation_id,
        role="assistant",
        content=full_content,
        model=llm_service.config.model,
        provider=llm_service.config.provider.value,
    )
    # Track token usage and costs (US-ESC-02, US-ESC-04)
    #
    # Contre-vérification Soso (finding 3) : ce suivi précède DÉLIBÉRÉMENT la
    # garde d'annulation. Les tokens ont réellement été consommés chez le
    # fournisseur, que l'utilisateur ait annulé ou non — les escamoter
    # fausserait le coût affiché dans Réglages.
    token_tracker = get_token_tracker()

    # Usage réel accumulé sur tous les tours d'outils (dette 14/06/2026), sinon
    # estimation ~1 mot = 2 tokens en filet (providers pas encore migrés).
    if usage_totals["estimated"] or usage_totals["input_tokens"] == 0:
        input_tokens = len(user_message.split()) * 2
        output_tokens = len(full_content.split()) * 2
    else:
        input_tokens = usage_totals["input_tokens"]
        output_tokens = usage_totals["output_tokens"]

    usage_record = token_tracker.record_usage(
        conversation_id=conversation_id,
        model=llm_service.config.model,
        provider=llm_service.config.provider.value,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
    )

    # Finding 3 de la revue Soso : le drapeau n'était consulté qu'entre deux
    # morceaux, jamais avant les effets PERSISTANTS. Un `__anext__()` pouvait
    # committer la réponse — ou déclencher l'auto-exécution d'un skill, qui
    # ÉCRIT UN FICHIER sur le disque — alors que l'utilisateur venait de cliquer
    # sur Arrêter. Il retrouvait ensuite une réponse qu'il croyait annulée, ou
    # un fichier orphelin sans carte pour l'ouvrir.
    #
    # Le sondage d'annulation a un pas de 50 ms : la course est réelle. La garde
    # est donc reposée ICI, juste avant le premier effet durable.
    if _annulation_observee():
        # 0.46 (design V2.1) : le TEXTE déjà produit survit - l'utilisateur le
        # voit à l'écran, le faire disparaître au rechargement était un
        # mensonge inverse. Les EFFETS (skill qui écrit un fichier, outils),
        # eux, restent interdits.
        logger.info(
            "Annulation demandée : réponse partielle conservée, aucun effet produit"
        )
        await _persister_message_partiel(
            conversation_id, full_content, llm_service
        )
        return

    session.add(assistant_message)
    await session.commit()

    # Finish performance tracking (US-PERF-01)
    perf_monitor.finish_stream(conversation_id)

    # Detect uncertainty in response (US-ESC-01)
    uncertainty = detect_uncertainty(full_content)

    # BUG-093 : Exécution automatique du skill si détecté.
    # IMPORTANT (fichiers générés visibles, 10/07/2026) : ce bloc tourne AVANT
    # l'événement done - le client arrête la lecture du stream sur done
    # (chat.ts), donc tout événement émis après n'atteint jamais l'UI en
    # direct (le testeur découvrait ses fichiers par hasard au rechargement).
    if skill_id and not (full_content or "").strip():
        # Trou couvert (revue design actions) : un skill était attendu mais le
        # modèle n'a produit AUCUN contenu - avant, l'utilisateur ne recevait
        # ni fichier ni explication.
        yield _skill_file_error_event(
            conversation_id, skill_id,
            "le modèle n'a produit aucun contenu (réessaie, ou change de modèle)",
        )
    # BUG-136 : une carte par fichier créé via l'outil generate_document
    # pendant ce tour (chronologiquement AVANT l'éventuel auto-exec).
    skill_files_payloads: list[dict[str, Any]] = []
    for tool_file in drain_generated_files():
        skill_files_payloads.append(tool_file)
        tool_file_event = {
            "type": "skill_file",
            "content": f"Fichier {tool_file.get('file_name')} généré",
            "conversation_id": conversation_id,
            "skill_file": tool_file,
        }
        yield f"data: {json.dumps(tool_file_event)}\n\n"

    if skill_id and full_content:
        try:
            from app.services.skills import get_skills_registry
            registry = get_skills_registry()
            skill = registry.get(skill_id)
            if skill is None:
                # Trou couvert (revue design) : skill introuvable au registre.
                yield _skill_file_error_event(
                    conversation_id, skill_id, "compétence de génération introuvable"
                )
            elif skill.output_type.value == "file":
                logger.info(f"Auto-exécution du skill {skill_id} après streaming")
                result = await registry.execute(
                    skill_id,
                    SkillExecuteRequest(prompt=user_message, title=None),
                    full_content,
                )
                if result.success:
                    skill_file_payload = {
                        "skill_id": skill_id,
                        "file_id": result.file_id,
                        "file_name": result.file_name,
                        "file_size": result.file_size,
                        "download_url": result.download_url,
                        "format": skill.output_format.value,
                        # Dossier local des sorties, pour « Afficher dans le
                        # dossier » côté desktop.
                        "local_dir": str(registry.output_dir),
                    }
                    skill_file_data = {
                        "type": "skill_file",
                        "content": f"Fichier {result.file_name} généré",
                        "conversation_id": conversation_id,
                        "skill_file": skill_file_payload,
                    }
                    yield f"data: {json.dumps(skill_file_data)}\n\n"
                    skill_files_payloads.append(skill_file_payload)
                    logger.info(f"Skill {skill_id} exécuté : {result.file_name}")
                else:
                    # L'échec doit être VISIBLE, pas seulement loggué.
                    logger.warning(f"Échec auto-exécution skill {skill_id}: {result.error}")
                    yield _skill_file_error_event(conversation_id, skill_id, result.error)
        except Exception as e:
            logger.warning(f"Erreur auto-exécution skill {skill_id}: {e}")
            yield _skill_file_error_event(conversation_id, skill_id, str(e))

    # BUG-130/136 : persister LES fichiers du tour sur le message pour les
    # restaurer au rechargement (les fichiers survivent sur disque, cf
    # outputs/ + download par id). Le contenu du message reste le texte ;
    # le frontend masque le code quand des fichiers sont présents.
    if skill_files_payloads:
        assistant_message.extra_data = json.dumps(
            {"skill_files": skill_files_payloads}
        )
        await session.commit()

    # Send done event with usage info
    done_data = StreamChunk(
        type="done",
        content="",
        conversation_id=conversation_id,
        message_id=assistant_message.id,
    )
    done_dict = done_data.model_dump()
    done_dict["provider"] = llm_service.config.provider.value
    done_dict["usage"] = {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cost_eur": usage_record.cost_eur,
        "model": llm_service.config.model,
        "provider": llm_service.config.provider.value,
    }
    done_dict["uncertainty"] = uncertainty
    yield f"data: {json.dumps(done_dict)}\n\n"

    # Fire-and-forget entity extraction (PERF-001)
    # L'extraction continue en arrière-plan sans bloquer le stream SSE
    # NOTE: On ne passe PAS la session FastAPI car elle sera fermée après la requête.
    # La background task crée sa propre session via get_session_context().
    asyncio.create_task(
        _extract_entities_background(
            user_message=user_message,
            conversation_id=conversation_id,
            message_id=assistant_message.id,
        )
    )


def _skill_file_error_event(
    conversation_id: str, skill_id: str, error: str | None
) -> str:
    """Événement SSE d'échec de génération de fichier (visible dans l'UI).

    Avant le 10/07/2026 un échec d'auto-exécution finissait uniquement dans
    les logs : l'utilisateur voyait la réponse texte mais aucun fichier, sans
    explication. Émis AVANT done (le client coupe la lecture sur done)."""
    payload = {
        "type": "skill_file_error",
        "content": (
            f"La génération du fichier a échoué : {error or 'erreur inconnue'}. "
            "Tu peux relancer la demande."
        ),
        "conversation_id": conversation_id,
        "skill_id": skill_id,
    }
    return f"data: {json.dumps(payload)}\n\n"


def _fallback_from_tool_outcomes(
    tool_outcomes: list[tuple[str, str, bool]],
) -> str | None:
    """Message de repli quand le modèle n'a produit aucun texte (BUG-124).

    Remonte le dernier résultat d'outil exploitable (succès, non vide, pas une
    simple mise en attente de confirmation) pour ne pas laisser l'utilisateur
    devant une réponse vide et muette. Si des outils ont tourné mais qu'aucun
    résultat n'est exploitable, on renvoie au moins un message honnête plutôt
    qu'une bulle vide. None s'il n'y a eu aucun outil (l'appelant garde alors
    son comportement d'origine)."""
    for _name, result, is_error in reversed(tool_outcomes):
        if is_error:
            continue
        text = (result or "").strip()
        if not text or "en attente de confirmation" in text:
            continue
        return (
            "Je n'ai pas réussi à rédiger une réponse, mais voici ce que j'ai "
            f"trouvé en consultant tes données :\n\n{text}"
        )

    if tool_outcomes:
        return (
            "Je n'ai pas réussi à formuler de réponse à partir des outils "
            "consultés. Reformule ta demande ou réessaie."
        )
    return None


async def _execute_tools_and_continue(
    llm_service: LLMService,
    mcp_service,
    context: ContextWindow,
    assistant_content: str,
    tool_calls: list[ToolCall],
    tools: list[dict],
    conversation_id: str,
    remaining_iterations: int,
    session: AsyncSession | None = None,
    prior_turns: list[ToolTurn] | None = None,
    usage_totals: dict | None = None,
    tool_outcomes: list[tuple[str, str, bool]] | None = None,
    contexte: ContexteExecution | None = None,
    assistant_content_brut: list[Any] | None = None,
) -> AsyncGenerator[str, None]:
    """
    Execute MCP tools and continue the conversation.

    Handles recursive tool calling up to max_iterations. prior_turns porte
    les tours d'outils déjà joués dans CETTE réponse : ils sont rejoués dans
    le contexte de continuation, sinon le modèle ne voit jamais les résultats
    précédents, re-demande le même outil en boucle puis invente une
    explication d'échec (bug lcjp 11/06/2026).

    usage_totals : accumulateur mutable partagé avec l'appelant (dette
    14/06/2026, usage réel plutôt qu'estimé) - un tour d'outils = un appel API
    = son propre usage, à sommer sur toute la récursion.

    tool_outcomes : accumulateur mutable (tool_name, résultat, is_error) de tous
    les outils exécutés sur la récursion (BUG-124). Sert de filet quand un modèle
    faible enchaîne des outils sans jamais produire de texte : l'appelant peut
    alors remonter le résultat réel (ex. les emails lus) plutôt qu'une réponse
    vide.
    """
    if remaining_iterations <= 0:
        logger.warning("Max tool iterations reached, stopping")
        return

    # Send status about tool execution
    tool_names = [tc.name for tc in tool_calls]
    status_data = StreamChunk(
        type="status",
        content=f"Execution des outils: {', '.join(tool_names)}...",
        conversation_id=conversation_id,
    )
    yield f"data: {json.dumps(status_data.model_dump())}\n\n"

    # Execute each tool call
    tool_results: list[ToolResult] = []

    # Chantier A (vérité d'exécution) : plafonner les créations d'entités par tour
    # (anti rafale de noms hallucinés), en plus de la déduplication par nom.
    from app.services.execution_truth import enforce_create_cap, summarize_executions
    allowed_calls, blocked_calls = enforce_create_cap(tool_calls)
    exec_records: list[tuple[str, str, bool]] = []
    # BUG-121 : une fois une action sensible mise en attente de confirmation, on
    # ne relance pas la chaîne d'outils (voir plus bas). Sinon le modèle - surtout
    # les modèles faibles - re-émet send_email en boucle et empile plusieurs
    # cartes de confirmation quasi identiques.
    sensitive_pending = False
    # D1 : `sensitive_pending` ne protège que la récursion. Dans CE tour, un
    # modèle qui répète send_email empilait une carte par appel pour un seul
    # envoi. On mémorise l'identité des actions déjà mises en attente ; une
    # empreinte incalculable (None) laisse toujours passer la carte.
    empreintes_en_attente: set[str] = set()

    for tc in allowed_calls:
        # Finding 3, troisième passe de revue : la boucle d'outils ignorait
        # complètement l'annulation. Elle émet d'abord un statut, puis exécute
        # — et ces outils ne sont pas anodins : ils créent des contacts et des
        # projets (commit SQLite et Qdrant), écrivent des documents sur le
        # disque, ou appellent un outil MCP arbitraire. L'utilisateur cliquait
        # sur Arrêter, recevait bien « cancelled », et retrouvait quand même un
        # fichier ou une entité créés après coup.
        #
        # La garde est en TÊTE de boucle : un seul endroit couvre tous les
        # chemins d'exécution (web, navigateur, mémoire, workspace, MCP).
        if (
            contexte.annulation_observee()
            if contexte is not None
            else _is_cancelled(conversation_id)
        ):
            logger.info("Annulation demandée : les outils restants ne sont pas exécutés")
            return

        # US-002 : les outils sensibles (envoi de mail) ne s'exécutent jamais
        # automatiquement sur décision du LLM. On met l'action en attente et on
        # demande validation à l'utilisateur ; l'exécution réelle a lieu via
        # POST /api/chat/confirm-tool une fois l'action confirmée. Le gate est
        # AVANT tout log d'exécution : BUG-121 a été mal lu parce que le log
        # "Executing tool: send_email" laissait croire à un envoi réel alors que
        # l'action était seulement mise en attente.
        if requires_confirmation(tc.name):
            pending_arguments = canoniser_arguments(tc.name, dict(tc.arguments))
            if tc.name.split("__", 1)[-1] == "create_calendar_event" and session is not None:
                from app.services.workspace_tools import (
                    get_calendar_confirmation_destination,
                )

                pending_arguments["_confirmation_destination"] = (
                    await get_calendar_confirmation_destination(session)
                )
            logger.info(
                "Outil sensible %s mis en attente de confirmation utilisateur "
                "(NON exécuté), clés d'arguments : %s",
                tc.name,
                sorted(pending_arguments),
            )
            sensitive_pending = True
            empreinte = empreinte_action(tc.name, pending_arguments)
            if empreinte is not None and empreinte in empreintes_en_attente:
                logger.info(
                    f"{tc.name} déjà en attente de confirmation dans ce tour : "
                    "pas de seconde carte pour la même action."
                )
                tool_results.append(ToolResult(
                    tool_call_id=tc.id,
                    result=(
                        "Cette action exacte attend DÉJÀ la validation de "
                        "l'utilisateur. Ne la redemande pas."
                    ),
                    is_error=False,
                ))
                exec_records.append(
                    (tc.name, "déjà en attente de confirmation utilisateur", False)
                )
                continue
            if empreinte is not None:
                empreintes_en_attente.add(empreinte)
            confirmation_id = register_pending(
                tc.name, pending_arguments, conversation_id=conversation_id
            )
            confirm_chunk = StreamChunk(
                type="confirmation_required",
                conversation_id=conversation_id,
                tool_name=tc.name,
                confirmation={
                    "confirmation_id": confirmation_id,
                    "tool_name": tc.name,
                    "arguments": pending_arguments,
                },
            )
            yield f"data: {json.dumps(confirm_chunk.model_dump())}\n\n"
            tool_results.append(ToolResult(
                tool_call_id=tc.id,
                result=(
                    "Action préparée et en attente de validation de l'utilisateur. "
                    "NE PAS la considérer comme exécutée : l'utilisateur doit confirmer."
                ),
                is_error=False,
            ))
            exec_records.append((tc.name, "en attente de confirmation utilisateur", False))
            continue

        logger.info(
            "Executing tool: %s, clés d'arguments : %s",
            tc.name,
            sorted(tc.arguments),
        )

        # Execute based on tool type
        if tc.name == "web_search":
            # Built-in web search tool
            import time
            start_time = time.time()
            try:
                search_result = await execute_web_search(tc.arguments)
                execution_time = (time.time() - start_time) * 1000

                # Create result object compatible with MCP format
                class WebSearchResult:
                    def __init__(self, result_text: str, exec_time: float):
                        self.success = True
                        self.result = result_text
                        self.error = None
                        self.execution_time_ms = exec_time

                result = WebSearchResult(search_result, execution_time)
            except Exception as e:
                execution_time = (time.time() - start_time) * 1000

                class WebSearchError:
                    def __init__(self, error_msg: str, exec_time: float):
                        self.success = False
                        self.result = None
                        self.error = error_msg
                        self.execution_time_ms = exec_time

                result = WebSearchError(str(e), execution_time)
        elif tc.name == "browser_navigate":
            # Built-in browser automation tool
            import time
            start_time = time.time()
            try:
                browser_result = await execute_browser_action(tc.arguments)
                execution_time = (time.time() - start_time) * 1000

                class BrowserResult:
                    def __init__(self, result_text: str, exec_time: float):
                        self.success = True
                        self.result = result_text
                        self.error = None
                        self.execution_time_ms = exec_time

                result = BrowserResult(browser_result, execution_time)
            except Exception as e:
                execution_time = (time.time() - start_time) * 1000

                class BrowserError:
                    def __init__(self, error_msg: str, exec_time: float):
                        self.success = False
                        self.result = None
                        self.error = error_msg
                        self.execution_time_ms = exec_time

                result = BrowserError(str(e), execution_time)
        elif tc.name in MEMORY_TOOL_NAMES:
            # Built-in memory tools (create_contact, create_project)
            import time
            start_time = time.time()
            try:
                if session is None:
                    raise RuntimeError("Database session not available for memory tools")
                # 0.43 : les outils mémoire respectent la cloison de la conversation.
                # Sans ce périmètre, `read_contact` rendait coordonnées et notes
                # d'un contact d'un autre projet.
                perimetre, perimetre_id = await _perimetre_de_conversation(
                    conversation_id, session
                )
                tool_result_str = await execute_memory_tool(
                    tc.name, tc.arguments, session,
                    scope=perimetre, scope_id=perimetre_id,
                    conversation_id=conversation_id,
                    contexte=contexte,
                )
                execution_time = (time.time() - start_time) * 1000

                class MemoryToolResult:
                    def __init__(self, result_text: str, exec_time: float):
                        self.success = True
                        self.result = result_text
                        self.error = None
                        self.execution_time_ms = exec_time

                result = MemoryToolResult(tool_result_str, execution_time)
            except Exception as e:
                execution_time = (time.time() - start_time) * 1000

                class MemoryToolError:
                    def __init__(self, error_msg: str, exec_time: float):
                        self.success = False
                        self.result = None
                        self.error = error_msg
                        self.execution_time_ms = exec_time

                result = MemoryToolError(str(e), execution_time)
        elif tc.name in WORKSPACE_TOOL_NAMES:
            # Built-in workspace tools (email, calendar)
            import time
            start_time = time.time()
            try:
                if session is None:
                    raise RuntimeError("Database session not available for workspace tools")
                tool_result_str = await execute_workspace_tool(
                    tc.name, tc.arguments, session, contexte=contexte,
                    # 0.56 : le PERIMETRE descend enfin jusqu'aux outils metier.
                    # Il etait calcule pour la memoire et jamais transmis ici :
                    # la cloison n'etait pas contournee, elle n'etait pas
                    # exprimable (campagne cinq personas, constat d'Ines).
                    conversation_id=conversation_id,
                )
                execution_time = (time.time() - start_time) * 1000

                class WorkspaceToolResult:
                    def __init__(self, result_text: str, exec_time: float):
                        self.success = True
                        self.result = result_text
                        self.error = None
                        self.execution_time_ms = exec_time

                result = WorkspaceToolResult(tool_result_str, execution_time)
            except Exception as e:
                execution_time = (time.time() - start_time) * 1000

                class WorkspaceToolError:
                    def __init__(self, error_msg: str, exec_time: float):
                        self.success = False
                        self.result = None
                        self.error = error_msg
                        self.execution_time_ms = exec_time

                result = WorkspaceToolError(str(e), execution_time)
        else:
            # Execute via MCP service
            result = await mcp_service.execute_tool_call(tc.name, tc.arguments)

        # Send tool result status
        if result.success:
            result_preview = str(result.result)[:100]
            if len(str(result.result)) > 100:
                result_preview += "..."

            tool_status = StreamChunk(
                type="tool_result",
                content=f"[{tc.name}] OK ({result.execution_time_ms:.0f}ms): {result_preview}",
                conversation_id=conversation_id,
            )
        else:
            tool_status = StreamChunk(
                type="tool_result",
                content=f"[{tc.name}] Erreur: {result.error}",
                conversation_id=conversation_id,
            )

        yield f"data: {json.dumps(tool_status.model_dump())}\n\n"

        # Build ToolResult for LLM
        tool_results.append(ToolResult(
            tool_call_id=tc.id,
            result=result.result if result.success else f"Error: {result.error}",
            is_error=not result.success,
        ))
        exec_records.append(
            (tc.name, result.result if result.success else f"Error: {result.error}", not result.success)
        )

    # Créations bloquées par le cap : erreur honnête pour le LLM ET l'utilisateur
    for tc in blocked_calls:
        cap_msg = (
            "Création bloquée : limite de créations par tour atteinte "
            "(garde-fou anti création en masse). Confirme si tu veux vraiment en créer davantage."
        )
        tool_results.append(ToolResult(tool_call_id=tc.id, result=f"Error: {cap_msg}", is_error=True))
        exec_records.append((tc.name, f"Error: {cap_msg}", True))
        blocked_status = StreamChunk(
            type="tool_result",
            content=f"[{tc.name}] Bloqué : limite de créations par tour atteinte",
            conversation_id=conversation_id,
        )
        yield f"data: {json.dumps(blocked_status.model_dump())}\n\n"

    # BUG-124 : mémoriser les résultats d'outils pour l'appelant, comme filet si
    # le modèle enchaîne des outils sans jamais produire de texte final.
    if tool_outcomes is not None:
        tool_outcomes.extend(exec_records)

    # Résumé DÉTERMINISTE de ce qui a réellement été créé (indépendant de la prose du LLM)
    recap = summarize_executions(exec_records)
    if recap:
        recap_chunk = StreamChunk(
            type="status",
            content=recap,
            conversation_id=conversation_id,
        )
        yield f"data: {json.dumps(recap_chunk.model_dump())}\n\n"

    # 0.46 : la garde POST-outils. Celle en tête de boucle couvre chaque
    # outil suivant ; celle-ci empêche de relancer un TOUR DE MODÈLE entier
    # alors que l'utilisateur vient d'arrêter pendant le dernier outil.
    if (
        contexte.annulation_observee()
        if contexte is not None
        else _is_cancelled(conversation_id)
    ):
        logger.info("Annulation demandée : pas de nouveau tour après les outils")
        return

    # Continue conversation with tool results
    new_tool_calls: list[ToolCall] = []
    new_assistant_brut: list[Any] | None = None
    continued_content = ""

    async for event in llm_service.continue_with_tool_results(
        context,
        assistant_content,
        tool_calls,
        tool_results,
        tools,
        prior_turns=prior_turns,
        # 0.48 : content BRUT du tour courant (liste de chunks reasoning
        # Mistral), rejoue tel quel dans le message assistant a tool_calls
        assistant_content_brut=assistant_content_brut,
    ):
        if event.type == "text" and event.content:
            continued_content += event.content
            data = StreamChunk(
                type="text",
                content=event.content,
                conversation_id=conversation_id,
            )
            yield f"data: {json.dumps(data.model_dump())}\n\n"

        elif event.type == "tool_call" and event.tool_call:
            new_tool_calls.append(event.tool_call)
            if event.assistant_content_brut is not None:
                new_assistant_brut = event.assistant_content_brut

        elif event.type == "done":
            if usage_totals is not None:
                if event.input_tokens is not None and event.output_tokens is not None:
                    usage_totals["input_tokens"] += event.input_tokens
                    usage_totals["output_tokens"] += event.output_tokens
                else:
                    usage_totals["estimated"] = True

            # Check if more tools need to be called
            # BUG-121 : si une action sensible attend confirmation, on NE relance
            # PAS la chaîne d'outils. Le modèle a déjà sa carte de confirmation ;
            # continuer laisserait un modèle faible re-émettre send_email en boucle
            # (4 cartes quasi identiques observées, args hallucinés body/content).
            if (
                new_tool_calls
                and event.stop_reason in ("tool_calls", "tool_use")
                and not sensitive_pending
            ):
                # Recursive call for chained tools
                async for nested_event in _execute_tools_and_continue(
                    llm_service,
                    mcp_service,
                    context,
                    continued_content,
                    new_tool_calls,
                    tools,
                    conversation_id,
                    remaining_iterations - 1,
                    session=session,
                    usage_totals=usage_totals,
                    tool_outcomes=tool_outcomes,
                    contexte=contexte,
                    # Le tour qui vient de se jouer rejoint l'historique :
                    # le prochain continue_with_tool_results rejouera TOUS
                    # les tours dans l'ordre avant le nouveau.
                    assistant_content_brut=new_assistant_brut,
                    prior_turns=[
                        *(prior_turns or []),
                        ToolTurn(
                            assistant_content=assistant_content,
                            tool_calls=tool_calls,
                            # Résultats tronqués au replay (budget contexte :
                            # 5 itérations max x N outils, les résultats
                            # complets ne servent qu'au tour qui les consomme)
                            tool_results=[
                                ToolResult(
                                    tool_call_id=tr.tool_call_id,
                                    result=(
                                        tr.result[:4000] + " [...tronqué]"
                                        if isinstance(tr.result, str) and len(tr.result) > 4000
                                        else tr.result
                                    ),
                                    is_error=tr.is_error,
                                )
                                for tr in tool_results
                            ],
                            assistant_content_brut=assistant_content_brut,
                        ),
                    ],
                ):
                    yield nested_event

        elif event.type == "error":
            error_data = StreamChunk(
                type="error",
                content=event.content or "Tool continuation error",
                conversation_id=conversation_id,
            )
            yield f"data: {json.dumps(error_data.model_dump())}\n\n"


# ============================================================
# US-002 - Confirmation d'actions sensibles
# ============================================================


class ConfirmToolRequest(BaseModel):
    """Validation (ou annulation) d'une action sensible mise en attente."""

    confirmation_id: str
    approved: bool


@router.post("/confirm-tool")
async def confirm_tool(
    request: ConfirmToolRequest,
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Exécute (ou annule) une action sensible (ex. send_email) après validation
    explicite de l'utilisateur. L'action a été mise en attente par la boucle
    d'outils, qui ne l'exécute jamais automatiquement (US-002)."""
    action = pop_pending(request.confirmation_id)
    if action is None:
        raise HTTPException(
            status_code=404, detail="Action introuvable ou déjà traitée"
        )

    tool_name, arguments, conversation_id = action
    if not request.approved:
        return {"status": "cancelled", "tool_name": tool_name}

    from app.services.workspace_tools import (
        drain_generated_files,
        start_generated_files_collection,
    )

    start_generated_files_collection()

    # Passe 4 : le portillon couvre désormais web_search, les outils
    # mémoire et n'importe quel MCP, plus seulement send_email / agenda.
    # Recopier le dispatch de la boucle : sans ça, l'utilisateur confirme
    # et execute_workspace_tool rend « Outil inconnu » : la carte ment.
    if "__" in tool_name:
        # BUG-121 : '{server_id}__{tool}' n'existe pas dans les workspace
        # tools. L'exécution confirmée doit suivre le service MCP.
        mcp_service = get_mcp_service()
        mcp_result = await mcp_service.execute_tool_call(tool_name, arguments)
        result = (
            mcp_result.result
            if mcp_result.success
            else f"Erreur lors de l'envoi : {mcp_result.error}"
        )
    elif tool_name == "web_search":
        result = await execute_web_search(arguments)
    elif tool_name == "browser_navigate":
        result = await execute_browser_action(arguments)
    elif tool_name in MEMORY_TOOL_NAMES:
        perimetre, perimetre_id = await _perimetre_de_conversation(
            conversation_id, session
        )
        result = await execute_memory_tool(
            tool_name,
            arguments,
            session,
            scope=perimetre,
            scope_id=perimetre_id,
            conversation_id=conversation_id,
        )
    else:
        result = await execute_workspace_tool(
            tool_name, arguments, session, conversation_id=conversation_id
        )
    # generate_document n'écrit plus pendant le flux : la carte a coupé
    # l'exécution. Sans collecteur ici, record_generated_file est un no-op
    # et l'utilisateur confirme un document qu'il ne peut pas télécharger
    # (même trou que BUG-136, déplacé après la confirmation).
    fichiers = drain_generated_files()
    payload: dict[str, Any] = {
        "status": "executed",
        "tool_name": tool_name,
        "result": result,
    }
    if fichiers:
        payload["skill_files"] = fichiers
    return payload


# ============================================================
# Conversation Endpoints
# ============================================================


class ConversationRename(BaseModel):
    title: str


@router.get("/conversations", response_model=list[ConversationResponse])
async def list_conversations(
    limit: int = 50,
    offset: int = 0,
    session: AsyncSession = Depends(get_session),
):
    """
    List all conversations with message counts.

    Sprint 2 - PERF-2.9: Use COUNT(*) with GROUP BY instead of N+1 queries.
    Before: 1 query for conversations + N queries for message counts
    After: 1 query with LEFT JOIN and GROUP BY
    """
    # Single query with COUNT (Sprint 2 - PERF-2.9)
    stmt = (
        select(
            Conversation,
            func.count(Message.id).label("message_count")
        )
        .outerjoin(Message, Message.conversation_id == Conversation.id)
        .group_by(Conversation.id)
        .order_by(Conversation.updated_at.desc())
        .offset(offset)
        .limit(limit)
    )

    result = await session.execute(stmt)
    rows = result.all()

    return [
        ConversationResponse(
            id=conv.id,
            title=conv.title,
            summary=conv.summary,
            message_count=msg_count,
            created_at=conv.created_at,
            updated_at=conv.updated_at,
            project_id=conv.project_id,
            memory_scope=conv.memory_scope,
        )
        for conv, msg_count in rows
    ]


@router.post("/conversations", response_model=ConversationResponse)
async def create_conversation(
    request: ConversationCreate,
    session: AsyncSession = Depends(get_session),
):
    """Create a new conversation."""
    conversation = Conversation(title=request.title)
    session.add(conversation)
    await session.commit()
    await session.refresh(conversation)

    # Index for fast search (US-PERF-04)
    search_index = get_search_index()
    search_index.index_conversation(conversation.id, conversation.title)

    return ConversationResponse(
        id=conversation.id,
        title=conversation.title,
        summary=conversation.summary,
        message_count=0,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        project_id=conversation.project_id,
        memory_scope=conversation.memory_scope,
    )


@router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: str,
    session: AsyncSession = Depends(get_session),
):
    """Get a specific conversation."""
    result = await session.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    )
    conversation = result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Count messages
    count_result = await session.execute(
        select(func.count()).select_from(Message).where(Message.conversation_id == conversation.id)
    )
    message_count = count_result.scalar() or 0

    return ConversationResponse(
        id=conversation.id,
        title=conversation.title,
        summary=conversation.summary,
        message_count=message_count,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        project_id=conversation.project_id,
        memory_scope=conversation.memory_scope,
    )


@router.patch("/conversations/{conversation_id}", response_model=ConversationResponse)
async def rename_conversation(
    conversation_id: str,
    request: ConversationRename,
    session: AsyncSession = Depends(get_session),
) -> ConversationResponse:
    """Renomme durablement une conversation sans modifier ses messages."""
    from datetime import UTC, datetime

    title = request.title.strip()
    if not title:
        raise HTTPException(status_code=400, detail="Le titre ne peut pas être vide")
    if len(title) > 120:
        raise HTTPException(status_code=400, detail="Le titre est limité à 120 caractères")

    result = await session.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    )
    conversation = result.scalar_one_or_none()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    conversation.title = title
    conversation.updated_at = datetime.now(UTC)
    session.add(conversation)
    await session.commit()
    await session.refresh(conversation)
    get_search_index().index_conversation(conversation.id, title)

    count_result = await session.execute(
        select(func.count()).select_from(Message).where(Message.conversation_id == conversation.id)
    )
    return ConversationResponse(
        id=conversation.id,
        title=conversation.title,
        summary=conversation.summary,
        message_count=count_result.scalar() or 0,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        project_id=conversation.project_id,
        memory_scope=conversation.memory_scope,
    )


@router.patch(
    "/conversations/{conversation_id}/project", response_model=ConversationResponse
)
async def rattacher_conversation_a_un_projet(
    conversation_id: str,
    request: ConversationProjectUpdate,
    session: AsyncSession = Depends(get_session),
) -> ConversationResponse:
    """Rattache une conversation à un projet, ou l'en détache (`project_id: null`).

    Ce rattachement commande le CLOISONNEMENT du contexte documentaire : une
    conversation rattachée ne consulte plus que les documents de son projet et
    les documents globaux. Sans cette route, `Conversation.project_id` resterait
    toujours nul et la cloison ne s'appliquerait jamais.
    """
    from datetime import UTC, datetime

    result = await session.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    )
    conversation = result.scalar_one_or_none()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    if request.project_id:
        # Rattacher à un projet inexistant cloisonnerait sur du vide : la
        # conversation ne verrait plus aucun document, sans explication.
        projet = await session.get(Project, request.project_id)
        if projet is None:
            raise HTTPException(status_code=404, detail="Projet introuvable")

    politique = (request.memory_scope or "global").lower()
    if politique not in {"global", "project", "all"}:
        raise HTTPException(status_code=422, detail="Politique documentaire inconnue")

    conversation.project_id = request.project_id or None
    # Un projet rattaché implique la politique `project` : les deux champs ne
    # doivent jamais raconter deux histoires différentes.
    conversation.memory_scope = "project" if conversation.project_id else politique
    conversation.updated_at = datetime.now(UTC)
    session.add(conversation)
    await session.commit()
    await session.refresh(conversation)

    count_result = await session.execute(
        select(func.count()).select_from(Message).where(Message.conversation_id == conversation.id)
    )
    return ConversationResponse(
        id=conversation.id,
        title=conversation.title,
        summary=conversation.summary,
        message_count=count_result.scalar() or 0,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        project_id=conversation.project_id,
        memory_scope=conversation.memory_scope,
    )


@router.get(
    "/conversations/{conversation_id}/messages", response_model=list[MessageResponse]
)
async def get_conversation_messages(
    conversation_id: str,
    limit: int = 100,
    session: AsyncSession = Depends(get_session),
):
    """Get messages for a conversation."""
    result = await session.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at)
        .limit(limit)
    )
    messages = result.scalars().all()

    return [
        MessageResponse(
            id=msg.id,
            conversation_id=msg.conversation_id,
            role=msg.role,
            content=msg.content,
            tokens_in=msg.tokens_in,
            tokens_out=msg.tokens_out,
            model=msg.model,
            provider=msg.provider,
            extra_data=msg.extra_data,
            created_at=msg.created_at,
        )
        for msg in messages
    ]


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    session: AsyncSession = Depends(get_session),
):
    """Delete a conversation and all its messages."""
    result = await session.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    )
    conversation = result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    await session.delete(conversation)
    await session.commit()

    return {"deleted": True, "id": conversation_id}


def _conversation_to_markdown(conversation: Conversation, messages: list[Message]) -> str:
    """Assemble le markdown lisible d'une conversation (export unitaire)."""
    from datetime import UTC, datetime

    lines = [
        f"# {conversation.title or 'Conversation'}",
        "",
        f"*Conversation du {conversation.created_at.strftime('%d/%m/%Y')} - "
        f"exportée le {datetime.now(UTC).strftime('%d/%m/%Y à %H:%M')} depuis THÉRÈSE*",
        "",
        "---",
        "",
    ]
    for msg in messages:
        who = "Vous" if msg.role == "user" else "THÉRÈSE"
        stamp = msg.created_at.strftime("%d/%m/%Y %H:%M")
        suffix = f" ({msg.model})" if msg.role == "assistant" and msg.model else ""
        lines.append(f"## {who}{suffix} - {stamp}")
        lines.append("")
        lines.append(msg.content or "")
        lines.append("")
    return "\n".join(lines).strip() + "\n"


@router.get("/conversations/{conversation_id}/export")
async def export_conversation(
    conversation_id: str,
    format: str = "md",
    session: AsyncSession = Depends(get_session),
) -> dict[str, object]:
    """Exporte UNE conversation en fichier téléchargeable (md ou docx).

    Suggestion testeurs (Dr_logic-3D, avril 2026) : sortir une conversation
    de l'app sans copier-coller. Réutilise le circuit des documents générés :
    fichier déposé dans le dossier de sortie des skills, servi par
    GET /api/skills/download/{file_id}. Format docx : conversion déterministe
    locale `render_markdown_docx` (BUG-135 - l'ancien passage par
    `registry.execute("docx-pro")` pouvait tronquer le contenu après une
    fence ``` non refermée, cas fréquent dans une conversation avec du code).
    """
    from uuid import uuid4

    from app.services.skills import get_skills_registry
    from app.services.skills.markdown_docx import render_markdown_docx

    fmt = (format or "md").lower()
    if fmt not in ("md", "docx"):
        raise HTTPException(
            status_code=400,
            detail=f"Format non supporté : {fmt}. Formats disponibles : md, docx.",
        )

    conversation = await session.get(Conversation, conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    result = await session.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at)
    )
    messages = list(result.scalars().all())
    if not messages:
        raise HTTPException(status_code=400, detail="Conversation vide : rien à exporter.")

    title = conversation.title or "Conversation"
    markdown = _conversation_to_markdown(conversation, messages)
    registry = get_skills_registry()

    # Fichier écrit directement dans le dossier des documents générés (même
    # convention de nommage {titre}_{id8}.{ext}, retrouvé par le download
    # endpoint via glob même sans cache).
    file_id = str(uuid4())
    safe_title = "".join(c if c.isalnum() or c in " -_" else "_" for c in title)[:50].strip()
    file_name = f"{safe_title}_{file_id[:8]}.{fmt}"
    output_path = registry.output_dir / file_name

    if fmt == "docx":
        from app.services.export_profile import load_export_profile

        profile, profile_warning = load_export_profile()
        if profile_warning:
            logger.warning("Export DOCX : %s", profile_warning)
        render_markdown_docx(markdown, output_path, profile=profile)
    else:
        output_path.write_text(markdown, encoding="utf-8")

    return {
        "success": True,
        "format": fmt,
        "file_name": file_name,
        "download_url": f"/api/skills/download/{file_id}",
    }
