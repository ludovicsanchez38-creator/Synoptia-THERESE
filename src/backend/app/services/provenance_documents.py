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
    if any(data.get(key) for key in ('attachments', 'sources', 'citations', 'files', 'file_paths', 'memory_used')):
        return 'documents'
    valeur = data.get('provenance_documents')
    return valeur if isinstance(valeur, str) and valeur in ('documents', 'sans_document') else 'inconnue'


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
