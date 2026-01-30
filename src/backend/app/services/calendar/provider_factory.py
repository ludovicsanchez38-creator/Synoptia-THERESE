"""
THERESE v2 - Calendar Provider Factory

Factory pattern for creating calendar providers based on configuration.
Part of the "Local First" architecture.
"""

import logging
from typing import Literal, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.calendar.base_provider import CalendarProvider
from app.services.calendar.local_provider import LocalCalendarProvider
from app.services.calendar.google_provider import GoogleCalendarProvider
from app.services.calendar.caldav_provider import CalDAVProvider

logger = logging.getLogger(__name__)


CalendarProviderType = Literal["local", "google", "caldav"]


def get_calendar_provider(
    provider_type: CalendarProviderType,
    # Local provider
    session: Optional[AsyncSession] = None,
    # Google OAuth
    access_token: Optional[str] = None,
    # CalDAV config
    caldav_url: Optional[str] = None,
    caldav_username: Optional[str] = None,
    caldav_password: Optional[str] = None,
) -> CalendarProvider:
    """
    Create a calendar provider based on configuration.

    Args:
        provider_type: Type of provider ('local', 'google', 'caldav')

        For Local:
            session: AsyncSession for database access

        For Google:
            access_token: OAuth2 access token

        For CalDAV:
            caldav_url: CalDAV server URL
            caldav_username: Username
            caldav_password: Password

    Returns:
        CalendarProvider instance

    Raises:
        ValueError: If required parameters are missing
    """
    if provider_type == "local":
        if not session:
            raise ValueError("Local provider requires session")
        return LocalCalendarProvider(session=session)

    elif provider_type == "google":
        if not access_token:
            raise ValueError("Google provider requires access_token")
        return GoogleCalendarProvider(access_token=access_token)

    elif provider_type == "caldav":
        if not caldav_url or not caldav_username or not caldav_password:
            raise ValueError("CalDAV provider requires url, username, and password")
        return CalDAVProvider(
            url=caldav_url,
            username=caldav_username,
            password=caldav_password,
        )

    else:
        raise ValueError(f"Unknown provider type: {provider_type}")


# Common CalDAV server configurations
CALDAV_PRESETS = {
    "nextcloud": {
        "url_template": "https://{host}/remote.php/dav",
        "note": "Replace {host} with your Nextcloud domain",
    },
    "icloud": {
        "url_template": "https://caldav.icloud.com",
        "note": "Use Apple ID and app-specific password",
    },
    "fastmail": {
        "url_template": "https://caldav.fastmail.com/dav/calendars/user/{username}@fastmail.com/",
        "note": "Use Fastmail app password",
    },
    "google-caldav": {
        "url_template": "https://www.google.com/calendar/dav/{calendar_id}/events",
        "note": "Limited CalDAV support, prefer Google Calendar API",
    },
    "calcom": {
        "url_template": "https://app.cal.com/dav/{username}",
        "note": "cal.com CalDAV access",
    },
    "radicale": {
        "url_template": "http://{host}:{port}/",
        "note": "Self-hosted Radicale server",
    },
    "baikal": {
        "url_template": "https://{host}/dav.php",
        "note": "Baikal CalDAV server",
    },
    "synology": {
        "url_template": "https://{host}:5001/caldav/{username}",
        "note": "Synology NAS CalDAV",
    },
    "zimbra": {
        "url_template": "https://{host}/dav/{email}/Calendar",
        "note": "Zimbra CalDAV endpoint",
    },
}


def get_caldav_preset(preset_name: str) -> dict:
    """
    Get pre-configured CalDAV settings for common providers.

    Args:
        preset_name: Name of the provider preset

    Returns:
        Dict with URL template and notes

    Raises:
        KeyError: If preset is not found
    """
    return CALDAV_PRESETS[preset_name.lower()]


def list_caldav_presets() -> list[dict]:
    """
    List all pre-configured CalDAV providers.

    Returns:
        List of preset configs with names
    """
    return [
        {"name": name, **config}
        for name, config in CALDAV_PRESETS.items()
    ]


async def test_caldav_connection(
    url: str,
    username: str,
    password: str,
) -> dict:
    """
    Test CalDAV connection and return server info.

    Args:
        url: CalDAV server URL
        username: Username
        password: Password

    Returns:
        Dict with connection status and discovered calendars
    """
    try:
        provider = CalDAVProvider(url=url, username=username, password=password)
        calendars = await provider.list_calendars()

        return {
            "success": True,
            "message": f"Connected successfully. Found {len(calendars)} calendar(s).",
            "calendars": [
                {"id": cal.id, "name": cal.name}
                for cal in calendars
            ],
        }
    except Exception as e:
        logger.error(f"CalDAV connection test failed: {e}")
        return {
            "success": False,
            "message": f"Connection failed: {str(e)}",
            "calendars": [],
        }
