"""
THERESE v2 - Calendar Services Package

Multi-provider calendar support (Local SQLite, Google Calendar, CalDAV).
Part of the "Local First" architecture.
"""

from app.services.calendar.base_provider import (
    CalendarProvider,
    CalendarDTO,
    CalendarEventDTO,
    CreateEventRequest,
    UpdateEventRequest,
)
from app.services.calendar.provider_factory import (
    get_calendar_provider,
    CalendarProviderType,
)

__all__ = [
    "CalendarProvider",
    "CalendarDTO",
    "CalendarEventDTO",
    "CreateEventRequest",
    "UpdateEventRequest",
    "get_calendar_provider",
    "CalendarProviderType",
]
