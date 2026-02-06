"""
THÉRÈSE v2 - Schemas Calendar (Local First)

Request/Response models pour les calendriers locaux et CalDAV.
"""

from pydantic import BaseModel


class LocalCalendarCreateRequest(BaseModel):
    """Create a local calendar (no external account needed)."""

    summary: str
    description: str | None = None
    timezone: str = "Europe/Paris"


class CalDAVSetupRequest(BaseModel):
    """Setup a CalDAV calendar connection."""

    url: str
    username: str
    password: str


class CalDAVTestRequest(BaseModel):
    """Test CalDAV connection."""

    url: str
    username: str
    password: str
