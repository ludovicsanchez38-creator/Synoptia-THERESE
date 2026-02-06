"""
THERESE v2 - Calendar Provider Abstract Interface

Defines the contract for calendar providers (Local, Google, CalDAV).
Part of the "Local First" architecture.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, timedelta
from typing import Literal, Optional


@dataclass
class CalendarDTO:
    """Data Transfer Object for calendars."""
    id: str
    name: str
    description: str | None = None
    timezone: str = "Europe/Paris"
    is_primary: bool = False
    color: str | None = None
    provider: str = "local"  # local, google, caldav
    remote_id: str | None = None  # External provider ID


@dataclass
class CalendarEventDTO:
    """Data Transfer Object for calendar events."""
    id: str
    calendar_id: str
    summary: str
    description: str | None = None
    location: str | None = None

    # Timing
    start: datetime | date | None = None  # datetime for timed events, date for all-day
    end: datetime | date | None = None
    all_day: bool = False
    timezone: str = "Europe/Paris"

    # Recurrence
    recurrence: list[str] | None = None  # RRULE strings
    recurring_event_id: str | None = None  # Parent event for instances

    # Attendees
    attendees: list[str] = field(default_factory=list)  # Email addresses
    organizer: str | None = None

    # Status
    status: Literal["confirmed", "tentative", "cancelled"] = "confirmed"

    # Reminders
    reminders: list[int] = field(default_factory=list)  # Minutes before event

    # Metadata
    created_at: datetime | None = None
    updated_at: datetime | None = None

    # External reference
    remote_id: str | None = None  # External provider event ID


@dataclass
class CreateEventRequest:
    """Request to create a calendar event."""
    calendar_id: str
    summary: str
    start: datetime | date
    end: datetime | date
    description: str | None = None
    location: str | None = None
    all_day: bool = False
    timezone: str = "Europe/Paris"
    attendees: list[str] = field(default_factory=list)
    recurrence: list[str] | None = None
    reminders: list[int] = field(default_factory=lambda: [30])  # Default 30 min reminder


@dataclass
class UpdateEventRequest:
    """Request to update a calendar event."""
    summary: str | None = None
    start: Optional[datetime | date] = None
    end: Optional[datetime | date] = None
    description: str | None = None
    location: str | None = None
    all_day: bool | None = None
    timezone: str | None = None
    attendees: list[str] | None = None
    recurrence: list[str] | None = None
    status: Literal["confirmed", "tentative", "cancelled"] | None = None
    reminders: list[int] | None = None


class CalendarProvider(ABC):
    """
    Abstract base class for calendar providers.

    Defines the contract that all calendar providers must implement.
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the provider name (e.g., 'local', 'google', 'caldav')."""
        pass

    @property
    def supports_attendees(self) -> bool:
        """Whether the provider supports event attendees."""
        return False

    @property
    def supports_recurrence(self) -> bool:
        """Whether the provider supports recurring events."""
        return True

    @property
    def supports_reminders(self) -> bool:
        """Whether the provider supports event reminders."""
        return False

    # ============================================================
    # Calendar Operations
    # ============================================================

    @abstractmethod
    async def list_calendars(self) -> list[CalendarDTO]:
        """
        List all calendars.

        Returns:
            List of CalendarDTO
        """
        pass

    @abstractmethod
    async def get_calendar(self, calendar_id: str) -> CalendarDTO:
        """
        Get a single calendar by ID.

        Args:
            calendar_id: Calendar ID

        Returns:
            CalendarDTO
        """
        pass

    @abstractmethod
    async def create_calendar(
        self,
        name: str,
        description: str | None = None,
        timezone: str = "Europe/Paris",
        color: str | None = None,
    ) -> CalendarDTO:
        """
        Create a new calendar.

        Args:
            name: Calendar name
            description: Optional description
            timezone: Timezone (default Europe/Paris)
            color: Optional color code

        Returns:
            Created CalendarDTO
        """
        pass

    @abstractmethod
    async def update_calendar(
        self,
        calendar_id: str,
        name: str | None = None,
        description: str | None = None,
        timezone: str | None = None,
        color: str | None = None,
    ) -> CalendarDTO:
        """
        Update a calendar.

        Args:
            calendar_id: Calendar ID
            name: New name
            description: New description
            timezone: New timezone
            color: New color

        Returns:
            Updated CalendarDTO
        """
        pass

    @abstractmethod
    async def delete_calendar(self, calendar_id: str) -> None:
        """
        Delete a calendar.

        Args:
            calendar_id: Calendar ID
        """
        pass

    # ============================================================
    # Event Operations
    # ============================================================

    @abstractmethod
    async def list_events(
        self,
        calendar_id: str,
        time_min: datetime | None = None,
        time_max: datetime | None = None,
        max_results: int = 100,
        page_token: str | None = None,
    ) -> tuple[list[CalendarEventDTO], str | None]:
        """
        List events from a calendar.

        Args:
            calendar_id: Calendar ID
            time_min: Start of time range
            time_max: End of time range
            max_results: Maximum number of events
            page_token: Pagination token

        Returns:
            Tuple of (events, next_page_token)
        """
        pass

    @abstractmethod
    async def get_event(
        self,
        calendar_id: str,
        event_id: str,
    ) -> CalendarEventDTO:
        """
        Get a single event by ID.

        Args:
            calendar_id: Calendar ID
            event_id: Event ID

        Returns:
            CalendarEventDTO
        """
        pass

    @abstractmethod
    async def create_event(self, request: CreateEventRequest) -> CalendarEventDTO:
        """
        Create a new event.

        Args:
            request: CreateEventRequest with event details

        Returns:
            Created CalendarEventDTO
        """
        pass

    @abstractmethod
    async def update_event(
        self,
        calendar_id: str,
        event_id: str,
        request: UpdateEventRequest,
    ) -> CalendarEventDTO:
        """
        Update an existing event.

        Args:
            calendar_id: Calendar ID
            event_id: Event ID
            request: UpdateEventRequest with changes

        Returns:
            Updated CalendarEventDTO
        """
        pass

    @abstractmethod
    async def delete_event(
        self,
        calendar_id: str,
        event_id: str,
    ) -> None:
        """
        Delete an event.

        Args:
            calendar_id: Calendar ID
            event_id: Event ID
        """
        pass

    # ============================================================
    # Utility Methods
    # ============================================================

    async def get_events_for_day(
        self,
        calendar_id: str,
        day: date,
    ) -> list[CalendarEventDTO]:
        """
        Get all events for a specific day.

        Args:
            calendar_id: Calendar ID
            day: Date to query

        Returns:
            List of events
        """
        time_min = datetime.combine(day, datetime.min.time())
        time_max = datetime.combine(day, datetime.max.time())

        events, _ = await self.list_events(
            calendar_id=calendar_id,
            time_min=time_min,
            time_max=time_max,
        )
        return events

    async def get_upcoming_events(
        self,
        calendar_id: str,
        days: int = 7,
        max_results: int = 20,
    ) -> list[CalendarEventDTO]:
        """
        Get upcoming events for the next N days.

        Args:
            calendar_id: Calendar ID
            days: Number of days to look ahead
            max_results: Maximum events to return

        Returns:
            List of upcoming events
        """
        time_min = datetime.now(UTC)
        time_max = time_min + timedelta(days=days)

        events, _ = await self.list_events(
            calendar_id=calendar_id,
            time_min=time_min,
            time_max=time_max,
            max_results=max_results,
        )
        return events

    async def test_connection(self) -> bool:
        """
        Test the connection to the calendar provider.

        Returns:
            True if connection successful
        """
        try:
            await self.list_calendars()
            return True
        except Exception:
            return False
