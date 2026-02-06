"""
THÉRÈSE v2 - Calendar Service (Google Calendar API)

Service client pour Google Calendar API.
Réutilise OAuth de email_service.py.

Phase 2 - Calendar
"""

import logging
from datetime import datetime
from typing import Any

from app.services.http_client import get_http_client

logger = logging.getLogger(__name__)


class CalendarService:
    """Client Google Calendar API avec OAuth access token."""

    BASE_URL = "https://www.googleapis.com/calendar/v3"

    def __init__(self, access_token: str):
        """
        Initialise le service Calendar.

        Args:
            access_token: OAuth 2.0 access token avec scopes calendar
        """
        self.access_token = access_token
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

    # =============================================================================
    # CALENDARS MANAGEMENT
    # =============================================================================

    async def list_calendars(self) -> list[dict[str, Any]]:
        """
        Liste tous les calendriers de l'utilisateur.

        Returns:
            Liste des calendriers avec id, summary, description, etc.

        Raises:
            HTTPException: Si l'API Calendar échoue
        """
        client = await get_http_client()
        response = await client.get(
            f"{self.BASE_URL}/users/me/calendarList",
            headers=self.headers,
            timeout=30.0,
        )
        response.raise_for_status()
        data = response.json()
        return data.get("items", [])

    async def get_calendar(self, calendar_id: str) -> dict[str, Any]:
        """
        Récupère un calendrier spécifique.

        Args:
            calendar_id: ID du calendrier

        Returns:
            Détails du calendrier
        """
        client = await get_http_client()
        response = await client.get(
            f"{self.BASE_URL}/calendars/{calendar_id}",
            headers=self.headers,
            timeout=30.0,
        )
        response.raise_for_status()
        return response.json()

    async def create_calendar(
        self, summary: str, description: str | None = None, timezone: str = "UTC"
    ) -> dict[str, Any]:
        """
        Crée un nouveau calendrier.

        Args:
            summary: Nom du calendrier
            description: Description optionnelle
            timezone: Timezone (ex: "Europe/Paris")

        Returns:
            Calendrier créé
        """
        payload = {"summary": summary, "timeZone": timezone}
        if description:
            payload["description"] = description

        client = await get_http_client()
        response = await client.post(
            f"{self.BASE_URL}/calendars",
            headers=self.headers,
            json=payload,
            timeout=30.0,
        )
        response.raise_for_status()
        return response.json()

    async def delete_calendar(self, calendar_id: str) -> None:
        """
        Supprime un calendrier.

        Args:
            calendar_id: ID du calendrier à supprimer
        """
        client = await get_http_client()
        response = await client.delete(
            f"{self.BASE_URL}/calendars/{calendar_id}",
            headers=self.headers,
            timeout=30.0,
        )
        response.raise_for_status()

    # =============================================================================
    # EVENTS MANAGEMENT
    # =============================================================================

    async def list_events(
        self,
        calendar_id: str = "primary",
        time_min: datetime | None = None,
        time_max: datetime | None = None,
        max_results: int = 50,
        page_token: str | None = None,
    ) -> dict[str, Any]:
        """
        Liste les événements d'un calendrier.

        Args:
            calendar_id: ID du calendrier (défaut: "primary")
            time_min: Date minimum (ISO 8601)
            time_max: Date maximum (ISO 8601)
            max_results: Nombre max de résultats (1-250)
            page_token: Token pagination

        Returns:
            Dict avec 'items' (événements) et 'nextPageToken'
        """
        params: dict[str, Any] = {
            "maxResults": min(max_results, 250),
            "singleEvents": True,  # Expand recurring events
            "orderBy": "startTime",
        }

        if time_min:
            params["timeMin"] = time_min.isoformat() + "Z"
        if time_max:
            params["timeMax"] = time_max.isoformat() + "Z"
        if page_token:
            params["pageToken"] = page_token

        client = await get_http_client()
        response = await client.get(
            f"{self.BASE_URL}/calendars/{calendar_id}/events",
            headers=self.headers,
            params=params,
            timeout=30.0,
        )
        response.raise_for_status()
        return response.json()

    async def get_event(self, calendar_id: str, event_id: str) -> dict[str, Any]:
        """
        Récupère un événement spécifique.

        Args:
            calendar_id: ID du calendrier
            event_id: ID de l'événement

        Returns:
            Détails de l'événement
        """
        client = await get_http_client()
        response = await client.get(
            f"{self.BASE_URL}/calendars/{calendar_id}/events/{event_id}",
            headers=self.headers,
            timeout=30.0,
        )
        response.raise_for_status()
        return response.json()

    async def create_event(
        self,
        calendar_id: str,
        summary: str,
        start: dict[str, Any],
        end: dict[str, Any],
        description: str | None = None,
        location: str | None = None,
        attendees: list[str] | None = None,
        recurrence: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Crée un nouvel événement.

        Args:
            calendar_id: ID du calendrier
            summary: Titre de l'événement
            start: {'dateTime': '2026-01-27T10:00:00Z'} ou {'date': '2026-01-27'}
            end: {'dateTime': '2026-01-27T11:00:00Z'} ou {'date': '2026-01-27'}
            description: Description optionnelle
            location: Lieu optionnel
            attendees: Liste d'emails des participants
            recurrence: Liste de règles RRULE (ex: ['RRULE:FREQ=DAILY;COUNT=5'])

        Returns:
            Événement créé avec ID
        """
        payload: dict[str, Any] = {
            "summary": summary,
            "start": start,
            "end": end,
        }

        if description:
            payload["description"] = description
        if location:
            payload["location"] = location
        if attendees:
            payload["attendees"] = [{"email": email} for email in attendees]
        if recurrence:
            payload["recurrence"] = recurrence

        client = await get_http_client()
        response = await client.post(
            f"{self.BASE_URL}/calendars/{calendar_id}/events",
            headers=self.headers,
            json=payload,
            timeout=30.0,
        )
        response.raise_for_status()
        return response.json()

    async def update_event(
        self,
        calendar_id: str,
        event_id: str,
        summary: str | None = None,
        start: dict[str, Any] | None = None,
        end: dict[str, Any] | None = None,
        description: str | None = None,
        location: str | None = None,
        attendees: list[str] | None = None,
        recurrence: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Met à jour un événement existant.

        Args:
            calendar_id: ID du calendrier
            event_id: ID de l'événement à modifier
            summary: Nouveau titre (optionnel)
            start: Nouveau début (optionnel)
            end: Nouvelle fin (optionnel)
            description: Nouvelle description (optionnel)
            location: Nouveau lieu (optionnel)
            attendees: Nouveaux participants (optionnel)
            recurrence: Nouvelles règles de récurrence (optionnel)

        Returns:
            Événement mis à jour
        """
        # Fetch current event first
        current_event = await self.get_event(calendar_id, event_id)

        # Update only provided fields
        if summary is not None:
            current_event["summary"] = summary
        if start is not None:
            current_event["start"] = start
        if end is not None:
            current_event["end"] = end
        if description is not None:
            current_event["description"] = description
        if location is not None:
            current_event["location"] = location
        if attendees is not None:
            current_event["attendees"] = [{"email": email} for email in attendees]
        if recurrence is not None:
            current_event["recurrence"] = recurrence

        client = await get_http_client()
        response = await client.put(
            f"{self.BASE_URL}/calendars/{calendar_id}/events/{event_id}",
            headers=self.headers,
            json=current_event,
            timeout=30.0,
        )
        response.raise_for_status()
        return response.json()

    async def delete_event(self, calendar_id: str, event_id: str) -> None:
        """
        Supprime un événement.

        Args:
            calendar_id: ID du calendrier
            event_id: ID de l'événement à supprimer
        """
        client = await get_http_client()
        response = await client.delete(
            f"{self.BASE_URL}/calendars/{calendar_id}/events/{event_id}",
            headers=self.headers,
            timeout=30.0,
        )
        response.raise_for_status()

    async def quick_add_event(self, calendar_id: str, text: str) -> dict[str, Any]:
        """
        Ajoute un événement via parsing texte naturel.
        Ex: "Déjeuner avec Pierre demain à 12h30"

        Args:
            calendar_id: ID du calendrier
            text: Description textuelle de l'événement

        Returns:
            Événement créé
        """
        params = {"text": text}

        client = await get_http_client()
        response = await client.post(
            f"{self.BASE_URL}/calendars/{calendar_id}/events/quickAdd",
            headers=self.headers,
            params=params,
            timeout=30.0,
        )
        response.raise_for_status()
        return response.json()
