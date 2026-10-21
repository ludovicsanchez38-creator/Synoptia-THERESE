"""Vue des brouillons existants : lectures SQL uniquement, aucune sauvegarde."""
import json
from typing import Any

from app.models.database import get_session_context
from app.models.entities import Document, EmailMessage, Invoice
from app.services.memory_cards import date_utc
from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import func, literal, union_all
from sqlmodel import col, select

router = APIRouter(prefix='/drafts', tags=['mémoire'])


@router.get('')
async def brouillons(offset: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=100)) -> dict[str, Any]:
    factures = select(col(Invoice.id).label('id'), col(Invoice.document_type).label('kind'),
        col(Invoice.invoice_number).label('title'), col(Invoice.status).label('status'),
        col(Invoice.updated_at).label('updated_at'), literal(None).label('account_id')).where(col(Invoice.status) == 'draft')
    documents = select(col(Document.id).label('id'), literal('document').label('kind'),
        col(Document.title).label('title'), col(Document.status).label('status'),
        col(Document.updated_at).label('updated_at'), literal(None).label('account_id')).where(col(Document.status) == 'en_cours')
    mails = select(col(EmailMessage.id).label('id'), literal('email').label('kind'),
        func.coalesce(col(EmailMessage.subject), 'Mail sans objet').label('title'), literal('draft').label('status'),
        col(EmailMessage.date).label('updated_at'), col(EmailMessage.account_id).label('account_id')).where(col(EmailMessage.is_draft).is_(True))
    vue = union_all(factures, documents, mails).subquery()
    async with get_session_context() as session:
        total = (await session.execute(select(func.count()).select_from(vue))).scalar_one()
        lignes = (await session.execute(select(vue).order_by(vue.c.updated_at.desc(), vue.c.kind, vue.c.id)
            .offset(offset).limit(limit))).mappings().all()
        return {'total': total, 'items': [dict(r) | {'updated_at': date_utc(r['updated_at']).isoformat()} for r in lignes]}


@router.get('/email/{message_id}')
async def mail_local(message_id: str) -> dict[str, Any]:
    async with get_session_context() as session:
        mail = await session.get(EmailMessage, message_id)
        if mail is None or not mail.is_draft:
            raise HTTPException(404, 'Brouillon supprimé ou déjà envoyé.')
        return {'id': mail.id, 'account_id': mail.account_id, 'subject': mail.subject or '',
                'to_emails': json.loads(mail.to_emails or '[]'),
                'cc_emails': json.loads(mail.cc_emails or '[]'),
                'bcc_emails': json.loads(mail.bcc_emails or '[]'),
                'body_plain': mail.body_plain, 'body_html': mail.body_html}
