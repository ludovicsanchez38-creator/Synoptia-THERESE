"""
THERESE v2 - CalDAV Provider

CalDAV implementation of CalendarProvider.
Supports Nextcloud, iCloud, Fastmail, cal.com, Radicale, etc.
"""

import asyncio
import logging
import os
from datetime import UTC, date, datetime, timedelta
from typing import Optional

import caldav
import pytz
from app.services.calendar.base_provider import (
    CalendarDTO,
    CalendarEventDTO,
    CalendarProvider,
    ConflitDeVersion,
    CreateEventRequest,
    UpdateEventRequest,
    allday_end_from_wire,
    allday_end_to_wire,
)
from icalendar import Alarm as IAlarm
from icalendar import Calendar as ICalendar
from icalendar import Event as IEvent
from icalendar import vDate, vDatetime

logger = logging.getLogger(__name__)



def _alarme(minutes_avant: int) -> IAlarm:
    """Un VALARM d'affichage `minutes_avant` minutes avant l'événement (B-481)."""
    alarme = IAlarm()
    alarme.add("action", "DISPLAY")
    alarme.add("description", "Rappel")
    alarme.add("trigger", timedelta(minutes=-int(minutes_avant)))
    return alarme

class CalDAVProvider(CalendarProvider):
    """
    CalDAV implementation of CalendarProvider.

    Works with any CalDAV-compatible server:
    - Nextcloud
    - iCloud
    - Fastmail
    - cal.com
    - Radicale
    - Baikal
    - etc.
    """

    def __init__(
        self,
        url: str,
        username: str,
        password: str,
    ):
        """
        Initialize CalDAV provider.

        Args:
            url: CalDAV server URL (principal or calendar URL)
            username: Username for authentication
            password: Password for authentication
        """
        self._url = url
        self._username = username
        self._password = password
        self._client: Optional[caldav.DAVClient] = None
        self._principal: Optional[caldav.Principal] = None

    @property
    def provider_name(self) -> str:
        return "caldav"

    @property
    def supports_attendees(self) -> bool:
        return True

    @property
    def supports_recurrence(self) -> bool:
        return True

    @property
    def supports_reminders(self) -> bool:
        return True

    def _get_client(self) -> caldav.DAVClient:
        """Get or create CalDAV client."""
        if not self._client:
            # US-008 (RES5-a) : timeout explicite. Sans lui, un serveur CalDAV
            # distant qui pend bloquait l'opération indéfiniment.
            timeout = int(os.getenv("CALDAV_TIMEOUT", "30"))
            self._client = caldav.DAVClient(
                url=self._url,
                username=self._username,
                password=self._password,
                timeout=timeout,
            )
        return self._client

    def _get_principal(self) -> caldav.Principal:
        """Get or create CalDAV principal."""
        if not self._principal:
            self._principal = self._get_client().principal()
        return self._principal

    # ============================================================
    # Calendar Operations
    # ============================================================

    async def list_calendars(self) -> list[CalendarDTO]:
        """List all CalDAV calendars."""

        def _sync_list():
            principal = self._get_principal()
            calendars = principal.calendars()
            return [self._caldav_cal_to_dto(cal) for cal in calendars]

        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, _sync_list)

    async def get_calendar(self, calendar_id: str) -> CalendarDTO:
        """Get a single CalDAV calendar."""

        def _sync_get():
            principal = self._get_principal()
            for cal in principal.calendars():
                if cal.id == calendar_id or str(cal.url) == calendar_id:
                    return self._caldav_cal_to_dto(cal)
            raise ValueError(f"Calendar {calendar_id} not found")

        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, _sync_get)

    async def create_calendar(
        self,
        name: str,
        description: str | None = None,
        timezone: str = "Europe/Paris",
        color: str | None = None,
    ) -> CalendarDTO:
        """Create a new CalDAV calendar."""

        def _sync_create():
            principal = self._get_principal()
            # Not all CalDAV servers support calendar creation
            try:
                cal = principal.make_calendar(name=name)
                return self._caldav_cal_to_dto(cal)
            except Exception as e:
                logger.error(f"Failed to create CalDAV calendar: {e}")
                raise ValueError(f"Calendar creation not supported or failed: {e}")

        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, _sync_create)

    async def update_calendar(
        self,
        calendar_id: str,
        name: str | None = None,
        description: str | None = None,
        timezone: str | None = None,
        color: str | None = None,
    ) -> CalendarDTO:
        """Update a CalDAV calendar."""
        # Most CalDAV servers don't support updating calendar properties
        # via the standard protocol. Return current state.
        return await self.get_calendar(calendar_id)

    async def delete_calendar(self, calendar_id: str) -> None:
        """Delete a CalDAV calendar."""

        def _sync_delete():
            principal = self._get_principal()
            for cal in principal.calendars():
                if cal.id == calendar_id or str(cal.url) == calendar_id:
                    cal.delete()
                    return
            raise ValueError(f"Calendar {calendar_id} not found")

        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, _sync_delete)

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
        """List events from a CalDAV calendar."""

        def _sync_list():
            principal = self._get_principal()
            cal = None
            for c in principal.calendars():
                if c.id == calendar_id or str(c.url) == calendar_id:
                    cal = c
                    break

            if not cal:
                raise ValueError(f"Calendar {calendar_id} not found")

            # Set default time range
            if not time_min:
                time_min_dt = datetime.now(UTC) - timedelta(days=30)
            else:
                time_min_dt = time_min

            if not time_max:
                time_max_dt = datetime.now(UTC) + timedelta(days=365)
            else:
                time_max_dt = time_max

            # Search events
            events = cal.date_search(
                start=time_min_dt,
                end=time_max_dt,
                expand=True,  # Expand recurring events
            )

            # Convert and limit
            result = []
            for event in events[:max_results]:
                try:
                    dto = self._caldav_event_to_dto(event, calendar_id)
                    result.append(dto)
                except Exception as e:
                    logger.warning(f"Failed to parse CalDAV event: {e}")

            return result, None  # CalDAV doesn't have pagination tokens

        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, _sync_list)

    async def get_event(
        self,
        calendar_id: str,
        event_id: str,
    ) -> CalendarEventDTO:
        """Get a single event from CalDAV."""

        def _sync_get():
            principal = self._get_principal()
            cal = None
            for c in principal.calendars():
                if c.id == calendar_id or str(c.url) == calendar_id:
                    cal = c
                    break

            if not cal:
                raise ValueError(f"Calendar {calendar_id} not found")

            # Try to find by UID
            try:
                event = cal.event_by_uid(event_id)
                return self._caldav_event_to_dto(event, calendar_id)
            except Exception as e:
                logger.debug("CalDAV evenement non trouve par UID, recherche sequentielle: %s", e)

            # Search all events
            events = cal.events()
            for event in events:
                if self._get_event_uid(event) == event_id:
                    return self._caldav_event_to_dto(event, calendar_id)

            raise ValueError(f"Event {event_id} not found")

        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, _sync_get)

    async def create_event(self, request: CreateEventRequest) -> CalendarEventDTO:
        """Create a new event in CalDAV calendar."""

        def _sync_create():
            principal = self._get_principal()
            cal = None
            for c in principal.calendars():
                if c.id == request.calendar_id or str(c.url) == request.calendar_id:
                    cal = c
                    break

            if not cal:
                raise ValueError(f"Calendar {request.calendar_id} not found")

            # Build iCalendar event
            ical = ICalendar()
            ical.add("prodid", "-//THERESE//CalDAV//FR")
            ical.add("version", "2.0")

            vevent = IEvent()
            vevent.add("summary", request.summary)

            if request.description:
                vevent.add("description", request.description)
            if request.location:
                vevent.add("location", request.location)

            # Set timing
            tz = pytz.timezone(request.timezone)

            if request.all_day:
                vevent.add("dtstart", request.start if isinstance(request.start, date) else request.start.date())
                # BUG-144 : fin inclusive (app) -> exclusive (RFC 5545, DTEND)
                vevent.add("dtend", allday_end_to_wire(request.end.date() if isinstance(request.end, datetime) else request.end))
            else:
                start_dt = request.start if isinstance(request.start, datetime) else datetime.combine(request.start, datetime.min.time())
                end_dt = request.end if isinstance(request.end, datetime) else datetime.combine(request.end, datetime.min.time())

                # Localize if naive
                if start_dt.tzinfo is None:
                    start_dt = tz.localize(start_dt)
                if end_dt.tzinfo is None:
                    end_dt = tz.localize(end_dt)

                vevent.add("dtstart", start_dt)
                vevent.add("dtend", end_dt)

            # Add attendees
            for attendee_email in request.attendees:
                vevent.add("attendee", f"mailto:{attendee_email}")

            # Add recurrence
            if request.recurrence:
                for rrule in request.recurrence:
                    if rrule.startswith("RRULE:"):
                        vevent.add("rrule", rrule[6:])
                    else:
                        vevent.add("rrule", rrule)

            # B-481 (05/09/2026) : rappels et statut n'étaient jamais écrits
            # alors que le provider annonce supports_reminders.
            for minutes in request.reminders or []:
                vevent.add_component(_alarme(minutes))
            statut = getattr(request, "status", None)
            if statut:
                vevent.add("status", str(statut).upper())

            vevent.add("dtstamp", datetime.now(UTC))

            ical.add_component(vevent)

            # Save to CalDAV
            event = cal.save_event(ical.to_ical().decode("utf-8"))

            return self._caldav_event_to_dto(event, request.calendar_id)

        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, _sync_create)

    async def update_event(
        self,
        calendar_id: str,
        event_id: str,
        request: UpdateEventRequest,
    ) -> CalendarEventDTO:
        """Update an event in CalDAV calendar."""

        def _sync_update():
            principal = self._get_principal()
            cal = None
            for c in principal.calendars():
                if c.id == calendar_id or str(c.url) == calendar_id:
                    cal = c
                    break

            if not cal:
                raise ValueError(f"Calendar {calendar_id} not found")

            # Find the event
            event = None
            try:
                event = cal.event_by_uid(event_id)
            except Exception:
                for e in cal.events():
                    if self._get_event_uid(e) == event_id:
                        event = e
                        break

            if not event:
                raise ValueError(f"Event {event_id} not found")

            # B-260 : relire le contenu ET son jeton de version dans la MEME
            # reponse. `load()` fait un GET et pose `data` et l'en-tete `Etag`
            # ensemble : la precondition porte alors sur ce qu'on a REELLEMENT
            # lu. Lire l'ETag apres coup (PROPFIND separe) ne protegerait que
            # les millisecondes entre ce PROPFIND et le PUT, en laissant grande
            # ouverte la vraie fenetre, celle de la lecture a l'ecriture.
            # Un serveur qui refuse le GET retombe sans jeton, donc sur le
            # chemin inconditionnel d'avant : jamais moins bien qu'avant.
            try:
                event.load()
            except Exception as e:
                logger.debug(
                    "CalDAV : relecture impossible, ecriture sans jeton de version: %s", e
                )

            # Parse existing iCalendar
            ical = ICalendar.from_ical(event.data)
            vevent = None
            for component in ical.walk():
                if component.name == "VEVENT":
                    vevent = component
                    break

            if not vevent:
                raise ValueError("Invalid event data")

            # Update fields
            if request.summary is not None:
                vevent["summary"] = request.summary
            if request.description is not None:
                vevent["description"] = request.description
            if request.location is not None:
                vevent["location"] = request.location

            # Update timing
            tz = pytz.timezone(request.timezone or "Europe/Paris")

            if request.start is not None:
                if request.all_day is True:
                    vevent["dtstart"] = vDate(request.start if isinstance(request.start, date) else request.start.date())
                else:
                    start_dt = request.start if isinstance(request.start, datetime) else datetime.combine(request.start, datetime.min.time())
                    if start_dt.tzinfo is None:
                        start_dt = tz.localize(start_dt)
                    vevent["dtstart"] = vDatetime(start_dt)

            if request.end is not None:
                if request.all_day is True:
                    # BUG-144 : fin inclusive (app) -> exclusive (RFC 5545, DTEND)
                    vevent["dtend"] = vDate(allday_end_to_wire(request.end.date() if isinstance(request.end, datetime) else request.end))
                else:
                    end_dt = request.end if isinstance(request.end, datetime) else datetime.combine(request.end, datetime.min.time())
                    if end_dt.tzinfo is None:
                        end_dt = tz.localize(end_dt)
                    vevent["dtend"] = vDatetime(end_dt)

            # B-481 : participants, récurrence, statut et rappels suivent aussi.
            if request.attendees is not None:
                if "attendee" in vevent:
                    del vevent["attendee"]
                for attendee_email in request.attendees:
                    vevent.add("attendee", f"mailto:{attendee_email}")
            if request.recurrence is not None:
                if "rrule" in vevent:
                    del vevent["rrule"]
                for rrule in request.recurrence:
                    vevent.add("rrule", rrule[6:] if rrule.startswith("RRULE:") else rrule)
            if request.status is not None:
                vevent["status"] = request.status.upper()
            if request.reminders is not None:
                vevent.subcomponents = [c for c in vevent.subcomponents if c.name != "VALARM"]
                for minutes in request.reminders:
                    vevent.add_component(_alarme(minutes))

            # Update and save
            donnees = ical.to_ical().decode("utf-8")
            event.data = donnees
            self._enregistrer_avec_precondition(event, donnees)

            return self._caldav_event_to_dto(event, calendar_id)

        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, _sync_update)

    async def delete_event(
        self,
        calendar_id: str,
        event_id: str,
    ) -> None:
        """Delete an event from CalDAV calendar."""

        def _sync_delete():
            principal = self._get_principal()
            cal = None
            for c in principal.calendars():
                if c.id == calendar_id or str(c.url) == calendar_id:
                    cal = c
                    break

            if not cal:
                raise ValueError(f"Calendar {calendar_id} not found")

            # Find and delete the event
            try:
                event = cal.event_by_uid(event_id)
                event.delete()
                return
            except Exception as e:
                logger.debug("CalDAV evenement non trouve par UID, recherche sequentielle: %s", e)

            for event in cal.events():
                if self._get_event_uid(event) == event_id:
                    event.delete()
                    return

            raise ValueError(f"Event {event_id} not found")

        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, _sync_delete)

    # ============================================================
    # Private Helpers
    # ============================================================

    def _lire_jeton_de_version(self, event: caldav.CalendarObjectResource) -> str | None:
        """L'ETag posé par la RELECTURE de l'événement, jamais un autre.

        On ne va pas le rechercher ailleurs : un ETag obtenu après coup ne
        correspondrait plus forcément au contenu qu'on s'apprête à réécrire,
        et la précondition mentirait. Absent : on ne l'invente pas — sans
        jeton, poser une précondition rendrait l'événement immodifiable,
        c'est le verrou déjà tenu par l'écrivain Google.
        """
        try:
            from caldav.elements import dav

            proprietes = getattr(event, "props", None) or {}
            jeton = proprietes.get(dav.GetEtag().tag)
        except Exception as e:
            logger.debug("CalDAV : ETag illisible, ecriture sans precondition: %s", e)
            return None
        return str(jeton) if jeton else None

    def _enregistrer_avec_precondition(
        self, event: caldav.CalendarObjectResource, donnees: str
    ) -> None:
        """Écrit l'événement sous `If-Match`, et nomme le conflit.

        B-260 : `event.save()` est un PUT inconditionnel, et la bibliothèque
        caldav n'accepte aucune précondition — elle code ses en-têtes en dur
        dans `_put`. Une modification faite ailleurs entre la lecture et
        l'écriture (le téléphone de l'utilisateur) était donc écrasée sans que
        rien ne le signale. On passe sous la bibliothèque : PUT direct par le
        client DAV, avec `If-Match` sur l'ETag lu.

        Un statut autre que 412 n'est PAS un signal de conflit : on rend alors
        la main à `save()`, qui porte le rattrapage vobject de la bibliothèque
        pour les serveurs pointilleux. Le repli est tracé, jamais silencieux,
        et ne fait pas pire que l'écriture inconditionnelle d'avant.
        """
        jeton = self._lire_jeton_de_version(event)
        client = getattr(event, "client", None)
        url = getattr(event, "url", None)
        if not jeton or client is None or url is None:
            event.save()
            return

        reponse = client.put(
            str(url),
            donnees,
            {"Content-Type": 'text/calendar; charset="utf-8"', "If-Match": jeton},
        )
        statut = getattr(reponse, "status", None)
        if statut == 412:
            raise ConflitDeVersion(
                "L'evenement a ete modifie ailleurs depuis sa lecture "
                "(telephone, autre appareil)."
            )
        if statut in (200, 201, 204, 302):
            return
        logger.warning(
            "CalDAV : ecriture conditionnelle refusee (HTTP %s), repli sans "
            "precondition sur save()",
            statut,
        )
        event.save()

    def _caldav_cal_to_dto(self, cal: caldav.Calendar) -> CalendarDTO:
        """Convert CalDAV calendar to CalendarDTO."""
        return CalendarDTO(
            id=cal.id or str(cal.url),
            name=cal.name or "Calendar",
            description=None,
            timezone="Europe/Paris",  # CalDAV doesn't expose this easily
            is_primary=False,
            provider="caldav",
            remote_id=str(cal.url),
        )

    def _caldav_event_to_dto(self, event: caldav.Event, calendar_id: str) -> CalendarEventDTO:
        """Convert CalDAV event to CalendarEventDTO."""
        ical = ICalendar.from_ical(event.data)

        vevent = None
        for component in ical.walk():
            if component.name == "VEVENT":
                vevent = component
                break

        if not vevent:
            raise ValueError("No VEVENT found in CalDAV event")

        # Extract fields
        uid = str(vevent.get("uid", ""))
        summary = str(vevent.get("summary", ""))
        description = str(vevent.get("description", "")) if vevent.get("description") else None
        location = str(vevent.get("location", "")) if vevent.get("location") else None

        # Extract timing
        dtstart = vevent.get("dtstart")
        dtend = vevent.get("dtend")

        start = None
        end = None
        all_day = False

        if dtstart:
            start_val = dtstart.dt
            if isinstance(start_val, datetime):
                start = start_val
            elif isinstance(start_val, date):
                start = start_val
                all_day = True

        if dtend:
            end_val = dtend.dt
            if isinstance(end_val, datetime):
                end = end_val
            elif isinstance(end_val, date):
                # BUG-144 : DTEND exclusif (RFC 5545) -> fin inclusive (app)
                end = allday_end_from_wire(start, end_val) if isinstance(start, date) and not isinstance(start, datetime) else end_val

        # Extract attendees
        attendees = []
        for attendee in vevent.get("attendee", []):
            email = str(attendee).replace("mailto:", "")
            if email:
                attendees.append(email)

        # Extract recurrence
        recurrence = None
        rrule = vevent.get("rrule")
        if rrule:
            recurrence = [f"RRULE:{rrule.to_ical().decode('utf-8')}"]

        # Extract timestamps
        dtstamp = vevent.get("dtstamp")
        created = dtstamp.dt if dtstamp else None

        return CalendarEventDTO(
            id=uid,
            calendar_id=calendar_id,
            summary=summary,
            description=description,
            location=location,
            start=start,
            end=end,
            all_day=all_day,
            recurrence=recurrence,
            attendees=attendees,
            status="confirmed",
            created_at=created,
            remote_id=uid,
        )

    def _get_event_uid(self, event: caldav.Event) -> str:
        """Extract UID from CalDAV event."""
        try:
            ical = ICalendar.from_ical(event.data)
            for component in ical.walk():
                if component.name == "VEVENT":
                    return str(component.get("uid", ""))
        except Exception as e:
            logger.debug("CalDAV evenement non trouve par UID, recherche sequentielle: %s", e)
        return ""
