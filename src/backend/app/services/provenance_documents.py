"""Provenance durable des messages ; l'absence de trace n'est pas une preuve."""
import json
from typing import Any

from app.models.entities import Message
from app.services.memory_card_context import documents_autorises
from app.services.providers.base import Message as LLMMessage

AVIS_HISTORIQUE = (
    "Certains messages de ton historique ont été retirés du contexte transmis, "
    "car leur provenance documentaire est connue ou incertaine et ton accord documents manque."
)


def _donnees(message: Message) -> dict[str, Any]:
    try:
        data = json.loads(message.extra_data or '{}')
        return data if isinstance(data, dict) else {}
    except (TypeError, ValueError):
        return {}


def provenance(message: Message) -> str:
    data = _donnees(message)
    # Les traces conservées priment même sur un ancien tag trop permissif.
    # Sources/citations sans typage : impossible d'exclure un document.
    if any(data.get(key) for key in ('attachments', 'sources', 'citations', 'files', 'file_paths')):
        return 'documents'
    # Tour 7 : `memory_used` ne prouve plus rien à lui seul. Depuis que les
    # fiches portent leur origine, le contexte d'un tour est marqué par les
    # fiches réellement retenues (actualiser_fiches) avant que la réponse ne
    # soit enregistrée. Une fiche née des mots de l'utilisateur ne rend donc
    # plus documentaire toute la conversation. Un ancien message sans
    # provenance reste « inconnue », fiches ou non.
    valeur = data.get('provenance_documents')
    return valeur if isinstance(valeur, str) and valeur in ('documents', 'sans_document') else 'inconnue'


def origine_cumulee(origines: Any) -> str:
    """« documents » l'emporte, puis « inconnue » ; sinon « sans_document »."""
    vues = set(origines)
    if 'documents' in vues:
        return 'documents'
    return 'inconnue' if vues - {'sans_document'} else 'sans_document'


def memoriser_provenance(message: Message, contient_documents: bool | None = None) -> str:
    data = _donnees(message)
    valeur = provenance(message)
    if contient_documents is True:
        valeur = 'documents'
    elif contient_documents is False and valeur != 'documents':
        valeur = 'sans_document'
    data['provenance_documents'] = valeur
    message.extra_data = json.dumps(data, ensure_ascii=False)
    return valeur


def filtrer_historique(messages: list[LLMMessage], config: Any) -> tuple[list[LLMMessage], str]:
    if documents_autorises(config, None):
        return list(messages), ''
    gardes = [m for m in messages if m.contient_documents is False and not m.images]
    return gardes, AVIS_HISTORIQUE if len(gardes) != len(messages) else ''


def copier_messages_differes(messages: list[LLMMessage]) -> list[dict[str, Any]]:
    """Copie textuelle locale : retirer les images ne retire pas leur provenance."""
    return [dict(role=m.role, content=m.content,
                 contient_documents=getattr(m, 'contient_documents', None) is not False
                 or bool(getattr(m, 'images', None)))
            for m in messages if m.role in ('user', 'assistant')]


def reprendre_messages_differes(copies: Any) -> list[LLMMessage]:
    """Les anciens instantanés sans booléen fiable restent documentaires."""
    if not isinstance(copies, list):
        return []
    return [LLMMessage(role=m['role'], content=m['content'],
                       contient_documents=m.get('contient_documents') is not False or bool(m.get('images')))
            for m in copies if isinstance(m, dict) and m.get('role') in ('user', 'assistant')
            and isinstance(m.get('content'), str)]


# Préfixe que RFCChat pose devant chaque saisie : la consigne du mini-chat
# est renvoyée avec le message courant, jamais répétée pour les tours repris.
_MARQUE_SAISIE_RFC = "\n\nMessage de l'utilisateur : "


def texte_rfc(message: Message) -> str:
    """Le texte d'un tour RFC repris, sans la consigne répétée du mini-chat."""
    contenu = message.content or ''
    if message.role == 'user' and contenu.startswith('[Instructions système :') and _MARQUE_SAISIE_RFC in contenu:
        return contenu.split(_MARQUE_SAISIE_RFC, 1)[1]
    return contenu


async def reprendre_rfc(session: Any, source_ids: list[str]) -> tuple[list[Message], str]:
    """Relire les tours RFC en base ; aucune copie du navigateur ne fait preuve.

    Tour 7 : rend les messages d'origine (jamais une transcription recopiée
    dans un message enregistré) et leur origine cumulée, « documents »,
    « inconnue » ou « sans_document ».
    """
    from fastapi import HTTPException
    from sqlmodel import col, select

    if not source_ids or len(source_ids) > 100:
        raise HTTPException(409, "La source de cet échange est incertaine. Renvoie ton message avant de continuer.")
    messages: dict[str, Message] = {}
    for source_id in dict.fromkeys(source_ids):
        source = await session.get(Message, source_id)
        if not source or source.role != 'assistant':
            raise HTTPException(409, "Cet échange est introuvable. Renvoie ton message avant de continuer.")
        # Chaque réponse référence aussi les demandes qui l'ont produite.
        tours = (await session.execute(select(Message).where(
            Message.conversation_id == source.conversation_id,
            Message.created_at <= source.created_at,
        ).order_by(col(Message.created_at), col(Message.id)))).scalars().all()
        for message in tours:
            if message.role in ('user', 'assistant'):
                messages[message.id] = message
    ordonnes = sorted(messages.values(), key=lambda m: (m.created_at, m.id))
    return ordonnes, origine_cumulee(provenance(m) for m in ordonnes)


def transcription_rfc(messages: list[Message]) -> str:
    return '\n\n'.join(f'{m.role}: {texte_rfc(m)}' for m in messages)


def contexte_documentaire(context: Any) -> bool:
    """Inclure aussi les copies conservées pour les continuations mémoire."""
    if getattr(context, 'contient_documents', None) is not False:
        return True
    return any(getattr(m, 'contient_documents', None) is not False or bool(getattr(m, 'images', None))
               for m in [*(getattr(context, 'messages', None) or []),
                         *(getattr(context, 'memory_original_messages', None) or [])])


def origine_contexte(context: Any) -> str:
    """Origine prudente d'un contexte, sur trois niveaux, pour une écriture.

    « documents » dès qu'un document avéré y figure, ou quand le contexte ne
    dit pas ce qu'il contient ; « inconnue » quand seule une provenance
    incertaine (ancien message, ancienne fiche) le marque.
    """
    messages = getattr(context, 'messages', None)
    if getattr(context, 'contient_documents', None) is None or not isinstance(messages, list):
        return 'documents'
    if not contexte_documentaire(context):
        return 'sans_document'
    return 'inconnue' if getattr(context, 'documents_averes', None) is False else 'documents'
