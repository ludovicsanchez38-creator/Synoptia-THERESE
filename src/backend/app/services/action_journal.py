"""Journal local : aucune copie des arguments ou de la prose des outils."""
import json
from typing import Any

from app.models.database import get_session_context
from app.models.entities import Activity, Contact, Conversation, Project
from app.services.memory_card_security import contient_sensible
from fastapi import HTTPException
from sqlmodel import select


def verifier_texte(title: str, description: str | None, extra_data: str | None) -> None:
    try:
        extra = json.loads(extra_data) if extra_data else None
    except (ValueError, TypeError):
        raise HTTPException(422, 'Les informations de la trace doivent être un objet JSON.') from None
    if contient_sensible([title, description, extra]):
        raise HTTPException(422, 'Cette donnée sensible ne peut pas être conservée dans Mémoire.')


def issue_structuree(tool_name: str, resultat: str) -> dict[str, Any]:
    try:
        data = json.loads(resultat)
    except (ValueError, TypeError):
        data = {}
    if not isinstance(data, dict):
        data = {}
    if data.get('success') is False or data.get('error'):
        return {'outcome': 'echouee'}
    envoi = tool_name.split('__')[-1] == 'send_email'
    recu = data.get('message_id')
    # Le reçu est conservé tel quel seulement si la garde l'admet.
    if envoi and data.get('success') is True and isinstance(recu, str) and recu and not contient_sensible(recu):
        return {'outcome': 'envoyee', 'receipt': recu}
    return {'outcome': 'reussie' if data.get('success') is True and not envoi else 'indeterminee'}


async def commencer(execution_id: str, arguments: dict[str, Any], conversation_id: str | None,
                   approved: bool, tool_name: str = "") -> str:
    async with get_session_context() as session:
        precedente = (await session.execute(select(Activity).where(Activity.execution_id == execution_id))).scalar_one_or_none()
        if precedente:
            return precedente.id
        conv = await session.get(Conversation, conversation_id) if conversation_id else None
        contact_id = arguments.get('contact_id')
        contact = await session.get(Contact, contact_id) if isinstance(contact_id, str) else None
        projet_id = conv.project_id if conv else None
        if not projet_id and isinstance(arguments.get('project_id'), str):
            projet = await session.get(Project, arguments['project_id'])
            projet_id = projet.id if projet else None
        titres = {'send_email': 'Envoi de mail', 'create_task': 'Création de tâche',
                  'create_contact': 'Création de contact', 'create_project': 'Création de projet',
                  'create_invoice': 'Création de brouillon de facturation',
                  'generate_document': 'Création de document', 'create_calendar_event': 'Création de rendez-vous'}
        titre = titres.get(tool_name.split('__')[-1], 'Action de Thérèse')
        trace = Activity(type='agent_action', title=titre,
            contact_id=contact.id if contact else None, project_id=projet_id,
            conversation_id=conv.id if conv else None, execution_id=execution_id,
            extra_data=json.dumps({'outcome': 'confirmee' if approved else 'annulee'}))
        verifier_texte(trace.title, trace.description, trace.extra_data)
        session.add(trace)
        await session.commit()
        return trace.id


async def terminer(trace_id: str, tool_name: str, resultat: str) -> None:
    async with get_session_context() as session:
        trace = await session.get(Activity, trace_id)
        if trace is None:
            return
        trace.extra_data = json.dumps(issue_structuree(tool_name, resultat), ensure_ascii=False)
        verifier_texte(trace.title, trace.description, trace.extra_data)
        session.add(trace)
        await session.commit()


def clause_du_contact(contact_id: str) -> Any:
    from sqlalchemy import or_
    projets = select(Project.id).where(Project.contact_id == contact_id)
    return or_(Activity.contact_id == contact_id, Activity.project_id.in_(projets))


async def effacer_activites(session: Any, clause: Any) -> int:
    from sqlalchemy import delete, update
    ids = list((await session.execute(select(Activity.id).where(clause))).scalars())
    if ids:
        await session.execute(update(Activity).where(Activity.remplace_id.in_(ids)).values(remplace_id=None))
        await session.execute(delete(Activity).where(Activity.id.in_(ids)))
    return len(ids)
