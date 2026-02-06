"""
THERESE v2 - Google Calendar Provider

Google Calendar API implementation of CalendarProvider.
Wraps the existing CalendarService.
"""

import logging
from datetime import date, datetime

from app.services.calendar.base_provider import (
    CalendarDTO,
    CalendarEventDTO,
    CalendarProvider,
    CreateEventRequest,
    UpdateEventRequest,
)
from app.services.calendar_service import CalendarService

logger = logging.getLogger(__name__)


class GoogleCalendarProvider(CalendarProvider):
    """
    Google Calendar implementation of CalendarProvider.

    Uses OAuth2 access token for authentication.
    """

    def __init__(self, access_token: str):
        """
        Initialize Google Calendar provider.

        Args:
            access_token: Valid OAuth2 access token
        """
        self._service = CalendarService(access_token)

    @property
    def provider_name(self) -> str:
        return "google"

    @property
    def supports_attendees(self) -> bool:
        return True

    @property
    def supports_recurrence(self) -> bool:
        return True

    @property
    def supports_reminders(self) -> bool:
        return True

    # ============================================================
    # Calendar Operations
    # ============================================================

    async def list_calendars(self) -> list[CalendarDTO]:
        """List all Google calendars."""
        calendars = await self._service.list_calendars()
        return [self._gcal_to_dto(cal) for cal in calendars]

    async def get_calendar(self, calendar_id: str) -> CalendarDTO:
        """Get a single Google calendar."""
        calendar = await self._service.get_calendar(calendar_id)
        return self._gcal_to_dto(calendar)

    async def create_calendar(
        self,
        name: str,
        description: str | None = None,
        timezone: str = "Europe/Paris",
        color: str | None = None,
    ) -> CalendarDTO:
        """Create a new Google calendar."""
        calendar = await self._service.create_calendar(
            summary=name,
            description=description,
            timezone=timezone,
        )
        return self._gcal_to_dto(calendar)

    async def update_calendar(
        self,
        calendar_id: str,
        name: str | None = None,
        description: str | None = None,
        timezone: str | None = None,
        color: str | None = None,
    ) -> CalendarDTO:
        """Update a Google calendar."""
        # Google Calendar API requires fetching first, then updating
        current = await self._service.get_calendar(calendar_id)

        # Build update payload
        from app.services.http_client import get_http_client

        url = f"https://www.googleapis.com/calendar/v3/calendars/{calendar_id}"
        headers = {
            "Authorization": f"Bearer {self._service.access_token}",
            "Content-Type": "application/json",
        }

        payload = {
            "summary": name or current.get("summary"),
            "description": description if description is not None else current.get("description"),
            "timeZone": timezone or current.get("timeZone", "Europe/Paris"),
        }

        client = await get_http_client()
        response = await client.put(url, headers=headers, json=payload, timeout=30.0)
        response.raise_for_status()
        updated = response.json()

        return self._gcal_to_dto(updated)

    async def delete_calendar(self, calendar_id: str) -> None:
        """Delete a Google calendar."""
        await self._service.delete_calendar(calendar_id)

    # ============================================================
    # Event Operations
    # ============================================================

    async def list_events(
        self,
        calendar_id: str,
        time_min: datetime | None = None,
        time_max: datetime | None = None,
        max_results: int = 100,
        page_token: str | None = None,
    ) -> tuple[list[CalendarEventDTO], str | None]:
        """List events from a Google calendar."""
        result = await self._service.list_events(
            calendar_id=calendar_id,
            time_min=time_min,
            time_max=time_max,
            max_results=max_results,
            page_token=page_token,
        )

        events = [self._gevent_to_dto(event, calendar_id) for event in result.get("items", [])]
        next_token = result.get("nextPageToken")

        return events, next_token

    async def get_event(
        self,
        calendar_id: str,
        event_id: str,
    ) -> CalendarEventDTO:
        """Get a single event from Google Calendar."""
        event = await self._service.get_event(calendar_id, event_id)
        return self._gevent_to_dto(event, calendar_id)

    async def create_event(self, request: CreateEventRequest) -> CalendarEventDTO:
        """Create a new event in Google Calendar."""
        # Build start/end objects
        if request.all_day:
            start = {"date": request.start.strftime("%Y-%m-%d") if isinstance(request.start, (date, datetime)) else str(request.start)}
            end = {"date": request.end.strftime("%Y-%m-%d") if isinstance(request.end, (date, datetime)) else str(request.end)}
        else:
            start_dt = request.start if isinstance(request.start, datetime) else datetime.combine(request.start, datetime.min.time())
            end_dt = request.end if isinstance(request.end, datetime) else datetime.combine(request.end, datetime.min.time())
            start = {"dateTime": start_dt.isoformat(), "timeZone": request.timezone}
            end = {"dateTime": end_dt.isoformat(), "timeZone": request.timezone}

        result = await self._service.create_event(
            calendar_id=request.calendar_id,
            summary=request.summary,
            start=start,
            end=end,
            description=request.description,
            location=request.location,
            attendees=request.attendees if request.attendees else None,
            recurrence=request.recurrence,
        )

        return self._gevent_to_dto(result, request.calendar_id)

    async def update_event(
        self,
        calendar_id: str,
        event_id: str,
        request: UpdateEventRequest,
    ) -> CalendarEventDTO:
        """Update an event in Google Calendar."""
        # Build optional start/end
        start = None
        end = None

        if request.start is not None:
            if request.all_day is True:
                start = {"date": request.start.strftime("%Y-%m-%d") if isinstance(request.start, (date, datetime)) else str(request.start)}
            else:
                start_dt = request.start if isinstance(request.start, datetime) else datetime.combine(request.start, datetime.min.time())
                start = {"dateTime": start_dt.isoformat(), "timeZone": request.timezone or "Europe/Paris"}

        if request.end is not None:
            if request.all_day is True:
                end = {"date": request.end.strftime("%Y-%m-%d") if isinstance(request.end, (date, datetime)) else str(request.end)}
            else:
                end_dt = request.end if isinstance(request.end, datetime) else datetime.combine(request.end, datetime.min.time())
                end = {"dateTime": end_dt.isoformat(), "timeZone": request.timezone or "Europe/Paris"}

        result = await self._service.update_event(
            calendar_id=calendar_id,
            event_id=event_id,
            summary=request.summary,
            start=start,
            end=end,
            description=request.description,
            location=request.location,
            attendees=request.attendees,
            recurrence=request.recurrence,
        )

        return self._gevent_to_dto(result, calendar_id)

    async def delete_event(
        self,
        calendar_id: str,
        event_id: str,
    ) -> None:
        """Delete an event from Google Calendar."""
        await self._service.delete_event(calendar_id, event_id)

    # ============================================================
    # Private Helpers
    # ============================================================

    def _gcal_to_dto(self, gcal: dict) -> CalendarDTO:
        """Convert Google Calendar API calendar to CalendarDTO."""
        return CalendarDTO(
            id=gcal.get("id", ""),
            name=gcal.get("summary", ""),
            description=gcal.get("description"),
            timezone=gcal.get("timeZone", "Europe/Paris"),
            is_primary=gcal.get("primary", False),
            color=gcal.get("backgroundColor"),
            provider="google",
            remote_id=gcal.get("id"),
        )

    def _gevent_to_dto(self, gevent: dict, calendar_id: str) -> CalendarEventDTO:
        """Convert Google Calendar API event to CalendarEventDTO."""
        # Parse start/end
        start_obj = gevent.get("start", {})
        end_obj = gevent.get("end", {})

        all_day = "date" in start_obj

        if all_day:
            start = datetime.strptime(start_obj["date"], "%Y-%m-%d").date()
            end = datetime.strptime(end_obj["date"], "%Y-%m-%d").date()
        else:
            start_str = start_obj.get("dateTime", "")
            end_str = end_obj.get("dateTime", "")
            start = datetime.fromisoformat(start_str.replace("Z", "+00:00")) if start_str else None
            end = datetime.fromisoformat(end_str.replace("Z", "+00:00")) if end_str else None

        # Parse attendees
        attendees = [
            att.get("email", "")
            for att in gevent.get("attendees", [])
            if att.get("email")
        ]

        # Parse organizer
        organizer = gevent.get("organizer", {}).get("email")

        # Parse created/updated
        created_str = gevent.get("created")
        updated_str = gevent.get("updated")

        created = datetime.fromisoformat(created_str.replace("Z", "+00:00")) if created_str else None
        updated = datetime.fromisoformat(updated_str.replace("Z", "+00:00")) if updated_str else None

        return CalendarEventDTO(
            id=gevent.get("id", ""),
            calendar_id=calendar_id,
            summary=gevent.get("summary", ""),
            description=gevent.get("description"),
            location=gevent.get("location"),
            start=start,
            end=end,
            all_day=all_day,
            timezone=start_obj.get("timeZone", "Europe/Paris"),
            recurrence=gevent.get("recurrence"),
            recurring_event_id=gevent.get("recurringEventId"),
            attendees=attendees,
            organizer=organizer,
            status=gevent.get("status", "confirmed"),
            created_at=created,
            updated_at=updated,
            remote_id=gevent.get("id"),
        )
