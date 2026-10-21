"""Liens des notes vérifiés en base locale ; aucune copie du rendez-vous."""
import json
from typing import Any

from app.models.entities import CalendarEvent
from fastapi import HTTPException


def liens(extra_data: str | None) -> dict[str, Any]:
    try:
        data = json.loads(extra_data or '{}')
    except (ValueError, TypeError):
        return {}
    return data if isinstance(data, dict) else {}


async def verifier_evenement(session: Any, extra: dict[str, Any]) -> CalendarEvent:
    identifiant, calendrier = extra.get('calendar_event_id'), extra.get('calendar_id')
    if not isinstance(identifiant, str) or not isinstance(calendrier, str) or not identifiant or not calendrier:
        raise HTTPException(422, 'Choisis le rendez-vous auquel cette note appartient.')
    event = await session.get(CalendarEvent, identifiant)
    if event is None or event.calendar_id != calendrier:
        raise HTTPException(404, 'Rendez-vous supprimé ou indisponible.')
    return event
