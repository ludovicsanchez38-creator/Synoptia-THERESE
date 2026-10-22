"""Raccord du composeur au cache chiffré des mails sauvegardés."""
import json
from datetime import UTC, datetime
from typing import Any

from app.models.entities import EmailMessage
from fastapi import HTTPException


async def identifiant_du_brouillon(gmail: Any, message_id: str) -> str:
    page: str | None = None
    vues: set[str] = set()
    while True:
        params: dict[str, Any] = {'maxResults': 500}
        if page:
            params['pageToken'] = page
        resultat = await gmail._request('GET', 'users/me/drafts', params=params)
        for draft in resultat.get('drafts', []):
            if draft.get('message', {}).get('id') == message_id and isinstance(draft.get('id'), str):
                return str(draft['id'])
        page = resultat.get('nextPageToken')
        if not page or page in vues:
            raise HTTPException(409, 'Ce brouillon a changé ou a déjà été envoyé. Synchronise tes mails avant de le rouvrir.')
        vues.add(page)


async def actualiser_cache(session: Any, account: Any, request: Any, message_id: str | None,
                           source_message_id: str | None = None, thread_id: str | None = None,
                           generation_attendue: int | None = None) -> None:
    from app.models.database import get_session_context
    from app.services.memory_tools import _proteger_le_geste, generation_des_donnees
    if not message_id:
        return
    generation = generation_des_donnees() if generation_attendue is None else generation_attendue
    async def geste() -> str:
        async with get_session_context() as courte:
            from sqlalchemy import text
            await courte.execute(text('BEGIN IMMEDIATE'))
            if generation != generation_des_donnees():
                return '{}'
            # Le compte peut avoir été effacé pendant l'attente du service.
            from app.models.entities import EmailAccount
            if await courte.get(EmailAccount, account.id) is None:
                return '{}'
            await _actualiser(courte, account, request, message_id, source_message_id, thread_id)
            return '{}'
    await _proteger_le_geste(geste())


async def _actualiser(session: Any, account: Any, request: Any, message_id: str,
                      source_message_id: str | None, thread_id: str | None) -> None:
    source = await session.get(EmailMessage, source_message_id) if source_message_id else None
    if source_message_id and (source is None or not source.is_draft):
        return
    message = await session.get(EmailMessage, message_id)
    contact_id = source.contact_id if source else None
    if source is not None and source.id != message_id:
        await session.delete(source)
        await session.flush()
    now = datetime.now(UTC)
    if message is None:
        message = EmailMessage(id=message_id, thread_id=thread_id or message_id,
            account_id=account.id, from_email=account.email, to_emails='[]', labels='["DRAFT"]',
            date=now, internal_date=now, is_draft=True, contact_id=contact_id)
    message.subject = request.subject
    message.to_emails = json.dumps(request.to)
    message.cc_emails = json.dumps(request.cc or [])
    message.bcc_emails = json.dumps(request.bcc or [])
    message.body_html = request.body if request.html else None
    message.body_plain = None if request.html else request.body
    message.date = now
    session.add(message)
    await session.commit()
