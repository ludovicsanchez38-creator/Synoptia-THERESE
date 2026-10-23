"""
THERESE v2 - Local Calendar Provider

100% local SQLite implementation of CalendarProvider.
No external dependencies, works completely offline.
Part of the "Local First" architecture.
"""

import asyncio
import logging
import sys
from collections.abc import Callable
from dataclasses import replace
from datetime import UTC, date, datetime
from importlib import import_module
from types import FrameType

import pytz
from app.models.entities import Calendar, CalendarEvent, generate_uuid
from app.services.calendar.base_provider import (
    CalendarDTO,
    CalendarEventDTO,
    CalendarProvider,
    CreateEventRequest,
    UpdateEventRequest,
)
from app.services.civil_time import PARIS
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

rrulestr = import_module("dateutil.rrule").rrulestr
rruleset = import_module("dateutil.rrule").rruleset

logger = logging.getLogger(__name__)

_MAX_ETAPES_RECURRENCE = 100_000
_TraceurRecurrence = Callable[[FrameType, str, object], "_TraceurRecurrence | None"]


class LimiteCalculRecurrence(ValueError):
    """La série dépasse le travail autorisé pour un événement local."""


def _borne_murale_paris(borne: datetime) -> datetime:
    """Ramène une borne de fenêtre à la convention de la colonne interrogée.

    B-275 : `CalendarEvent.start_datetime` porte une heure murale Europe/Paris
    naïve. Les appelants, eux, tiennent un INSTANT : la fenêtre du mois arrive
    en forme Z depuis l'écran, et les outils du chat passent
    `datetime.now(UTC)`. Comparer l'un à l'autre décalait la fenêtre de deux
    heures en été - un rendez-vous à 22h30 le dernier jour du mois sortait de
    la vue. Une borne déjà naïve est du Paris mural, comme partout ailleurs
    (services/civil_time).
    """
    if borne.tzinfo is None:
        return borne
    return borne.astimezone(PARIS).replace(tzinfo=None)


def _occurrences_locales(
    event: CalendarEventDTO, debut: datetime, fin: datetime, limite: int,
) -> list[CalendarEventDTO]:
    """Borne le travail interne, même avant la première occurrence produite.

    dateutil n'expose pas de budget : limiter ses seuls résultats laisse
    sans borne les filtres impossibles ou les séries entièrement exclues.
    Le compteur de lignes couvre aussi ces boucles internes. Le traceur est
    propre au fil de calcul et restauré à la sortie, y compris en cas d'erreur.
    """
    etapes = 0

    def compter(frame: FrameType, evenement: str, argument: object) -> _TraceurRecurrence | None:
        nonlocal etapes
        if frame.f_globals.get("__name__") != "dateutil.rrule":
            return None
        if evenement == "line":
            etapes += 1
            if etapes > _MAX_ETAPES_RECURRENCE:
                raise LimiteCalculRecurrence(
                    f"Limite de calcul des récurrences atteinte ({_MAX_ETAPES_RECURRENCE} étapes)"
                )
        return compter

    precedent = sys.gettrace()
    sys.settrace(compter)
    try:
        return _developper_occurrences_locales(event, debut, fin, limite)
    finally:
        sys.settrace(precedent)


def _developper_occurrences_locales(
    event: CalendarEventDTO, debut: datetime, fin: datetime, limite: int,
) -> list[CalendarEventDTO]:
    """B-1110 : développe une série dans une fenêtre, sans modifier sa souche.

    Les heures stockées sont murales à Paris : garder ce fuseau pendant le
    calcul préserve 10 h après un changement d'heure. dateutil est déjà fourni
    par CalDAV. Les journées entières se calculent en dates civiles flottantes.
    """
    if event.start is None:
        return []
    if event.all_day:
        # Comme le filtre SQL historique, une journée reste visible à 14 h.
        debut = datetime.combine(debut.date(), datetime.min.time())
    start = event.start if isinstance(event.start, datetime) else datetime.combine(event.start, datetime.min.time())
    if not event.recurrence:
        return [event] if debut <= start < fin else []
    regles = []
    jours_exclus: set[date] = set()
    for regle in event.recurrence:
        regle = regle if ":" in regle else f"RRULE:{regle}"
        propriete, contenu = regle.split(":", 1)
        nom = propriete.split(";", 1)[0]
        if nom in ("RRULE", "EXRULE"):
            morceaux = contenu.split(";")
            for i, morceau in enumerate(morceaux):
                if not morceau.startswith("UNTIL="):
                    continue
                valeur_until = morceau.removeprefix("UNTIL=")
                if len(valeur_until) == 8:
                    until = datetime.strptime(valeur_until, "%Y%m%d")
                    if not event.all_day:
                        until = until.replace(hour=23, minute=59, second=59)
                else:
                    until = datetime.strptime(valeur_until.rstrip("Z"), "%Y%m%dT%H%M%S")
                    if valeur_until.endswith("Z"):
                        until = until.replace(tzinfo=UTC).astimezone(PARIS)
                if event.all_day:
                    morceaux[i] = "UNTIL=" + until.strftime("%Y%m%dT%H%M%S")
                else:
                    until = until.replace(tzinfo=PARIS).astimezone(UTC)
                    morceaux[i] = "UNTIL=" + until.strftime("%Y%m%dT%H%M%SZ")
            regle = nom + ":" + ";".join(morceaux)
        elif nom in ("RDATE", "EXDATE"):
            # icalendar lit VALUE=DATE, les heures flottantes et TZID.
            from icalendar import Event

            dates = Event.from_ical(f"BEGIN:VEVENT\n{regle}\nEND:VEVENT")[nom].dts
            instants = []
            for valeur in dates:
                instant = valeur.dt
                if not isinstance(instant, datetime):
                    if nom == "EXDATE":
                        jours_exclus.add(instant)
                        continue
                    instant = datetime.combine(instant, datetime.min.time())
                if instant.tzinfo is None:
                    instant = instant.replace(tzinfo=PARIS)
                if event.all_day:
                    instants.append(instant.astimezone(PARIS).strftime("%Y%m%dT000000"))
                else:
                    instants.append(instant.astimezone(UTC).strftime("%Y%m%dT%H%M%SZ"))
            if not instants:
                continue
            regle = nom + ":" + ",".join(instants)
        regles.append(regle)
    depart = start if event.all_day else start.replace(tzinfo=PARIS)
    borne = debut if event.all_day else debut.replace(tzinfo=PARIS)
    # Une série faite des seules exclusions DATE ne laisse aucune règle :
    # l'ensemble part vide, DTSTART s'y ajoute ci-dessous.
    serie = rrulestr("\n".join(regles), dtstart=depart, forceset=True) if regles else rruleset()
    # DTSTART appartient à l'ensemble, y compris sans RRULE ; EXDATE/EXRULE
    # restent appliquées par rruleset, comme pour les dates ajoutées par RDATE.
    serie.rdate(depart)
    duree = event.end - event.start if event.end else None
    occurrences = []
    for instant in serie.xafter(borne, inc=True):
        mural = instant if event.all_day else instant.astimezone(PARIS).replace(tzinfo=None)
        if mural >= fin:
            break
        if mural.date() in jours_exclus:
            continue
        nouveau_debut = mural.date() if event.all_day else mural
        occurrences.append(replace(
            event, start=nouveau_debut,
            end=nouveau_debut + duree if duree is not None else None,
            recurring_event_id=event.id,
        ))
        if len(occurrences) >= limite:
            break
    return occurrences


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
        self.recurrence_warnings: list[str] = []

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
        description: str | None = None,
        timezone: str = "Europe/Paris",
        color: str | None = None,
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
        name: str | None = None,
        description: str | None = None,
        timezone: str | None = None,
        color: str | None = None,
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
        time_min: datetime | None = None,
        time_max: datetime | None = None,
        max_results: int = 100,
        page_token: str | None = None,
        project_id: str | None = None,
        expand_recurring: bool = False,
    ) -> tuple[list[CalendarEventDTO], str | None]:
        """List events from a local calendar.

        `project_id` : cloison par dossier (0.56). LOCAL SEULEMENT - le
        fournisseur Google liste en direct chez Google, la colonne SQLite ne le
        filtrerait pas, et pretendre le contraire serait le motif de la 0.53.
        """
        statement = select(CalendarEvent).where(CalendarEvent.calendar_id == calendar_id)
        # 0.56 : cloison par dossier. Depuis une conversation rattachee, on ne
        # rend que les evenements de CE dossier - plus ceux d'avant la 0.56, qui
        # n'en portent aucun (fail-open sur NULL, pas de backfill).
        # Campagne cinq personas : « Seance Martin » apparaissait depuis le
        # dossier Ruiz.
        if project_id is not None:
            statement = statement.where(
                (CalendarEvent.project_id == project_id)
                | (CalendarEvent.project_id.is_(None))
            )

        # Time filtering. B-275 : la borne est un instant, la colonne une heure
        # murale de Paris - la conversion appartient à ce fournisseur, seul à
        # connaître la convention de SA table.
        if time_min:
            borne_min = _borne_murale_paris(time_min)
            filtre = (
                (CalendarEvent.start_datetime >= borne_min) |
                (CalendarEvent.start_date >= borne_min.strftime("%Y-%m-%d"))
            )
            # Une souche ancienne peut encore produire des occurrences futures.
            if expand_recurring:
                filtre = filtre | CalendarEvent.recurrence.is_not(None)
            statement = statement.where(filtre)
        if time_max:
            borne_max = _borne_murale_paris(time_max)
            statement = statement.where(
                (CalendarEvent.start_datetime <= borne_max) |
                (CalendarEvent.start_date <= borne_max.strftime("%Y-%m-%d"))
            )

        # Order by start time
        statement = statement.order_by(
            CalendarEvent.start_datetime.asc(),
            CalendarEvent.start_date.asc(),
        )

        # Pagination
        offset = int(page_token) if page_token else 0
        if not expand_recurring:
            statement = statement.offset(offset).limit(max_results)

        result = await self._session.execute(statement)
        events = result.scalars().all()

        if expand_recurring:
            if time_min is None or time_max is None:
                raise ValueError("Le développement des récurrences exige une période bornée")
            self.recurrence_warnings = []
            dtos = []
            for event in events:
                try:
                    dtos.extend(await asyncio.to_thread(
                        _occurrences_locales,
                        self._event_to_dto(event), _borne_murale_paris(time_min),
                        _borne_murale_paris(time_max), offset + max_results + 1,
                    ))
                except LimiteCalculRecurrence as exc:
                    self.recurrence_warnings.append(
                        f"Événement ignoré : {event.summary}. {exc}. "
                        "Ouvre Agenda pour vérifier cette série."
                    )
                except Exception:
                    logger.warning("Récurrence locale illisible : événement %s", event.id)
                    self.recurrence_warnings.append(
                        f"Événement ignoré (récurrence illisible) : {event.summary}. "
                        "Ouvre Agenda pour vérifier cette série."
                    )
            dtos.sort(key=lambda evt: (
                evt.start if isinstance(evt.start, datetime) else datetime.combine(evt.start, datetime.min.time()), evt.id,
            ))
            suivant = str(offset + max_results) if len(dtos) > offset + max_results else None
            return dtos[offset:offset + max_results], suivant

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
            project_id=request.project_id,
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

        # B-026 : le rappel etait le SEUL champ de la requete a n'etre jamais
        # lu. `[]` est serialise comme les autres valeurs - une absence de
        # rappel voulue ne doit pas se relire comme « jamais renseigne ».
        import json as _json
        event.reminders = _json.dumps(list(request.reminders))

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

        if request.reminders is not None:
            # `None` = « je n'y touche pas » ; `[]` = « plus de rappel ».
            import json
            event.reminders = json.dumps(list(request.reminders))

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

        # Parse reminders (B-026). `None` en base = evenement anterieur a la
        # colonne : aucun rappel connu, donc aucun rappel annonce.
        reminders: list[int] = []
        if event.reminders:
            try:
                lus = json.loads(event.reminders)
                if isinstance(lus, list):
                    reminders = [int(m) for m in lus]
            except (json.JSONDecodeError, TypeError, ValueError):
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
            reminders=reminders,
            status=event.status,
            created_at=event.synced_at,
            updated_at=event.synced_at,
        )
