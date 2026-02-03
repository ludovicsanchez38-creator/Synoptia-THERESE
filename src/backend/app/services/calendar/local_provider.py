"""
THERESE v2 - Local Calendar Provider

100% local SQLite implementation of CalendarProvider.
No external dependencies, works completely offline.
Part of the "Local First" architecture.
"""

import logging
from datetime import UTC, datetime, date
from typing import Optional
import pytz

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.entities import Calendar, CalendarEvent, generate_uuid
from app.services.calendar.base_provider import (
    CalendarProvider,
    CalendarDTO,
    CalendarEventDTO,
    CreateEventRequest,
    UpdateEventRequest,
)

logger = logging.getLogger(__name__)


class LocalCalendarProvider(CalendarProvider):
    """
    Local SQLite implementation of CalendarProvider.

    Stores all data locally - no external sync required.
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize local calendar provider.

        Args:
            session: AsyncSession for database access
        """
        self._session = session

    @property
    def provider_name(self) -> str:
        return "local"

    @property
    def supports_attendees(self) -> bool:
        return True  # We can store attendees locally

    @property
    def supports_recurrence(self) -> bool:
        return True  # We store RRULE strings

    @property
    def supports_reminders(self) -> bool:
        return True  # We can store reminders locally

    # ============================================================
    # Calendar Operations
    # ============================================================

    async def list_calendars(self) -> list[CalendarDTO]:
        """List all local calendars."""
        statement = select(Calendar).where(Calendar.provider == "local")
        result = await self._session.execute(statement)
        calendars = result.scalars().all()

        return [self._calendar_to_dto(cal) for cal in calendars]

    async def get_calendar(self, calendar_id: str) -> CalendarDTO:
        """Get a single local calendar."""
        calendar = await self._session.get(Calendar, calendar_id)
        if not calendar:
            raise ValueError(f"Calendar {calendar_id} not found")
        return self._calendar_to_dto(calendar)

    async def create_calendar(
        self,
        name: str,
        description: Optional[str] = None,
        timezone: str = "Europe/Paris",
        color: Optional[str] = None,
    ) -> CalendarDTO:
        """Create a new local calendar."""
        # Validate timezone
        try:
            pytz.timezone(timezone)
        except pytz.UnknownTimeZoneError:
            timezone = "Europe/Paris"

        # Check if this is the first calendar (make it primary)
        statement = select(Calendar).where(Calendar.provider == "local")
        result = await self._session.execute(statement)
        existing = result.scalars().all()
        is_primary = len(existing) == 0

        calendar = Calendar(
            id=generate_uuid(),
            summary=name,
            description=description,
            timezone=timezone,
            primary=is_primary,
            provider="local",
        )

        self._session.add(calendar)
        await self._session.commit()
        await self._session.refresh(calendar)

        logger.info(f"Created local calendar: {calendar.id} ({name})")
        return self._calendar_to_dto(calendar)

    async def update_calendar(
        self,
        calendar_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        timezone: Optional[str] = None,
        color: Optional[str] = None,
    ) -> CalendarDTO:
        """Update a local calendar."""
        calendar = await self._session.get(Calendar, calendar_id)
        if not calendar:
            raise ValueError(f"Calendar {calendar_id} not found")

        if name is not None:
            calendar.summary = name
        if description is not None:
            calendar.description = description
        if timezone is not None:
            try:
                pytz.timezone(timezone)
                calendar.timezone = timezone
            except pytz.UnknownTimeZoneError:
                pass  # Keep existing timezone

        calendar.updated_at = datetime.now(UTC)

        self._session.add(calendar)
        await self._session.commit()
        await self._session.refresh(calendar)

        return self._calendar_to_dto(calendar)

    async def delete_calendar(self, calendar_id: str) -> None:
        """Delete a local calendar and all its events."""
        calendar = await self._session.get(Calendar, calendar_id)
        if not calendar:
            raise ValueError(f"Calendar {calendar_id} not found")

        # Delete all events first (cascade should handle this, but be explicit)
        statement = select(CalendarEvent).where(CalendarEvent.calendar_id == calendar_id)
        result = await self._session.execute(statement)
        events = result.scalars().all()
        for event in events:
            await self._session.delete(event)

        await self._session.delete(calendar)
        await self._session.commit()

        logger.info(f"Deleted local calendar: {calendar_id}")

    # ============================================================
    # Event Operations
    # ============================================================

    async def list_events(
        self,
        calendar_id: str,
        time_min: Optional[datetime] = None,
        time_max: Optional[datetime] = None,
        max_results: int = 100,
        page_token: Optional[str] = None,
    ) -> tuple[list[CalendarEventDTO], Optional[str]]:
        """List events from a local calendar."""
        statement = select(CalendarEvent).where(CalendarEvent.calendar_id == calendar_id)

        # Time filtering
        if time_min:
            statement = statement.where(
                (CalendarEvent.start_datetime >= time_min) |
                (CalendarEvent.start_date >= time_min.strftime("%Y-%m-%d"))
            )
        if time_max:
            statement = statement.where(
                (CalendarEvent.start_datetime <= time_max) |
                (CalendarEvent.start_date <= time_max.strftime("%Y-%m-%d"))
            )

        # Order by start time
        statement = statement.order_by(
            CalendarEvent.start_datetime.asc(),
            CalendarEvent.start_date.asc(),
        )

        # Pagination
        offset = int(page_token) if page_token else 0
        statement = statement.offset(offset).limit(max_results)

        result = await self._session.execute(statement)
        events = result.scalars().all()

        # Calculate next page token
        next_token = None
        if len(events) == max_results:
            next_token = str(offset + max_results)

        return [self._event_to_dto(event) for event in events], next_token

    async def get_event(
        self,
        calendar_id: str,
        event_id: str,
    ) -> CalendarEventDTO:
        """Get a single event."""
        event = await self._session.get(CalendarEvent, event_id)
        if not event or event.calendar_id != calendar_id:
            raise ValueError(f"Event {event_id} not found in calendar {calendar_id}")
        return self._event_to_dto(event)

    async def create_event(self, request: CreateEventRequest) -> CalendarEventDTO:
        """Create a new local event."""
        # Verify calendar exists
        calendar = await self._session.get(Calendar, request.calendar_id)
        if not calendar:
            raise ValueError(f"Calendar {request.calendar_id} not found")

        # Determine if all-day event
        is_all_day = request.all_day or isinstance(request.start, date) and not isinstance(request.start, datetime)

        event = CalendarEvent(
            id=generate_uuid(),
            calendar_id=request.calendar_id,
            summary=request.summary,
            description=request.description,
            location=request.location,
            all_day=is_all_day,
            status="confirmed",
        )

        # Set timing
        if is_all_day:
            event.start_date = request.start.strftime("%Y-%m-%d") if isinstance(request.start, (date, datetime)) else str(request.start)
            event.end_date = request.end.strftime("%Y-%m-%d") if isinstance(request.end, (date, datetime)) else str(request.end)
        else:
            event.start_datetime = request.start if isinstance(request.start, datetime) else datetime.combine(request.start, datetime.min.time())
            event.end_datetime = request.end if isinstance(request.end, datetime) else datetime.combine(request.end, datetime.min.time())

        # Set recurrence
        if request.recurrence:
            import json
            event.recurrence = json.dumps(request.recurrence)

        # Set attendees
        if request.attendees:
            import json
            event.attendees = json.dumps(request.attendees)

        self._session.add(event)
        await self._session.commit()
        await self._session.refresh(event)

        logger.info(f"Created local event: {event.id} ({request.summary})")
        return self._event_to_dto(event)

    async def update_event(
        self,
        calendar_id: str,
        event_id: str,
        request: UpdateEventRequest,
    ) -> CalendarEventDTO:
        """Update a local event."""
        event = await self._session.get(CalendarEvent, event_id)
        if not event or event.calendar_id != calendar_id:
            raise ValueError(f"Event {event_id} not found in calendar {calendar_id}")

        if request.summary is not None:
            event.summary = request.summary
        if request.description is not None:
            event.description = request.description
        if request.location is not None:
            event.location = request.location
        if request.status is not None:
            event.status = request.status

        if request.all_day is not None:
            event.all_day = request.all_day

        # Update timing
        if request.start is not None:
            if event.all_day or (request.all_day is True):
                event.start_date = request.start.strftime("%Y-%m-%d") if isinstance(request.start, (date, datetime)) else str(request.start)
                event.start_datetime = None
            else:
                event.start_datetime = request.start if isinstance(request.start, datetime) else datetime.combine(request.start, datetime.min.time())
                event.start_date = None

        if request.end is not None:
            if event.all_day or (request.all_day is True):
                event.end_date = request.end.strftime("%Y-%m-%d") if isinstance(request.end, (date, datetime)) else str(request.end)
                event.end_datetime = None
            else:
                event.end_datetime = request.end if isinstance(request.end, datetime) else datetime.combine(request.end, datetime.min.time())
                event.end_date = None

        if request.recurrence is not None:
            import json
            event.recurrence = json.dumps(request.recurrence) if request.recurrence else None

        if request.attendees is not None:
            import json
            event.attendees = json.dumps(request.attendees) if request.attendees else None

        event.synced_at = datetime.now(UTC)

        self._session.add(event)
        await self._session.commit()
        await self._session.refresh(event)

        return self._event_to_dto(event)

    async def delete_event(
        self,
        calendar_id: str,
        event_id: str,
    ) -> None:
        """Delete a local event."""
        event = await self._session.get(CalendarEvent, event_id)
        if not event or event.calendar_id != calendar_id:
            raise ValueError(f"Event {event_id} not found in calendar {calendar_id}")

        await self._session.delete(event)
        await self._session.commit()

        logger.info(f"Deleted local event: {event_id}")

    # ============================================================
    # Private Helpers
    # ============================================================

    def _calendar_to_dto(self, calendar: Calendar) -> CalendarDTO:
        """Convert Calendar entity to CalendarDTO."""
        return CalendarDTO(
            id=calendar.id,
            name=calendar.summary,
            description=calendar.description,
            timezone=calendar.timezone,
            is_primary=calendar.primary,
            provider="local",
            remote_id=None,
        )

    def _event_to_dto(self, event: CalendarEvent) -> CalendarEventDTO:
        """Convert CalendarEvent entity to CalendarEventDTO."""
        import json

        # Parse attendees
        attendees = []
        if event.attendees:
            try:
                attendees = json.loads(event.attendees)
            except json.JSONDecodeError:
                pass

        # Parse recurrence
        recurrence = None
        if event.recurrence:
            try:
                recurrence = json.loads(event.recurrence)
            except json.JSONDecodeError:
                pass

        # Determine start/end
        if event.all_day:
            start = datetime.strptime(event.start_date, "%Y-%m-%d").date() if event.start_date else None
            end = datetime.strptime(event.end_date, "%Y-%m-%d").date() if event.end_date else None
        else:
            start = event.start_datetime
            end = event.end_datetime

        return CalendarEventDTO(
            id=event.id,
            calendar_id=event.calendar_id,
            summary=event.summary,
            description=event.description,
            location=event.location,
            start=start,
            end=end,
            all_day=event.all_day,
            attendees=attendees,
            recurrence=recurrence,
            status=event.status,
            created_at=event.synced_at,
            updated_at=event.synced_at,
        )
