"""
THERESE v2 - Calendar Provider Abstract Interface

Defines the contract for calendar providers (Local, Google, CalDAV).
Part of the "Local First" architecture.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import UTC, datetime, date, timedelta
from typing import Literal, Optional


@dataclass
class CalendarDTO:
    """Data Transfer Object for calendars."""
    id: str
    name: str
    description: Optional[str] = None
    timezone: str = "Europe/Paris"
    is_primary: bool = False
    color: Optional[str] = None
    provider: str = "local"  # local, google, caldav
    remote_id: Optional[str] = None  # External provider ID


@dataclass
class CalendarEventDTO:
    """Data Transfer Object for calendar events."""
    id: str
    calendar_id: str
    summary: str
    description: Optional[str] = None
    location: Optional[str] = None

    # Timing
    start: datetime | date | None = None  # datetime for timed events, date for all-day
    end: datetime | date | None = None
    all_day: bool = False
    timezone: str = "Europe/Paris"

    # Recurrence
    recurrence: Optional[list[str]] = None  # RRULE strings
    recurring_event_id: Optional[str] = None  # Parent event for instances

    # Attendees
    attendees: list[str] = field(default_factory=list)  # Email addresses
    organizer: Optional[str] = None

    # Status
    status: Literal["confirmed", "tentative", "cancelled"] = "confirmed"

    # Reminders
    reminders: list[int] = field(default_factory=list)  # Minutes before event

    # Metadata
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    # External reference
    remote_id: Optional[str] = None  # External provider event ID


@dataclass
class CreateEventRequest:
    """Request to create a calendar event."""
    calendar_id: str
    summary: str
    start: datetime | date
    end: datetime | date
    description: Optional[str] = None
    location: Optional[str] = None
    all_day: bool = False
    timezone: str = "Europe/Paris"
    attendees: list[str] = field(default_factory=list)
    recurrence: Optional[list[str]] = None
    reminders: list[int] = field(default_factory=lambda: [30])  # Default 30 min reminder


@dataclass
class UpdateEventRequest:
    """Request to update a calendar event."""
    summary: Optional[str] = None
    start: Optional[datetime | date] = None
    end: Optional[datetime | date] = None
    description: Optional[str] = None
    location: Optional[str] = None
    all_day: Optional[bool] = None
    timezone: Optional[str] = None
    attendees: Optional[list[str]] = None
    recurrence: Optional[list[str]] = None
    status: Optional[Literal["confirmed", "tentative", "cancelled"]] = None
    reminders: Optional[list[int]] = None


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
        description: Optional[str] = None,
        timezone: str = "Europe/Paris",
        color: Optional[str] = None,
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
        name: Optional[str] = None,
        description: Optional[str] = None,
        timezone: Optional[str] = None,
        color: Optional[str] = None,
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
        time_min: Optional[datetime] = None,
        time_max: Optional[datetime] = None,
        max_results: int = 100,
        page_token: Optional[str] = None,
    ) -> tuple[list[CalendarEventDTO], Optional[str]]:
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
