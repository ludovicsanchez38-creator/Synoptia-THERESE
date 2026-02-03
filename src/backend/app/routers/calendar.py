"""
THÉRÈSE v2 - Calendar Router

API endpoints pour la gestion calendrier.
Supporte Local (SQLite), Google Calendar (OAuth), CalDAV (Nextcloud, iCloud, etc.)

Phase 2 - Calendar
Local First - Multi-Provider
"""

import logging
import json
from datetime import UTC, datetime
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.calendar_service import CalendarService
from app.services.encryption import decrypt_value, encrypt_value, is_value_encrypted
from app.models.entities import EmailAccount, Calendar, CalendarEvent, generate_uuid
from app.models.schemas import (
    CalendarResponse,
    CalendarEventResponse,
    CreateEventRequest,
    UpdateEventRequest,
    ListEventsRequest,
    QuickAddEventRequest,
    CalendarSyncResponse,
)
from app.models.database import get_session
from app.services.calendar.provider_factory import (
    get_calendar_provider,
    list_caldav_presets,
    test_caldav_connection,
)
from app.routers.email import ensure_valid_access_token

router = APIRouter()
logger = logging.getLogger(__name__)


# ============================================================
# Local First Schemas
# ============================================================


class LocalCalendarCreateRequest(BaseModel):
    """Create a local calendar (no external account needed)."""
    summary: str
    description: Optional[str] = None
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


# ============================================================
# Helper Functions
# ============================================================


async def _get_provider_for_calendar(
    calendar: Calendar,
    session: AsyncSession,
):
    """
    Get the correct CalendarProvider based on calendar's provider type.

    Returns the provider instance ready to use.
    """
    if calendar.provider == "local":
        return get_calendar_provider(
            provider_type="local",
            session=session,
        )
    elif calendar.provider == "google":
        # Get account and ensure valid token (refresh if expired)
        account = await session.get(EmailAccount, calendar.account_id)
        if not account:
            raise HTTPException(status_code=404, detail="Account not found for Google calendar")
        access_token = await ensure_valid_access_token(account, session)
        return get_calendar_provider(
            provider_type="google",
            access_token=access_token,
        )
    elif calendar.provider == "caldav":
        return get_calendar_provider(
            provider_type="caldav",
            caldav_url=calendar.caldav_url,
            caldav_username=calendar.caldav_username,
            caldav_password=(
                decrypt_value(calendar.caldav_password)
                if calendar.caldav_password and is_value_encrypted(calendar.caldav_password)
                else calendar.caldav_password
            ),
        )
    else:
        raise HTTPException(status_code=400, detail=f"Provider inconnu: {calendar.provider}")


# =============================================================================
# LOCAL FIRST - CALENDARS
# =============================================================================


@router.get("/calendars")
async def list_calendars(
    account_id: Optional[str] = Query(None, description="Email account ID (optional for local calendars)"),
    provider: Optional[str] = Query(None, description="Filter by provider: local, google, caldav"),
    session: AsyncSession = Depends(get_session),
) -> List[CalendarResponse]:
    """
    Liste tous les calendriers.

    - Sans account_id : retourne les calendriers locaux + tous les calendriers en DB
    - Avec account_id : sync Google Calendar et retourne les calendriers du compte
    - Avec provider : filtre par type de provider
    """
    # If account_id provided and it's a Google account, sync from Google
    if account_id:
        account = await session.get(EmailAccount, account_id)
        if account and account.provider == "gmail":
            return await _list_google_calendars(account_id, account, session)

    # Otherwise, list from database (local + cached Google + CalDAV)
    statement = select(Calendar)
    if provider:
        statement = statement.where(Calendar.provider == provider)
    if account_id:
        statement = statement.where(Calendar.account_id == account_id)

    result = await session.execute(statement)
    calendars = result.scalars().all()

    return [
        CalendarResponse(
            id=cal.id,
            account_id=cal.account_id,
            summary=cal.summary,
            description=cal.description,
            timezone=cal.timezone,
            primary=cal.primary,
            synced_at=cal.synced_at.isoformat() if cal.synced_at else None,
        )
        for cal in calendars
    ]


async def _list_google_calendars(
    account_id: str,
    account: EmailAccount,
    session: AsyncSession,
) -> List[CalendarResponse]:
    """Sync and list Google Calendar calendars."""
    access_token = await ensure_valid_access_token(account, session)

    try:
        calendar_service = CalendarService(access_token)
        calendars_data = await calendar_service.list_calendars()

        calendars = []
        for cal_data in calendars_data:
            cal_id = cal_data["id"]
            existing_cal = await session.get(Calendar, cal_id)

            if existing_cal:
                existing_cal.summary = cal_data.get("summary", "")
                existing_cal.description = cal_data.get("description")
                existing_cal.timezone = cal_data.get("timeZone", "UTC")
                existing_cal.primary = cal_data.get("primary", False)
                existing_cal.provider = "google"
                existing_cal.synced_at = datetime.now(UTC)
                session.add(existing_cal)
                calendars.append(existing_cal)
            else:
                new_cal = Calendar(
                    id=cal_id,
                    account_id=account_id,
                    summary=cal_data.get("summary", ""),
                    description=cal_data.get("description"),
                    timezone=cal_data.get("timeZone", "UTC"),
                    primary=cal_data.get("primary", False),
                    provider="google",
                    remote_id=cal_id,
                    synced_at=datetime.now(UTC),
                )
                session.add(new_cal)
                calendars.append(new_cal)

        await session.commit()

        return [
            CalendarResponse(
                id=cal.id,
                account_id=cal.account_id,
                summary=cal.summary,
                description=cal.description,
                timezone=cal.timezone,
                primary=cal.primary,
                synced_at=cal.synced_at.isoformat() if cal.synced_at else None,
            )
            for cal in calendars
        ]

    except Exception as e:
        logger.error(f"Failed to list Google calendars: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/calendars/{calendar_id}")
async def get_calendar(
    calendar_id: str,
    account_id: str = Query(...),
    session: AsyncSession = Depends(get_session),
) -> CalendarResponse:
    """Récupère un calendrier spécifique."""
    calendar = await session.get(Calendar, calendar_id)
    if not calendar or calendar.account_id != account_id:
        raise HTTPException(status_code=404, detail="Calendar not found")

    return CalendarResponse(
        id=calendar.id,
        account_id=calendar.account_id,
        summary=calendar.summary,
        description=calendar.description,
        timezone=calendar.timezone,
        primary=calendar.primary,
        synced_at=calendar.synced_at.isoformat(),
    )


@router.post("/calendars")
async def create_calendar(
    account_id: Optional[str] = None,
    summary: str = "Mon calendrier",
    description: Optional[str] = None,
    timezone: str = "Europe/Paris",
    provider_type: str = Query("local", description="Provider: local, google, caldav"),
    session: AsyncSession = Depends(get_session),
) -> CalendarResponse:
    """
    Cree un nouveau calendrier.

    - provider_type=local : Calendrier local SQLite (pas besoin d'account_id)
    - provider_type=google : Calendrier Google Calendar (account_id requis)
    - provider_type=caldav : Voir POST /calendars/caldav-setup
    """
    if provider_type == "local":
        # Local calendar - no external account needed
        provider = get_calendar_provider(provider_type="local", session=session)
        cal_dto = await provider.create_calendar(
            name=summary,
            description=description,
            timezone=timezone,
        )
        # The local provider already saved to DB, fetch the entity
        calendar = await session.get(Calendar, cal_dto.id)
        return CalendarResponse(
            id=cal_dto.id,
            account_id=None,
            summary=cal_dto.name,
            description=cal_dto.description,
            timezone=cal_dto.timezone,
            primary=cal_dto.is_primary,
            synced_at=datetime.now(UTC).isoformat(),
        )

    elif provider_type == "google":
        if not account_id:
            raise HTTPException(status_code=400, detail="account_id requis pour Google Calendar")

        account = await session.get(EmailAccount, account_id)
        if not account:
            raise HTTPException(status_code=404, detail="Account not found")

        access_token = (
            decrypt_value(account.access_token)
            if account.access_token and is_value_encrypted(account.access_token)
            else account.access_token
        )

        try:
            calendar_service = CalendarService(access_token)
            cal_data = await calendar_service.create_calendar(summary, description, timezone)

            new_cal = Calendar(
                id=cal_data["id"],
                account_id=account_id,
                summary=cal_data["summary"],
                description=cal_data.get("description"),
                timezone=cal_data.get("timeZone", timezone),
                primary=False,
                provider="google",
                remote_id=cal_data["id"],
                synced_at=datetime.now(UTC),
            )
            session.add(new_cal)
            await session.commit()
            await session.refresh(new_cal)

            return CalendarResponse(
                id=new_cal.id,
                account_id=new_cal.account_id,
                summary=new_cal.summary,
                description=new_cal.description,
                timezone=new_cal.timezone,
                primary=new_cal.primary,
                synced_at=new_cal.synced_at.isoformat() if new_cal.synced_at else None,
            )

        except Exception as e:
            logger.error(f"Failed to create Google calendar: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    else:
        raise HTTPException(status_code=400, detail=f"Pour CalDAV, utilisez POST /calendars/caldav-setup")


@router.delete("/calendars/{calendar_id}")
async def delete_calendar(
    calendar_id: str,
    account_id: str = Query(...),
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Supprime un calendrier."""
    calendar = await session.get(Calendar, calendar_id)
    if not calendar or calendar.account_id != account_id:
        raise HTTPException(status_code=404, detail="Calendar not found")

    account = await session.get(EmailAccount, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    access_token = (
        decrypt_value(account.access_token)
        if is_value_encrypted(account.access_token)
        else account.access_token
    )

    try:
        calendar_service = CalendarService(access_token)
        await calendar_service.delete_calendar(calendar_id)

        # Delete from DB (cascade events)
        await session.delete(calendar)
        await session.commit()

        return {"success": True, "message": "Calendar deleted"}

    except Exception as e:
        logger.error(f"Failed to delete calendar: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# CALDAV SETUP (Local First)
# =============================================================================


@router.post("/calendars/caldav-setup")
async def setup_caldav_calendar(
    request: CalDAVSetupRequest,
    session: AsyncSession = Depends(get_session),
) -> List[CalendarResponse]:
    """
    Configure un serveur CalDAV et importe les calendriers decouverts.

    Compatible: Nextcloud, iCloud, Fastmail, cal.com, Radicale, Baikal, etc.
    """
    # Test connection first
    test_result = await test_caldav_connection(
        url=request.url,
        username=request.username,
        password=request.password,
    )

    if not test_result["success"]:
        raise HTTPException(status_code=400, detail=test_result["message"])

    # Import discovered calendars
    calendars = []
    for cal_info in test_result["calendars"]:
        # Check if already exists
        statement = select(Calendar).where(
            Calendar.provider == "caldav",
            Calendar.remote_id == cal_info["id"],
        )
        result = await session.execute(statement)
        existing = result.scalar_one_or_none()

        if existing:
            existing.caldav_url = request.url
            existing.caldav_username = request.username
            existing.caldav_password = encrypt_value(request.password)
            existing.summary = cal_info["name"] or existing.summary
            existing.sync_status = "idle"
            existing.synced_at = datetime.now(UTC)
            session.add(existing)
            calendars.append(existing)
        else:
            new_cal = Calendar(
                id=generate_uuid(),
                summary=cal_info["name"] or "Calendrier CalDAV",
                provider="caldav",
                remote_id=cal_info["id"],
                caldav_url=request.url,
                caldav_username=request.username,
                caldav_password=encrypt_value(request.password),
                sync_status="idle",
                synced_at=datetime.now(UTC),
            )
            session.add(new_cal)
            calendars.append(new_cal)

    await session.commit()

    logger.info(f"CalDAV setup: {len(calendars)} calendrier(s) importe(s)")

    return [
        CalendarResponse(
            id=cal.id,
            account_id=cal.account_id,
            summary=cal.summary,
            description=cal.description,
            timezone=cal.timezone,
            primary=cal.primary,
            synced_at=cal.synced_at.isoformat() if cal.synced_at else None,
        )
        for cal in calendars
    ]


@router.post("/calendars/caldav-test")
async def test_caldav(
    request: CalDAVTestRequest,
) -> dict:
    """
    Teste une connexion CalDAV sans sauvegarder.

    Retourne les calendriers decouverts.
    """
    result = await test_caldav_connection(
        url=request.url,
        username=request.username,
        password=request.password,
    )
    return result


@router.get("/caldav-presets")
async def get_caldav_presets() -> list[dict]:
    """
    Liste les presets CalDAV preconfigures.

    Retourne les configurations pour Nextcloud, iCloud, Fastmail, cal.com, etc.
    """
    return list_caldav_presets()


# =============================================================================
# EVENTS MANAGEMENT
# =============================================================================


@router.get("/events")
async def list_events(
    calendar_id: str = Query(default="primary"),
    account_id: Optional[str] = Query(None),
    time_min: Optional[str] = None,
    time_max: Optional[str] = None,
    max_results: int = Query(default=50, le=250),
    session: AsyncSession = Depends(get_session),
) -> List[CalendarEventResponse]:
    """
    Liste les evenements d'un calendrier (local, Google ou CalDAV).

    - Pour les calendriers locaux : pas besoin d'account_id
    - Pour Google Calendar : account_id requis
    - Pour CalDAV : pas besoin d'account_id (credentials dans le calendrier)
    """
    # Get calendar from DB to determine provider
    calendar = await session.get(Calendar, calendar_id)

    if calendar and calendar.provider in ("local", "caldav"):
        return await _list_events_provider(calendar, session, time_min, time_max, max_results)
    else:
        # Google Calendar (legacy flow or explicit)
        if not account_id:
            raise HTTPException(status_code=400, detail="account_id requis pour Google Calendar")
        return await _list_events_google(
            account_id, calendar_id, session, time_min, time_max, max_results
        )


async def _list_events_provider(
    calendar: Calendar,
    session: AsyncSession,
    time_min: Optional[str],
    time_max: Optional[str],
    max_results: int,
) -> List[CalendarEventResponse]:
    """List events via abstract CalendarProvider (local or CalDAV)."""
    provider = await _get_provider_for_calendar(calendar, session)

    def _parse_dt_naive(s: str) -> datetime:
        """Parse ISO datetime string to naive UTC datetime."""
        # URL query params decode '+' as space, so restore it
        s = s.replace(" 00:00", "+00:00").replace("Z", "+00:00")
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is not None:
            dt = dt.replace(tzinfo=None)
        return dt

    dt_min = _parse_dt_naive(time_min) if time_min else None
    dt_max = _parse_dt_naive(time_max) if time_max else None

    events_dto, _ = await provider.list_events(
        calendar_id=calendar.id,
        time_min=dt_min,
        time_max=dt_max,
        max_results=max_results,
    )

    # Convert DTOs to CalendarEventResponse
    return [
        CalendarEventResponse(
            id=evt.id,
            calendar_id=evt.calendar_id,
            summary=evt.summary,
            description=evt.description,
            location=evt.location,
            start_datetime=evt.start.isoformat() if isinstance(evt.start, datetime) else None,
            end_datetime=evt.end.isoformat() if isinstance(evt.end, datetime) else None,
            start_date=evt.start.isoformat() if evt.all_day and evt.start else None,
            end_date=evt.end.isoformat() if evt.all_day and evt.end else None,
            all_day=evt.all_day,
            attendees=evt.attendees,
            recurrence=evt.recurrence,
            status=evt.status,
            synced_at=datetime.now(UTC).isoformat(),
        )
        for evt in events_dto
    ]


async def _list_events_google(
    account_id: str,
    calendar_id: str,
    session: AsyncSession,
    time_min: Optional[str],
    time_max: Optional[str],
    max_results: int,
) -> List[CalendarEventResponse]:
    """List events via Google Calendar API (legacy flow)."""
    account = await session.get(EmailAccount, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    access_token = (
        decrypt_value(account.access_token)
        if account.access_token and is_value_encrypted(account.access_token)
        else account.access_token
    )

    try:
        calendar_service = CalendarService(access_token)

        dt_min = datetime.fromisoformat(time_min.replace("Z", "")) if time_min else None
        dt_max = datetime.fromisoformat(time_max.replace("Z", "")) if time_max else None

        events_data = await calendar_service.list_events(
            calendar_id, dt_min, dt_max, max_results
        )

        # Sync to DB
        events = []
        for event_data in events_data.get("items", []):
            event_id = event_data["id"]
            existing_event = await session.get(CalendarEvent, event_id)

            start_obj = event_data.get("start", {})
            end_obj = event_data.get("end", {})
            all_day = "date" in start_obj

            if existing_event:
                existing_event.summary = event_data.get("summary", "")
                existing_event.description = event_data.get("description")
                existing_event.location = event_data.get("location")
                if all_day:
                    existing_event.start_date = start_obj.get("date")
                    existing_event.end_date = end_obj.get("date")
                else:
                    existing_event.start_datetime = datetime.fromisoformat(
                        start_obj["dateTime"].replace("Z", "")
                    )
                    existing_event.end_datetime = datetime.fromisoformat(
                        end_obj["dateTime"].replace("Z", "")
                    )
                existing_event.all_day = all_day
                existing_event.attendees = json.dumps(
                    [a["email"] for a in event_data.get("attendees", [])]
                )
                existing_event.recurrence = json.dumps(event_data.get("recurrence", []))
                existing_event.status = event_data.get("status", "confirmed")
                existing_event.synced_at = datetime.now(UTC)
                session.add(existing_event)
                events.append(existing_event)
            else:
                new_event = CalendarEvent(
                    id=event_id,
                    calendar_id=calendar_id,
                    summary=event_data.get("summary", ""),
                    description=event_data.get("description"),
                    location=event_data.get("location"),
                    start_date=start_obj.get("date") if all_day else None,
                    end_date=end_obj.get("date") if all_day else None,
                    start_datetime=(
                        datetime.fromisoformat(start_obj["dateTime"].replace("Z", ""))
                        if not all_day
                        else None
                    ),
                    end_datetime=(
                        datetime.fromisoformat(end_obj["dateTime"].replace("Z", ""))
                        if not all_day
                        else None
                    ),
                    all_day=all_day,
                    attendees=json.dumps(
                        [a["email"] for a in event_data.get("attendees", [])]
                    ),
                    recurrence=json.dumps(event_data.get("recurrence", [])),
                    status=event_data.get("status", "confirmed"),
                    synced_at=datetime.now(UTC),
                )
                session.add(new_event)
                events.append(new_event)

        await session.commit()

        return [
            CalendarEventResponse(
                id=event.id,
                calendar_id=event.calendar_id,
                summary=event.summary,
                description=event.description,
                location=event.location,
                start_datetime=event.start_datetime.isoformat() if event.start_datetime else None,
                end_datetime=event.end_datetime.isoformat() if event.end_datetime else None,
                start_date=event.start_date,
                end_date=event.end_date,
                all_day=event.all_day,
                attendees=json.loads(event.attendees) if event.attendees else None,
                recurrence=json.loads(event.recurrence) if event.recurrence else None,
                status=event.status,
                synced_at=event.synced_at.isoformat() if event.synced_at else None,
            )
            for event in events
        ]

    except Exception as e:
        logger.error(f"Failed to list events: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/events/{event_id}")
async def get_event(
    event_id: str,
    calendar_id: str = Query(default="primary"),
    account_id: str = Query(...),
    session: AsyncSession = Depends(get_session),
) -> CalendarEventResponse:
    """Récupère un événement spécifique."""
    event = await session.get(CalendarEvent, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    return CalendarEventResponse(
        id=event.id,
        calendar_id=event.calendar_id,
        summary=event.summary,
        description=event.description,
        location=event.location,
        start_datetime=event.start_datetime.isoformat() if event.start_datetime else None,
        end_datetime=event.end_datetime.isoformat() if event.end_datetime else None,
        start_date=event.start_date,
        end_date=event.end_date,
        all_day=event.all_day,
        attendees=json.loads(event.attendees) if event.attendees else None,
        recurrence=json.loads(event.recurrence) if event.recurrence else None,
        status=event.status,
        synced_at=event.synced_at.isoformat(),
    )


@router.post("/events")
async def create_event(
    request: CreateEventRequest,
    account_id: Optional[str] = Query(None),
    session: AsyncSession = Depends(get_session),
) -> CalendarEventResponse:
    """
    Cree un nouvel evenement (local, Google ou CalDAV).

    Pour les calendriers locaux/CalDAV, account_id est optionnel.
    """
    # Determine provider from calendar
    calendar = await session.get(Calendar, request.calendar_id)

    if calendar and calendar.provider in ("local", "caldav"):
        return await _create_event_provider(calendar, request, session)
    else:
        return await _create_event_google(account_id, request, session)


async def _create_event_provider(
    calendar: Calendar,
    request: CreateEventRequest,
    session: AsyncSession,
) -> CalendarEventResponse:
    """Create event via abstract CalendarProvider."""
    from app.services.calendar.base_provider import CreateEventRequest as ProviderCreateRequest

    provider = await _get_provider_for_calendar(calendar, session)

    # Build provider request
    all_day = bool(request.start_date and request.end_date)
    if all_day:
        start = datetime.strptime(request.start_date, "%Y-%m-%d").date()
        end = datetime.strptime(request.end_date, "%Y-%m-%d").date()
    else:
        start = datetime.fromisoformat(request.start_datetime.replace("Z", "")) if request.start_datetime else datetime.now(UTC)
        end = datetime.fromisoformat(request.end_datetime.replace("Z", "")) if request.end_datetime else datetime.now(UTC)

    provider_req = ProviderCreateRequest(
        calendar_id=request.calendar_id,
        summary=request.summary,
        description=request.description,
        location=request.location,
        start=start,
        end=end,
        all_day=all_day,
        attendees=request.attendees or [],
        recurrence=request.recurrence,
    )

    evt = await provider.create_event(provider_req)

    return CalendarEventResponse(
        id=evt.id,
        calendar_id=evt.calendar_id,
        summary=evt.summary,
        description=evt.description,
        location=evt.location,
        start_datetime=evt.start.isoformat() if isinstance(evt.start, datetime) else None,
        end_datetime=evt.end.isoformat() if isinstance(evt.end, datetime) else None,
        start_date=evt.start.isoformat() if evt.all_day and evt.start else None,
        end_date=evt.end.isoformat() if evt.all_day and evt.end else None,
        all_day=evt.all_day,
        attendees=evt.attendees,
        recurrence=evt.recurrence,
        status=evt.status,
        synced_at=datetime.now(UTC).isoformat(),
    )


async def _create_event_google(
    account_id: Optional[str],
    request: CreateEventRequest,
    session: AsyncSession,
) -> CalendarEventResponse:
    """Create event via Google Calendar API."""
    if not account_id:
        raise HTTPException(status_code=400, detail="account_id requis pour Google Calendar")

    account = await session.get(EmailAccount, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    access_token = (
        decrypt_value(account.access_token)
        if account.access_token and is_value_encrypted(account.access_token)
        else account.access_token
    )

    try:
        calendar_service = CalendarService(access_token)

        if request.start_datetime and request.end_datetime:
            start = {"dateTime": request.start_datetime}
            end = {"dateTime": request.end_datetime}
        elif request.start_date and request.end_date:
            start = {"date": request.start_date}
            end = {"date": request.end_date}
        else:
            raise HTTPException(
                status_code=400,
                detail="Must provide either start_datetime/end_datetime or start_date/end_date",
            )

        event_data = await calendar_service.create_event(
            calendar_id=request.calendar_id,
            summary=request.summary,
            start=start,
            end=end,
            description=request.description,
            location=request.location,
            attendees=request.attendees,
            recurrence=request.recurrence,
        )

        all_day = "date" in event_data.get("start", {})
        start_obj = event_data["start"]
        end_obj = event_data["end"]

        new_event = CalendarEvent(
            id=event_data["id"],
            calendar_id=request.calendar_id,
            summary=event_data["summary"],
            description=event_data.get("description"),
            location=event_data.get("location"),
            start_date=start_obj.get("date") if all_day else None,
            end_date=end_obj.get("date") if all_day else None,
            start_datetime=(
                datetime.fromisoformat(start_obj["dateTime"].replace("Z", ""))
                if not all_day
                else None
            ),
            end_datetime=(
                datetime.fromisoformat(end_obj["dateTime"].replace("Z", ""))
                if not all_day
                else None
            ),
            all_day=all_day,
            attendees=json.dumps(request.attendees or []),
            recurrence=json.dumps(request.recurrence or []),
            status=event_data.get("status", "confirmed"),
            synced_at=datetime.now(UTC),
        )
        session.add(new_event)
        await session.commit()
        await session.refresh(new_event)

        return CalendarEventResponse(
            id=new_event.id,
            calendar_id=new_event.calendar_id,
            summary=new_event.summary,
            description=new_event.description,
            location=new_event.location,
            start_datetime=new_event.start_datetime.isoformat()
            if new_event.start_datetime
            else None,
            end_datetime=new_event.end_datetime.isoformat() if new_event.end_datetime else None,
            start_date=new_event.start_date,
            end_date=new_event.end_date,
            all_day=new_event.all_day,
            attendees=json.loads(new_event.attendees) if new_event.attendees else None,
            recurrence=json.loads(new_event.recurrence) if new_event.recurrence else None,
            status=new_event.status,
            synced_at=new_event.synced_at.isoformat() if new_event.synced_at else None,
        )

    except Exception as e:
        logger.error(f"Failed to create event: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/events/{event_id}")
async def update_event(
    event_id: str,
    request: UpdateEventRequest,
    calendar_id: str = Query(default="primary"),
    account_id: Optional[str] = Query(None),
    session: AsyncSession = Depends(get_session),
) -> CalendarEventResponse:
    """Met a jour un evenement (local, Google ou CalDAV)."""
    # Check if calendar is local/CalDAV
    calendar = await session.get(Calendar, calendar_id)

    if calendar and calendar.provider in ("local", "caldav"):
        from app.services.calendar.base_provider import UpdateEventRequest as ProviderUpdateRequest

        provider = await _get_provider_for_calendar(calendar, session)

        # Build provider update request
        start = None
        end = None
        all_day = None

        if request.start_datetime:
            start = datetime.fromisoformat(request.start_datetime.replace("Z", ""))
        elif request.start_date:
            start = datetime.strptime(request.start_date, "%Y-%m-%d").date()
            all_day = True

        if request.end_datetime:
            end = datetime.fromisoformat(request.end_datetime.replace("Z", ""))
        elif request.end_date:
            end = datetime.strptime(request.end_date, "%Y-%m-%d").date()
            all_day = True

        provider_req = ProviderUpdateRequest(
            summary=request.summary,
            description=request.description,
            location=request.location,
            start=start,
            end=end,
            all_day=all_day,
            attendees=request.attendees,
            recurrence=request.recurrence,
        )

        evt = await provider.update_event(calendar_id, event_id, provider_req)

        return CalendarEventResponse(
            id=evt.id,
            calendar_id=evt.calendar_id,
            summary=evt.summary,
            description=evt.description,
            location=evt.location,
            start_datetime=evt.start.isoformat() if isinstance(evt.start, datetime) else None,
            end_datetime=evt.end.isoformat() if isinstance(evt.end, datetime) else None,
            start_date=evt.start.isoformat() if evt.all_day and evt.start else None,
            end_date=evt.end.isoformat() if evt.all_day and evt.end else None,
            all_day=evt.all_day,
            attendees=evt.attendees,
            recurrence=evt.recurrence,
            status=evt.status,
            synced_at=datetime.now(UTC).isoformat(),
        )

    # Google Calendar
    if not account_id:
        raise HTTPException(status_code=400, detail="account_id requis pour Google Calendar")

    account = await session.get(EmailAccount, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    access_token = (
        decrypt_value(account.access_token)
        if account.access_token and is_value_encrypted(account.access_token)
        else account.access_token
    )

    try:
        calendar_service = CalendarService(access_token)

        start = (
            {"dateTime": request.start_datetime}
            if request.start_datetime
            else ({"date": request.start_date} if request.start_date else None)
        )
        end = (
            {"dateTime": request.end_datetime}
            if request.end_datetime
            else ({"date": request.end_date} if request.end_date else None)
        )

        event_data = await calendar_service.update_event(
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

        db_event = await session.get(CalendarEvent, event_id)
        if db_event:
            all_day_flag = "date" in event_data.get("start", {})
            start_obj = event_data["start"]
            end_obj = event_data["end"]

            db_event.summary = event_data["summary"]
            db_event.description = event_data.get("description")
            db_event.location = event_data.get("location")
            if all_day_flag:
                db_event.start_date = start_obj.get("date")
                db_event.end_date = end_obj.get("date")
            else:
                db_event.start_datetime = datetime.fromisoformat(
                    start_obj["dateTime"].replace("Z", "")
                )
                db_event.end_datetime = datetime.fromisoformat(
                    end_obj["dateTime"].replace("Z", "")
                )
            db_event.all_day = all_day_flag
            db_event.attendees = json.dumps(
                [a["email"] for a in event_data.get("attendees", [])]
            )
            db_event.recurrence = json.dumps(event_data.get("recurrence", []))
            db_event.status = event_data.get("status", "confirmed")
            db_event.synced_at = datetime.now(UTC)
            session.add(db_event)
            await session.commit()
            await session.refresh(db_event)

        return CalendarEventResponse(
            id=db_event.id,
            calendar_id=db_event.calendar_id,
            summary=db_event.summary,
            description=db_event.description,
            location=db_event.location,
            start_datetime=db_event.start_datetime.isoformat()
            if db_event.start_datetime
            else None,
            end_datetime=db_event.end_datetime.isoformat() if db_event.end_datetime else None,
            start_date=db_event.start_date,
            end_date=db_event.end_date,
            all_day=db_event.all_day,
            attendees=json.loads(db_event.attendees) if db_event.attendees else None,
            recurrence=json.loads(db_event.recurrence) if db_event.recurrence else None,
            status=db_event.status,
            synced_at=db_event.synced_at.isoformat() if db_event.synced_at else None,
        )

    except Exception as e:
        logger.error(f"Failed to update event: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/events/{event_id}")
async def delete_event(
    event_id: str,
    calendar_id: str = Query(default="primary"),
    account_id: Optional[str] = Query(None),
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Supprime un evenement (local, Google ou CalDAV)."""
    # Check if calendar is local/CalDAV
    calendar = await session.get(Calendar, calendar_id)

    if calendar and calendar.provider in ("local", "caldav"):
        provider = await _get_provider_for_calendar(calendar, session)
        await provider.delete_event(calendar_id, event_id)
        return {"success": True, "message": "Evenement supprime"}

    # Google Calendar
    if not account_id:
        raise HTTPException(status_code=400, detail="account_id requis pour Google Calendar")

    account = await session.get(EmailAccount, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    access_token = (
        decrypt_value(account.access_token)
        if account.access_token and is_value_encrypted(account.access_token)
        else account.access_token
    )

    try:
        calendar_service = CalendarService(access_token)
        await calendar_service.delete_event(calendar_id, event_id)

        db_event = await session.get(CalendarEvent, event_id)
        if db_event:
            await session.delete(db_event)
            await session.commit()

        return {"success": True, "message": "Evenement supprime"}

    except Exception as e:
        logger.error(f"Failed to delete event: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/events/quick-add")
async def quick_add_event(
    request: QuickAddEventRequest,
    account_id: str = Query(...),
    session: AsyncSession = Depends(get_session),
) -> CalendarEventResponse:
    """
    Ajoute un événement via parsing texte naturel.
    Ex: "Déjeuner avec Pierre demain à 12h30"
    """
    account = await session.get(EmailAccount, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    access_token = (
        decrypt_value(account.access_token)
        if is_value_encrypted(account.access_token)
        else account.access_token
    )

    try:
        calendar_service = CalendarService(access_token)
        event_data = await calendar_service.quick_add_event(request.calendar_id, request.text)

        # Save to DB (simplified, same logic as create_event)
        all_day = "date" in event_data.get("start", {})
        start_obj = event_data["start"]
        end_obj = event_data["end"]

        new_event = CalendarEvent(
            id=event_data["id"],
            calendar_id=request.calendar_id,
            summary=event_data["summary"],
            description=event_data.get("description"),
            location=event_data.get("location"),
            start_date=start_obj.get("date") if all_day else None,
            end_date=end_obj.get("date") if all_day else None,
            start_datetime=(
                datetime.fromisoformat(start_obj["dateTime"].replace("Z", ""))
                if not all_day
                else None
            ),
            end_datetime=(
                datetime.fromisoformat(end_obj["dateTime"].replace("Z", ""))
                if not all_day
                else None
            ),
            all_day=all_day,
            attendees=json.dumps([]),
            recurrence=json.dumps([]),
            status=event_data.get("status", "confirmed"),
            synced_at=datetime.now(UTC),
        )
        session.add(new_event)
        await session.commit()
        await session.refresh(new_event)

        return CalendarEventResponse(
            id=new_event.id,
            calendar_id=new_event.calendar_id,
            summary=new_event.summary,
            description=new_event.description,
            location=new_event.location,
            start_datetime=new_event.start_datetime.isoformat()
            if new_event.start_datetime
            else None,
            end_datetime=new_event.end_datetime.isoformat() if new_event.end_datetime else None,
            start_date=new_event.start_date,
            end_date=new_event.end_date,
            all_day=new_event.all_day,
            attendees=[],
            recurrence=[],
            status=new_event.status,
            synced_at=new_event.synced_at.isoformat(),
        )

    except Exception as e:
        logger.error(f"Failed to quick add event: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# SYNC
# =============================================================================


@router.post("/sync")
async def sync_calendar(
    account_id: Optional[str] = Query(None),
    session: AsyncSession = Depends(get_session),
) -> CalendarSyncResponse:
    """
    Force sync de tous les calendriers et evenements.

    - Avec account_id : sync Google Calendar
    - Sans account_id : sync tous les calendriers locaux et CalDAV
    """
    try:
        calendars_result = await list_calendars(
            account_id=account_id,
            provider=None,
            session=session,
        )
        calendars_count = len(calendars_result)

        total_events = 0
        for calendar in calendars_result:
            events_result = await list_events(
                calendar_id=calendar.id,
                account_id=account_id,
                max_results=250,
                session=session,
            )
            total_events += len(events_result)

        return CalendarSyncResponse(
            calendars_synced=calendars_count,
            events_synced=total_events,
            synced_at=datetime.now(UTC).isoformat(),
        )

    except Exception as e:
        logger.error(f"Failed to sync calendar: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sync/status")
async def get_sync_status(
    account_id: Optional[str] = Query(None),
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Recupere le status de synchronisation."""
    # Count calendars and events
    calendars_stmt = select(Calendar)
    if account_id:
        calendars_stmt = calendars_stmt.where(Calendar.account_id == account_id)

    calendars_result = await session.execute(calendars_stmt)
    calendars = calendars_result.scalars().all()

    events_stmt = select(CalendarEvent)
    if account_id:
        events_stmt = events_stmt.join(Calendar).where(Calendar.account_id == account_id)

    events_result = await session.execute(events_stmt)
    events = events_result.scalars().all()

    last_sync = None
    synced_calendars = [cal for cal in calendars if cal.synced_at]
    if synced_calendars:
        last_sync = max(cal.synced_at for cal in synced_calendars).isoformat()

    return {
        "calendars_count": len(calendars),
        "events_count": len(events),
        "last_sync": last_sync,
        "providers": list(set(cal.provider for cal in calendars)),
    }
