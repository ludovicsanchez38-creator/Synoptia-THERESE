"""
THÉRÈSE v2 - Calendar Router

API endpoints pour la gestion calendrier.
Supporte Local (SQLite), Google Calendar (OAuth), CalDAV (Nextcloud, iCloud, etc.)

Phase 2 - Calendar
Local First - Multi-Provider
"""

import json
import logging
import uuid
from collections.abc import Awaitable, Callable
from datetime import UTC, date, datetime
from typing import Any, TypeVar
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.models.database import get_session
from app.models.entities import Calendar, CalendarEvent, EmailAccount, generate_uuid
from app.models.schemas import (
    CalendarEventResponse,
    CalendarResponse,
    CalendarSyncResponse,
    CreateEventRequest,
    QuickAddEventRequest,
    UpdateEventRequest,
)
from app.models.schemas_calendar import (
    CalDAVSetupRequest,
    CalDAVTestRequest,
)
from app.routers.email import ensure_valid_access_token
from app.services.calendar.base_provider import (
    ConflitDeVersion,
    allday_end_from_wire,
    allday_end_to_wire,
)
from app.services.calendar.provider_factory import (
    get_calendar_provider,
    list_caldav_presets,
    test_caldav_connection,
)
from app.services.calendar_service import CalendarService
from app.services.encryption import decrypt_value, encrypt_value, is_value_encrypted
from app.services.error_handler import message_pour_ecran
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col, select

router = APIRouter()
logger = logging.getLogger(__name__)

# Lot F : un mois d'agence (10 RDV/jour) dépasse 250. Ce n'est pas un plafond
# métier, c'est une taille de page. Au-delà de ce filet, on refuse plutôt
# que de blanchir la fin du mois.
PLAFOND_EVENEMENTS_FENETRE = 2000

TPage = TypeVar("TPage")


async def _collecter_pages_evenements(
    fetch_page: Callable[[str | None], Awaitable[tuple[list[TPage], str | None]]],
) -> list[TPage]:
    """Enchaîne les jetons jusqu'à épuisement, ou avoue le plafond."""
    collected: list[TPage] = []
    token: str | None = None
    while True:
        items, next_token = await fetch_page(token)
        collected.extend(items)
        if not next_token:
            return collected
        if len(collected) >= PLAFOND_EVENEMENTS_FENETRE:
            raise HTTPException(
                status_code=409,
                detail=(
                    "Trop d'événements dans cette période "
                    f"(plus de {PLAFOND_EVENEMENTS_FENETRE}). Affine la vue."
                ),
            )
        token = next_token


def _validate_timezone(tz: str | None) -> str:
    """Fuseau IANA valide ou repli Europe/Paris (parité avec local_provider.py,
    qui valide déjà via pytz - un fuseau invalide envoyé tel quel à Google
    remonte en 400 reformulé en 500 générique)."""
    if not tz:
        return "Europe/Paris"
    try:
        ZoneInfo(tz)
    except (ZoneInfoNotFoundError, ValueError):
        return "Europe/Paris"
    return tz


def _google_allday_end_inclusive(start_obj: dict[str, str], end_obj: dict[str, str]) -> str | None:
    """BUG-144 (F2 revue) : end.date Google est EXCLUSIF (lendemain du dernier
    jour), l'app est INCLUSIVE. Conversion clampée à la lecture des réponses
    Google avant stockage local."""
    end_raw = end_obj.get("date")
    if not end_raw:
        return None
    start_raw = start_obj.get("date")
    if not start_raw:
        return str(end_raw)
    inclusive: date = allday_end_from_wire(
        date.fromisoformat(start_raw), date.fromisoformat(end_raw)
    )
    return inclusive.isoformat()


def _google_allday_end_exclusive(end_value: str) -> str:
    """Fin « toute la journée » inclusive (app) -> exclusive (Google). Sans
    +1 jour, un événement d'un seul jour (début = fin) est une plage vide."""
    exclusive: date = allday_end_to_wire(date.fromisoformat(end_value))
    return exclusive.isoformat()


def _google_datetime_civile(value: str, timezone: str | None = None) -> datetime:
    """Normalise un instant Google en heure murale Europe/Paris pour SQLite.

    Le schéma historique stocke des DateTime naïfs. Conserver tantôt `Z`,
    tantôt `+02:00`, faisait dépendre le brief du format renvoyé par Google.
    La conversion est donc faite explicitement à la frontière fournisseur.
    """
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=ZoneInfo(_validate_timezone(timezone)))
    return parsed.astimezone(ZoneInfo("Europe/Paris")).replace(tzinfo=None)


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
    account_id: str | None = Query(None, description="Email account ID (optional for local calendars)"),
    provider: str | None = Query(None, description="Filter by provider: local, google, caldav"),
    create_default: bool = Query(True, description="Create the default local calendar when none exists"),
    session: AsyncSession = Depends(get_session),
) -> list[CalendarResponse]:
    """
    Liste tous les calendriers.

    - Sans account_id : retourne les calendriers locaux + tous les calendriers en DB
    - Avec account_id : sync Google Calendar et retourne les calendriers du compte
    - Avec provider : filtre par type de provider
    """
    # If account_id provided and it's a Google account, sync from Google.
    # BUG-120 : un compte non-Google (IMAP) ne possède aucun calendrier Google.
    # Filtrer la liste sur son account_id renvoie donc une liste vide et bloque
    # la création d'événement. On le traite comme « pas de compte Google
    # exploitable » : repli sur les calendriers locaux (account_id NULL).
    non_google_account = False
    if account_id:
        account = await session.get(EmailAccount, account_id)
        if account:
            is_google = (
                account.provider in ("gmail", "google")
                or (account.access_token and account.refresh_token)
            )
            if is_google:
                google_cals = await _list_google_calendars(account_id, account, session)
                # Finding 2 (30/08) : choisir Gmail pour le courrier vidait le
                # menu Agenda de iCloud et du local. On les rajoute, filtrés.
                if provider == "google":
                    return google_cals
                autres_stmt = select(Calendar).where(
                    Calendar.provider.in_(("local", "caldav"))
                )
                if provider:
                    autres_stmt = autres_stmt.where(Calendar.provider == provider)
                autres = (await session.execute(autres_stmt)).scalars().all()
                extras = [
                    CalendarResponse(
                        id=cal.id,
                        account_id=cal.account_id,
                        summary=cal.summary,
                        description=cal.description,
                        timezone=cal.timezone,
                        primary=cal.primary,
                        provider=cal.provider,
                        synced_at=cal.synced_at.isoformat() if cal.synced_at else None,
                    )
                    for cal in autres
                ]
                if provider in ("local", "caldav"):
                    return extras
                return google_cals + extras
            else:
                non_google_account = True
                logger.warning(
                    "list_calendars fallthrough: account %s has provider=%r, "
                    "no Google sync performed",
                    account_id,
                    account.provider,
                )

    # Otherwise, list from database (local + cached Google + CalDAV)
    statement = select(Calendar)
    if provider:
        statement = statement.where(Calendar.provider == provider)
    # On ne filtre par account_id que pour un vrai compte Google : sinon on
    # exclurait les calendriers locaux (account_id NULL) du repli IMAP (BUG-120).
    if account_id and not non_google_account:
        statement = statement.where(Calendar.account_id == account_id)

    result = await session.execute(statement)
    calendars = result.scalars().all()

    # Sans compte Google exploitable, la liste était VIDE : le formulaire
    # d'événement exigeait « un calendrier dans le menu déroulant » qui ne
    # proposait rien - impasse totale hors Google (retour Dr_logic-3D, 05/07 puis
    # revalidé en bloquant le 08/07, BUG-120). On crée donc un calendrier local
    # par défaut au premier passage (idempotent), y compris pour un compte IMAP.
    if create_default and not calendars and (not account_id or non_google_account) and provider in (None, "local"):
        from app.services.calendar.local_provider import LocalCalendarProvider

        local = LocalCalendarProvider(session)
        await local.create_calendar(
            name="Mon calendrier",
            description="Calendrier local créé automatiquement (aucun compte connecté)",
        )
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
            provider=cal.provider,
            synced_at=cal.synced_at.isoformat() if cal.synced_at else None,
        )
        for cal in calendars
    ]


def _raise_if_google_412(e: Exception) -> None:
    """412 = la précondition `If-Match` a échoué : l'événement a bougé ailleurs.

    B-029 : un conflit d'écriture concurrente sortait en 500 « 412 Precondition
    Failed ». L'écran ne pouvait ni le distinguer d'une panne, ni proposer le
    seul geste utile : relire avant de réécrire.
    """
    import httpx

    if isinstance(e, httpx.HTTPStatusError) and e.response.status_code == 412:
        raise HTTPException(
            status_code=409,
            detail=(
                "L'événement a été modifié ailleurs depuis sa lecture "
                "(téléphone, autre appareil). Recharge l'agenda avant "
                "d'enregistrer, sans quoi cette modification en écraserait "
                "une autre."
            ),
        ) from e


def _raise_if_google_403(e: Exception) -> None:
    """403 Google = API Calendar non activée dans le projet GCP ou scope refusé.

    Sans ce mapping, le testeur reçoit un 500 générique et le chat répond
    « ça coince » sans piste (bug lcjp 11/06/2026).
    """
    import httpx

    if isinstance(e, httpx.HTTPStatusError) and e.response.status_code == 403:
        raise HTTPException(
            status_code=403,
            detail=(
                "Google refuse l'accès au calendrier (403). Active l'API "
                "« Google Calendar » dans ta console Google Cloud "
                "(APIs et services > Bibliothèque > Google Calendar API > Activer), "
                "puis relance la synchronisation. Si le souci persiste, vérifie "
                "que l'accès au calendrier a bien été autorisé pour ce compte."
            ),
        ) from e


async def _list_google_calendars(
    account_id: str,
    account: EmailAccount,
    session: AsyncSession,
) -> list[CalendarResponse]:
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
                # Finding 3 (30/08) : les fériés ont le même id Google sur
                # deux comptes. Écrire ici volait la ligne de A (account_id
                # inchangé, summary de B) : déconnecter A, et B 401.
                if existing_cal.account_id != account_id:
                    continue
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
                provider=cal.provider,
                synced_at=cal.synced_at.isoformat() if cal.synced_at else None,
            )
            for cal in calendars
        ]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list Google calendars: {e}")
        _raise_if_google_403(e)
        raise HTTPException(status_code=500, detail=message_pour_ecran(e))


@router.get("/calendars/{calendar_id}")
async def get_calendar(
    calendar_id: str,
    account_id: str | None = Query(None),
    session: AsyncSession = Depends(get_session),
) -> CalendarResponse:
    """Récupère un calendrier spécifique.

    B-181 : `account_id` était OBLIGATOIRE et comparé à celui du calendrier.
    Un calendrier local naît avec `account_id` à NULL : aucune valeur ne
    pouvait convenir, ni une chaîne, ni la chaîne vide, ni l'omission (422).
    La route était donc fermée à tout ce que l'application crée elle-même. Le
    paramètre devient facultatif ; la comparaison, elle, ne bouge pas et reste
    fermée dans les deux sens - un calendrier Google ne s'ouvre pas sans son
    compte, un calendrier local ne s'ouvre pas avec le compte d'un autre.
    """
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
        provider=calendar.provider,
        # Un calendrier local naît sans date de synchronisation. Le paramètre
        # obligatoire fermait la route avant qu'on n'atteigne cette ligne : la
        # rouvrir sans la rendre facultative aurait remplacé un 422 par un 500.
        synced_at=calendar.synced_at.isoformat() if calendar.synced_at else None,
    )


class CreationCalendrier(BaseModel):
    """Corps de `POST /calendars`.

    B-182 : la route ne déclarait que des paramètres simples, donc des
    paramètres d'URL. Un corps JSON était ignoré EN ENTIER et la route rendait
    200 avec un calendrier nommé « Mon calendrier », comme si elle avait obéi.
    Le client `createCalendar` (`services/api/calendar.ts`) envoie pourtant un
    corps JSON : aucun calendrier créé par l'application ne portait le nom
    demandé. `extra="forbid"` ferme l'autre moitié du défaut : un champ que la
    route ne connaît pas (`provider` au lieu de `provider_type`) se dit, au
    lieu de disparaître dans un 200.
    """

    model_config = ConfigDict(extra="forbid")

    account_id: str | None = None
    summary: str | None = None
    description: str | None = None
    timezone: str | None = None
    provider_type: str | None = None


@router.post("/calendars")
async def create_calendar(
    corps: CreationCalendrier | None = None,
    account_id: str | None = None,
    summary: str | None = None,
    description: str | None = None,
    timezone: str | None = None,
    provider_type: str | None = Query(None, description="Provider: local, google, caldav"),
    session: AsyncSession = Depends(get_session),
) -> CalendarResponse:
    """
    Cree un nouveau calendrier.

    - provider_type=local : Calendrier local SQLite (pas besoin d'account_id)
    - provider_type=google : Calendrier Google Calendar (account_id requis)
    - provider_type=caldav : Voir POST /calendars/caldav-setup

    Le corps JSON prime sur les paramètres d'URL, qui restent acceptés pour les
    appelants historiques.
    """
    demande = corps or CreationCalendrier()
    compte = demande.account_id if demande.account_id is not None else account_id
    nom = (demande.summary if demande.summary is not None else summary) or "Mon calendrier"
    detail = demande.description if demande.description is not None else description
    fuseau = (demande.timezone if demande.timezone is not None else timezone) or "Europe/Paris"
    type_fournisseur = (
        demande.provider_type if demande.provider_type is not None else provider_type
    ) or "local"

    if type_fournisseur == "local":
        # Local calendar - no external account needed
        provider = get_calendar_provider(provider_type="local", session=session)
        cal_dto = await provider.create_calendar(
            name=nom,
            description=detail,
            timezone=fuseau,
        )
        # The local provider already saved to DB
        await session.get(Calendar, cal_dto.id)
        return CalendarResponse(
            id=cal_dto.id,
            account_id=None,
            summary=cal_dto.name,
            description=cal_dto.description,
            timezone=cal_dto.timezone,
            primary=cal_dto.is_primary,
            provider="local",
            synced_at=datetime.now(UTC).isoformat(),
        )

    elif type_fournisseur == "google":
        if not compte:
            raise HTTPException(status_code=400, detail="account_id requis pour Google Calendar")

        account = await session.get(EmailAccount, compte)
        if not account:
            raise HTTPException(status_code=404, detail="Account not found")

        access_token = (
            decrypt_value(account.access_token)
            if account.access_token and is_value_encrypted(account.access_token)
            else account.access_token
        )

        try:
            calendar_service = CalendarService(access_token)
            cal_data = await calendar_service.create_calendar(nom, detail, fuseau)

            new_cal = Calendar(
                id=cal_data["id"],
                account_id=compte,
                summary=cal_data["summary"],
                description=cal_data.get("description"),
                timezone=cal_data.get("timeZone", fuseau),
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
                provider=new_cal.provider,
                synced_at=new_cal.synced_at.isoformat() if new_cal.synced_at else None,
            )

        except Exception as e:
            logger.error(f"Failed to create Google calendar: {e}")
            raise HTTPException(status_code=500, detail=message_pour_ecran(e))

    else:
        raise HTTPException(status_code=400, detail="Pour CalDAV, utilisez POST /calendars/caldav-setup")


@router.delete("/calendars/{calendar_id}")
async def delete_calendar(
    calendar_id: str,
    account_id: str | None = Query(None),
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Supprime un calendrier.

    B-181 : deux verrous se cumulaient sur un calendrier local. Le premier est
    celui de la lecture (`account_id` obligatoire, comparé à NULL). Le second
    est plus profond : la suite chargeait un `EmailAccount` puis appelait le
    service Google, alors qu'un calendrier local n'a ni compte ni distant. Un
    calendrier créé par l'application ne pouvait donc jamais être supprimé.
    """
    calendar = await session.get(Calendar, calendar_id)
    if not calendar or calendar.account_id != account_id:
        raise HTTPException(status_code=404, detail="Calendar not found")

    if calendar.provider != "google":
        # Un calendrier local vit dans cette base : la ligne EST le calendrier.
        # Un calendrier CalDAV vit chez un tiers : on le DÉTACHE, on ne détruit
        # rien chez l'hébergeur - une suppression distante non demandée serait
        # irréversible et invisible depuis ici.
        distant = calendar.provider == "caldav"
        evenements = (
            await session.execute(
                select(CalendarEvent).where(CalendarEvent.calendar_id == calendar_id)
            )
        ).scalars().all()
        for evenement in evenements:
            await session.delete(evenement)
        await session.delete(calendar)
        await session.commit()
        return {
            "success": True,
            "message": "Calendrier détaché" if distant else "Calendar deleted",
        }

    account = await session.get(EmailAccount, calendar.account_id)
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
        raise HTTPException(status_code=500, detail=message_pour_ecran(e))


# =============================================================================
# CALDAV SETUP (Local First)
# =============================================================================


@router.post("/calendars/caldav-setup")
async def setup_caldav_calendar(
    request: CalDAVSetupRequest,
    session: AsyncSession = Depends(get_session),
) -> list[CalendarResponse]:
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
            provider=cal.provider,
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
    account_id: str | None = Query(None),
    time_min: str | None = None,
    time_max: str | None = None,
    # B-183 : le plafond haut existait seul. SQLite lit « LIMIT -1 » comme
    # « sans limite » : max_results=-1 rendait la table entière, et le
    # plafond de 250 se contournait par un signe moins.
    max_results: int = Query(default=50, ge=1, le=250),
    session: AsyncSession = Depends(get_session),
) -> list[CalendarEventResponse]:
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
            # B-236 : un identifiant qui ne désigne aucun calendrier connu, et
            # sans compte pour aller le chercher ailleurs, n'est pas un
            # calendrier Google : il n'existe pas. Répondre « account_id requis
            # pour Google Calendar » désignait un fournisseur hors de cause sur
            # une base 100 % locale, et l'écran affichait une panne Google.
            if calendar is None and calendar_id != "primary":
                raise HTTPException(
                    status_code=404,
                    detail=f"Calendrier introuvable : {calendar_id}",
                )
            raise HTTPException(status_code=400, detail="account_id requis pour Google Calendar")
        return await _list_events_google(
            account_id, calendar_id, session, time_min, time_max, max_results
        )


async def _list_events_provider(
    calendar: Calendar,
    session: AsyncSession,
    time_min: str | None,
    time_max: str | None,
    max_results: int,
) -> list[CalendarEventResponse]:
    """List events via abstract CalendarProvider (local or CalDAV)."""
    provider = await _get_provider_for_calendar(calendar, session)

    def _parse_borne_instant(s: str) -> datetime:
        """Borne de fenêtre, rendue comme un INSTANT (datetime aware).

        B-275 : la docstring annonçait « naive UTC » et le corps se contentait
        de retirer le décalage. Or l'écran envoie la forme Z
        (`startOfMonth.toISOString()`) et le stockage local est en heure murale
        Europe/Paris : la fenêtre du mois était décalée de deux heures en été,
        et un rendez-vous du dernier jour à 22h30 sortait de la vue.

        On rend donc l'instant, sans le mutiler ; c'est chaque fournisseur qui
        le ramène à SA convention (le local en heure murale Paris, CalDAV le
        cherche tel quel). Une borne déjà naïve est du Paris mural, comme
        partout ailleurs (services/civil_time).
        """
        # URL query params decode '+' as space, so restore it
        s = s.replace(" 00:00", "+00:00").replace("Z", "+00:00")
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=ZoneInfo("Europe/Paris"))
        return dt

    dt_min = _parse_borne_instant(time_min) if time_min else None
    dt_max = _parse_borne_instant(time_max) if time_max else None

    if dt_min is not None and dt_max is not None:
        # Fenêtre bornée (mois de l'agenda) : tout ramener ou avouer.
        async def _page(token: str | None) -> tuple[list[Any], str | None]:
            evenements, jeton = await provider.list_events(
                calendar_id=calendar.id,
                time_min=dt_min,
                time_max=dt_max,
                max_results=250,
                page_token=token,
            )
            return list(evenements), jeton

        events_dto = await _collecter_pages_evenements(_page)
    else:
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
            blocage=getattr(evt, "blocage", None),  # notion locale : un DTO de fournisseur ne la porte pas
            synced_at=datetime.now(UTC).isoformat(),
        )
        for evt in events_dto
    ]


async def _list_events_google(
    account_id: str,
    calendar_id: str,
    session: AsyncSession,
    time_min: str | None,
    time_max: str | None,
    max_results: int,
) -> list[CalendarEventResponse]:
    """List events via Google Calendar API (legacy flow)."""
    account = await session.get(EmailAccount, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    access_token = await ensure_valid_access_token(account, session)

    try:
        calendar_service = CalendarService(access_token)

        dt_min = datetime.fromisoformat(time_min.replace("Z", "")) if time_min else None
        dt_max = datetime.fromisoformat(time_max.replace("Z", "")) if time_max else None

        if dt_min is not None and dt_max is not None:
            async def _page_google(token: str | None) -> tuple[list[Any], str | None]:
                data = await calendar_service.list_events(
                    calendar_id, dt_min, dt_max, 250, token
                )
                return data.get("items", []), data.get("nextPageToken")

            items = await _collecter_pages_evenements(_page_google)
            events_data = {"items": items}
        else:
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
                # Finding 3 (30/08) : même id d'événement sur deux agendas
                # Google. Le second sync écrasait le premier.
                if existing_event.calendar_id != calendar_id:
                    continue
                existing_event.summary = event_data.get("summary", "")
                existing_event.description = event_data.get("description")
                existing_event.location = event_data.get("location")
                if all_day:
                    existing_event.start_date = start_obj.get("date")
                    existing_event.end_date = _google_allday_end_inclusive(start_obj, end_obj)
                else:
                    existing_event.start_datetime = _google_datetime_civile(
                        start_obj["dateTime"], start_obj.get("timeZone")
                    )
                    existing_event.end_datetime = _google_datetime_civile(
                        end_obj["dateTime"], end_obj.get("timeZone")
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
                    end_date=_google_allday_end_inclusive(start_obj, end_obj) if all_day else None,
                    start_datetime=(
                        _google_datetime_civile(
                            start_obj["dateTime"], start_obj.get("timeZone")
                        )
                        if not all_day
                        else None
                    ),
                    end_datetime=(
                        _google_datetime_civile(
                            end_obj["dateTime"], end_obj.get("timeZone")
                        )
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
                blocage=getattr(event, "blocage", None),  # notion locale : un DTO de fournisseur ne la porte pas
                synced_at=event.synced_at.isoformat() if event.synced_at else None,
            )
            for event in events
        ]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list events: {e}")
        _raise_if_google_403(e)
        # Robustesse (recette Ludo 16/07) : un calendrier Google introuvable ou
        # inaccessible (404) ne doit pas casser tout l'agenda en 500. On
        # dégrade en liste vide pour ce calendrier ; l'affichage continue avec
        # les autres calendriers.
        import httpx

        if isinstance(e, httpx.HTTPStatusError) and e.response.status_code == 404:
            logger.warning(
                f"Calendrier Google introuvable (404), ignoré : {calendar_id}"
            )
            return []
        raise HTTPException(status_code=500, detail=message_pour_ecran(e))


@router.get("/events/{event_id}")
async def get_event(
    event_id: str,
    calendar_id: str = Query(default="primary"),
    account_id: str | None = Query(None),
    session: AsyncSession = Depends(get_session),
) -> CalendarEventResponse:
    """Récupère un événement spécifique.

    B-180 : les deux paramètres étaient déclarés - `account_id` était même
    obligatoire - et AUCUN n'était lu. N'importe quelle valeur donnait accès à
    n'importe quel événement, y compris celui d'un autre compte connecté. La
    route voisine `GET /calendars/{id}` refusait déjà ce croisement.
    """
    event = await session.get(CalendarEvent, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    if calendar_id != "primary" and event.calendar_id != calendar_id:
        raise HTTPException(status_code=404, detail="Event not found")

    calendrier = await session.get(Calendar, event.calendar_id)
    if calendrier is not None and calendrier.account_id != account_id:
        raise HTTPException(status_code=404, detail="Event not found")
    # Un événement dont la ligne de calendrier a disparu n'est rattachable à
    # aucun compte : il n'y a rien à comparer. Le refuser condamnerait des
    # données déjà en base sans rien cloisonner de plus - les deux croisements
    # du défaut (calendrier voisin, compte étranger) sont fermés au-dessus.

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
        blocage=getattr(event, "blocage", None),  # notion locale : un DTO de fournisseur ne la porte pas
        synced_at=event.synced_at.isoformat(),
    )


class BlocageDeSeance(BaseModel):
    """Pourquoi cet evenement ne peut pas avoir lieu en l'etat."""

    blocage: str | None = None


@router.patch("/events/{event_id}/blocage")
async def bloquer_un_evenement(
    event_id: str,
    request: BlocageDeSeance,
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Bloque un evenement, ou leve le blocage.

    « Bloque » n'est pas « annule » : l'OPCO qui ecrit « ne maintenez pas la
    seance du 24 sans l'attestation » ne demande pas d'annuler. Le motif est
    obligatoire pour poser un blocage : un booleen sans raison obligerait a se
    souvenir.
    """
    evenement = await session.get(CalendarEvent, event_id)
    if evenement is None:
        raise HTTPException(status_code=404, detail="Evenement introuvable")

    motif = (request.blocage or "").strip()
    if request.blocage is not None and not motif:
        raise HTTPException(
            status_code=400, detail="Un blocage doit dire POURQUOI"
        )

    evenement.blocage = motif or None
    session.add(evenement)
    await session.commit()
    return {"id": evenement.id, "blocage": evenement.blocage, "status": evenement.status}


@router.post("/events")
async def create_event(
    request: CreateEventRequest,
    account_id: str | None = Query(None),
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
        # B-223 : même règle qu'à la lecture (B-236). Un identifiant absent
        # de la base ET sans compte pour aller le chercher ailleurs n'est pas
        # un agenda Google : il n'existe pas. L'alias `primary`, lui, réclame
        # bien un compte.
        if not account_id and calendar is None and request.calendar_id != "primary":
            raise HTTPException(
                status_code=404,
                detail=f"Calendrier introuvable : {request.calendar_id}",
            )
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
        blocage=getattr(evt, "blocage", None),  # notion locale : un DTO de fournisseur ne la porte pas
        synced_at=datetime.now(UTC).isoformat(),
    )


async def _create_event_google(
    account_id: str | None,
    request: CreateEventRequest,
    session: AsyncSession,
) -> CalendarEventResponse:
    """Create event via Google Calendar API."""
    if not account_id:
        raise HTTPException(status_code=400, detail="account_id requis pour Google Calendar")

    account = await session.get(EmailAccount, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    # BUG-105 : rafraîchir le token OAuth si expiré (comme _get_provider_for_calendar)
    access_token = await ensure_valid_access_token(account, session)

    try:
        calendar_service = CalendarService(access_token)

        if request.start_datetime and request.end_datetime:
            # BUG-082 : ajouter timeZone pour que Google Calendar interprète correctement
            # Ne PAS ajouter de suffixe Z (UTC) car les heures sont locales.
            # Fuseau réel du poste de l'utilisateur (capov à Toronto voyait un
            # décalage de 6 h tant que "Europe/Paris" était codé en dur).
            event_tz = _validate_timezone(request.timezone)
            start = {"dateTime": request.start_datetime, "timeZone": event_tz}
            end = {"dateTime": request.end_datetime, "timeZone": event_tz}
        elif request.start_date and request.end_date:
            start = {"date": request.start_date}
            end = {"date": _google_allday_end_exclusive(request.end_date)}
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
            end_date=_google_allday_end_inclusive(start_obj, end_obj) if all_day else None,
            # B-274 : retirer le « Z » stockait l'heure murale du décalage rendu
            # par Google, pas celle de Paris. La colonne est en heure murale
            # Europe/Paris (cf. _google_datetime_civile et le brief) : un
            # instant à 22h30 UTC se range le lendemain, pas la veille.
            start_datetime=(
                _google_datetime_civile(start_obj["dateTime"], start_obj.get("timeZone"))
                if not all_day
                else None
            ),
            end_datetime=(
                _google_datetime_civile(end_obj["dateTime"], end_obj.get("timeZone"))
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
            blocage=getattr(new_event, "blocage", None),  # notion locale : un DTO de fournisseur ne la porte pas
            synced_at=new_event.synced_at.isoformat() if new_event.synced_at else None,
        )

    except Exception as e:
        logger.error(f"Failed to create event: {e}")
        raise HTTPException(status_code=500, detail=message_pour_ecran(e))


@router.put("/events/{event_id}")
async def update_event(
    event_id: str,
    request: UpdateEventRequest,
    calendar_id: str = Query(default="primary"),
    account_id: str | None = Query(None),
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

        # B-260 : un conflit d'ecriture CalDAV est un CONFLIT, pas une panne.
        # Sans ce mapping, `ConflitDeVersion` sortait en 500 generique et
        # l'ecran ne pouvait ni le distinguer d'une panne, ni proposer le seul
        # geste utile : relire avant de reecrire. Meme reponse que l'ecrivain
        # Google depuis B-029.
        try:
            evt = await provider.update_event(calendar_id, event_id, provider_req)
        except ConflitDeVersion as e:
            raise HTTPException(
                status_code=409,
                detail=(
                    "L'événement a été modifié ailleurs depuis sa lecture "
                    "(téléphone, autre appareil). Recharge l'agenda avant "
                    "d'enregistrer, sans quoi cette modification en écraserait "
                    "une autre."
                ),
            ) from e

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
            blocage=getattr(evt, "blocage", None),  # notion locale : un DTO de fournisseur ne la porte pas
            synced_at=datetime.now(UTC).isoformat(),
        )

    # Google Calendar
    if not account_id:
        # B-223 : même règle qu'à la lecture (B-236). Un identifiant absent
        # de la base ET sans compte pour aller le chercher ailleurs n'est pas
        # un agenda Google : il n'existe pas. L'alias `primary`, lui, réclame
        # bien un compte.
        if calendar is None and calendar_id != "primary":
            raise HTTPException(
                status_code=404,
                detail=f"Calendrier introuvable : {calendar_id}",
            )
        raise HTTPException(status_code=400, detail="account_id requis pour Google Calendar")

    account = await session.get(EmailAccount, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    access_token = await ensure_valid_access_token(account, session)

    try:
        calendar_service = CalendarService(access_token)

        # Même fuseau réel du poste que pour la création (cohérence create/update).
        event_tz = _validate_timezone(request.timezone)
        start = (
            {"dateTime": request.start_datetime, "timeZone": event_tz}
            if request.start_datetime
            else ({"date": request.start_date} if request.start_date else None)
        )
        end = (
            {"dateTime": request.end_datetime, "timeZone": event_tz}
            if request.end_datetime
            else (
                {"date": _google_allday_end_exclusive(request.end_date)}
                if request.end_date
                else None
            )
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
        if db_event and db_event.calendar_id != calendar_id:
            db_event = None
        if db_event:
            all_day_flag = "date" in event_data.get("start", {})
            start_obj = event_data["start"]
            end_obj = event_data["end"]

            db_event.summary = event_data["summary"]
            db_event.description = event_data.get("description")
            db_event.location = event_data.get("location")
            if all_day_flag:
                db_event.start_date = start_obj.get("date")
                db_event.end_date = _google_allday_end_inclusive(start_obj, end_obj)
            else:
                # B-274 : même colonne, même convention que le sync et la
                # création — heure murale Europe/Paris.
                db_event.start_datetime = _google_datetime_civile(
                    start_obj["dateTime"], start_obj.get("timeZone")
                )
                db_event.end_datetime = _google_datetime_civile(
                    end_obj["dateTime"], end_obj.get("timeZone")
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

        if db_event is None:
            # B-139 / B-100 : Google a DÉJÀ accepté l'écriture distante. Sans
            # ligne miroir en base (événement jamais synchronisé, ou ligne
            # rattachée à un autre agenda et remise à None ci-dessus), lire
            # `db_event.id` levait un AttributeError converti en 500 : l'écran
            # annonçait un échec alors que l'agenda distant était bien modifié.
            # La réponse se construit donc depuis ce que Google a renvoyé,
            # sans rien écrire en base. `delete_event` traite déjà son cas
            # jumeau de cette façon.
            distant_start = event_data.get("start", {})
            distant_end = event_data.get("end", {})
            distant_all_day = "date" in distant_start
            return CalendarEventResponse(
                id=str(event_data.get("id", event_id)),
                calendar_id=calendar_id,
                summary=event_data.get("summary", ""),
                description=event_data.get("description"),
                location=event_data.get("location"),
                start_datetime=(
                    datetime.fromisoformat(
                        distant_start["dateTime"].replace("Z", "")
                    ).isoformat()
                    if not distant_all_day and distant_start.get("dateTime")
                    else None
                ),
                end_datetime=(
                    datetime.fromisoformat(
                        distant_end["dateTime"].replace("Z", "")
                    ).isoformat()
                    if not distant_all_day and distant_end.get("dateTime")
                    else None
                ),
                start_date=distant_start.get("date") if distant_all_day else None,
                end_date=(
                    _google_allday_end_inclusive(distant_start, distant_end)
                    if distant_all_day
                    else None
                ),
                all_day=distant_all_day,
                attendees=[a["email"] for a in event_data.get("attendees") or []],
                # `or []` et non `get(..., [])` : un `recurrence: null` explicite
                # relèverait le 500 que cette branche vient de fermer.
                recurrence=list(event_data.get("recurrence") or []),
                status=event_data.get("status", "confirmed"),
                blocage=None,  # notion locale : sans ligne en base, rien à refléter
                synced_at=datetime.now(UTC).isoformat(),
            )

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
            blocage=getattr(db_event, "blocage", None),  # notion locale : un DTO de fournisseur ne la porte pas
            synced_at=db_event.synced_at.isoformat() if db_event.synced_at else None,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update event: {e}")
        _raise_if_google_412(e)
        _raise_if_google_403(e)
        raise HTTPException(status_code=500, detail=message_pour_ecran(e))


@router.delete("/events/{event_id}")
async def delete_event(
    event_id: str,
    calendar_id: str = Query(default="primary"),
    account_id: str | None = Query(None),
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
        # B-223 : même règle qu'à la lecture (B-236). Un identifiant absent
        # de la base ET sans compte pour aller le chercher ailleurs n'est pas
        # un agenda Google : il n'existe pas. L'alias `primary`, lui, réclame
        # bien un compte.
        if calendar is None and calendar_id != "primary":
            raise HTTPException(
                status_code=404,
                detail=f"Calendrier introuvable : {calendar_id}",
            )
        raise HTTPException(status_code=400, detail="account_id requis pour Google Calendar")

    account = await session.get(EmailAccount, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    access_token = await ensure_valid_access_token(account, session)

    try:
        calendar_service = CalendarService(access_token)
        await calendar_service.delete_event(calendar_id, event_id)

        db_event = await session.get(CalendarEvent, event_id)
        if db_event and db_event.calendar_id == calendar_id:
            await session.delete(db_event)
            await session.commit()

        return {"success": True, "message": "Evenement supprime"}

    except Exception as e:
        logger.error(f"Failed to delete event: {e}")
        raise HTTPException(status_code=500, detail=message_pour_ecran(e))


@router.post("/events/quick-add")
async def quick_add_event(
    request: QuickAddEventRequest,
    account_id: str | None = Query(None, description="Compte Google (requis pour le quick-add NL)"),
    session: AsyncSession = Depends(get_session),
) -> CalendarEventResponse:
    """
    Ajoute un événement via parsing texte naturel.
    Ex: "Déjeuner avec Pierre demain à 12h30"

    Le parsing en langage naturel s'appuie sur l'API quickAdd de Google : il
    n'est donc disponible que sur un calendrier Google connecté. Pour un
    calendrier local (souverain), on répond clairement plutôt que de renvoyer
    un « Account not found » trompeur : l'événement se crée via le formulaire.
    """
    # Garde-fou honnête : quick-add NL = Google uniquement.
    calendar = await session.get(Calendar, request.calendar_id)
    is_local_target = calendar is not None and calendar.provider in ("local", "caldav")
    if account_id is None or is_local_target:
        raise HTTPException(
            status_code=400,
            detail=(
                "L'ajout rapide en langage naturel n'est disponible que sur un "
                "calendrier Google connecté. Pour un calendrier local, crée "
                "l'événement avec le formulaire (titre, date et heure)."
            ),
        )

    account = await session.get(EmailAccount, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    access_token = await ensure_valid_access_token(account, session)

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
            end_date=_google_allday_end_inclusive(start_obj, end_obj) if all_day else None,
            # B-274 : c'est Google qui interprète le texte et rend l'instant ;
            # il se range en heure murale Europe/Paris comme les autres.
            start_datetime=(
                _google_datetime_civile(start_obj["dateTime"], start_obj.get("timeZone"))
                if not all_day
                else None
            ),
            end_datetime=(
                _google_datetime_civile(end_obj["dateTime"], end_obj.get("timeZone"))
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
            blocage=getattr(new_event, "blocage", None),  # notion locale : un DTO de fournisseur ne la porte pas
            synced_at=new_event.synced_at.isoformat(),
        )

    except Exception as e:
        logger.error(f"Failed to quick add event: {e}")
        raise HTTPException(status_code=500, detail=message_pour_ecran(e))


# =============================================================================
# SYNC
# =============================================================================


@router.post("/sync")
async def sync_calendar(
    account_id: str | None = Query(None),
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

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to sync calendar: {e}")
        raise HTTPException(status_code=500, detail=message_pour_ecran(e))


@router.get("/sync/status")
async def get_sync_status(
    account_id: str | None = Query(None),
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


# ============================================================
# Import ICS
# ============================================================

# Espace de noms fige : l'id derive d'un evenement importe doit etre le MEME
# a chaque re-import du meme fichier dans le meme calendrier, sinon la garde
# anti-doublon ne peut plus le retrouver (B-196).
_ESPACE_ICS = uuid.UUID("6f0f4a2e-8a9d-5d38-9d0b-1f2c3a4b5c6d")


def _id_evenement_importe(calendar_id: str, uid: str) -> str:
    """Identifiant de ligne pour un evenement .ics, propre au calendrier.

    L'UID d'un fichier .ics n'est unique que dans son fichier : deux agendas
    peuvent legitimement contenir la meme invitation. La cle primaire, elle,
    est globale a la table - d'ou le derive par calendrier.
    """
    return str(uuid.uuid5(_ESPACE_ICS, f"{calendar_id}\n{uid}"))


@router.post("/import-ics")
async def import_ics_file(
    file: UploadFile = File(..., description="Fichier .ics (calendrier)"),
    calendar_id: str | None = Query(None, description="ID du calendrier cible (auto-detect sinon)"),
    session: AsyncSession = Depends(get_session),
):
    """
    Importe des événements depuis un fichier .ics dans le calendrier local.

    Si aucun calendar_id n'est fourni, utilise le premier calendrier local
    ou en crée un ("Mon calendrier").
    """
    from app.services.import_service import parse_ics

    # Validation fichier
    if not file.filename or not file.filename.lower().endswith(".ics"):
        raise HTTPException(status_code=400, detail="Le fichier doit être au format .ics")

    content = await file.read()
    if len(content) > 1_000_000:  # 1 Mo max
        raise HTTPException(status_code=400, detail="Fichier trop volumineux (max 1 Mo)")

    # Parser le fichier
    try:
        events = parse_ics(content)
    except Exception as e:
        logger.error(f"Erreur parsing ICS: {e}")
        raise HTTPException(status_code=400, detail="Fichier ICS invalide, impossible de le lire.") from e

    if not events:
        return {"imported": 0, "message": "Aucun événement trouvé dans le fichier"}

    # Trouver ou créer le calendrier cible
    if calendar_id:
        cal = await session.get(Calendar, calendar_id)
        if not cal:
            raise HTTPException(status_code=404, detail="Calendrier non trouvé")
    else:
        # Chercher le premier calendrier local
        result = await session.execute(
            select(Calendar).where(Calendar.provider == "local").limit(1)
        )
        cal = result.scalar_one_or_none()
        if not cal:
            # Créer un calendrier local
            cal = Calendar(
                id=generate_uuid(),
                summary="Mon calendrier",
                provider="local",
                timezone="Europe/Paris",
            )
            session.add(cal)
            await session.flush()

    # Importer les événements
    imported = 0
    skipped = 0
    for event_data in events:
        # Vérifier si l'événement existe déjà (par UID)
        uid = event_data.get("uid", "")
        identifiant = uid or generate_uuid()
        if uid:
            # B-196 : la garde anti-doublon porte sur (calendrier, UID) alors
            # que l'UID servait de CLE PRIMAIRE GLOBALE - la contrainte etait
            # donc plus large que la garde censee la proteger, et le meme
            # fichier range dans un second agenda sortait en 500. L'identite
            # d'un evenement importe est desormais le couple : un UID deja pris
            # ailleurs recoit ici un id derive, deterministe donc rejouable.
            derive = _id_evenement_importe(cal.id, uid)
            existing = await session.execute(
                select(CalendarEvent).where(
                    CalendarEvent.calendar_id == cal.id,
                    col(CalendarEvent.id).in_([uid, derive]),
                )
            )
            # `first()` et non `scalar_one_or_none()` : la recherche porte
            # desormais sur DEUX identifiants candidats, et deux lignes
            # trouvees feraient lever `MultipleResultsFound` a une garde dont
            # le seul travail est de dire « ca existe deja ».
            if existing.first() is not None:
                skipped += 1
                continue

            # NB : cette requete-ci ne filtre PAS par calendrier - c'est tout
            # son objet, verifier que l'UID est libre dans TOUTE la table.
            deja_pris = await session.execute(
                select(CalendarEvent).where(CalendarEvent.id == uid)
            )
            identifiant = uid if deja_pris.first() is None else derive

        event = CalendarEvent(
            id=identifiant,
            calendar_id=cal.id,
            summary=event_data["summary"][:200],
            description=event_data.get("description"),
            location=event_data.get("location"),
            all_day=event_data.get("all_day", False),
            status=event_data.get("status", "confirmed"),
            attendees=json.dumps(event_data.get("attendees", [])),
            recurrence=json.dumps(event_data.get("recurrence")) if event_data.get("recurrence") else None,
        )

        if event_data["all_day"]:
            event.start_date = event_data["start"]
            event.end_date = event_data["end"]
        else:
            event.start_datetime = datetime.fromisoformat(event_data["start"])
            event.end_datetime = datetime.fromisoformat(event_data["end"])

        session.add(event)
        imported += 1

    await session.commit()

    logger.info(f"ICS import: {imported} imported, {skipped} skipped (duplicates)")

    return {
        "imported": imported,
        "skipped": skipped,
        "calendar_id": cal.id,
        "calendar_name": cal.summary,
        "message": f"{imported} événement(s) importé(s){f', {skipped} doublon(s) ignoré(s)' if skipped else ''}",
    }


@router.get("/export-ics")
async def export_ics_file(
    calendar_id: str | None = Query(None, description="ID du calendrier a exporter (tous sinon)"),
    session: AsyncSession = Depends(get_session),
):
    """
    Exporte les evenements d'un calendrier au format .ics.

    Si aucun calendar_id n'est fourni, exporte tous les evenements locaux.
    """
    from datetime import date as date_type

    from fastapi.responses import Response as RawResponse
    from icalendar import Calendar as ICalCalendar
    from icalendar import Event as ICalEvent

    # Requete : evenements du calendrier specifie ou tous
    query = select(CalendarEvent)
    if calendar_id:
        cal = await session.get(Calendar, calendar_id)
        if not cal:
            raise HTTPException(status_code=404, detail="Calendrier non trouvé")
        query = query.where(CalendarEvent.calendar_id == calendar_id)

    result = await session.execute(query)
    events = result.scalars().all()

    # Construire le fichier ICS
    ical = ICalCalendar()
    ical.add("prodid", "-//THERESE v2//FR")
    ical.add("version", "2.0")
    ical.add("calscale", "GREGORIAN")

    for evt in events:
        ie = ICalEvent()
        ie.add("uid", evt.id)
        ie.add("summary", evt.summary)
        if evt.description:
            ie.add("description", evt.description)
        if evt.location:
            ie.add("location", evt.location)
        ie.add("status", evt.status.upper() if evt.status else "CONFIRMED")

        if evt.all_day and evt.start_date:
            ie.add("dtstart", date_type.fromisoformat(evt.start_date))
            if evt.end_date:
                # BUG-144 (F4 revue) : DTEND est EXCLUSIF (RFC 5545), la fin
                # stockée est INCLUSIVE -> +1 jour à l'export.
                ie.add("dtend", allday_end_to_wire(date_type.fromisoformat(evt.end_date)))
        elif evt.start_datetime:
            ie.add("dtstart", evt.start_datetime)
            if evt.end_datetime:
                ie.add("dtend", evt.end_datetime)

        if evt.attendees:
            try:
                att_list = json.loads(evt.attendees)
                for att in att_list:
                    ie.add("attendee", f"mailto:{att}")
            except (ValueError, TypeError):
                pass

        if evt.recurrence:
            try:
                rrules = json.loads(evt.recurrence)
                for rule in rrules:
                    if rule.startswith("RRULE:"):
                        ie.add("rrule", rule[6:])
            except (ValueError, TypeError):
                pass

        ical.add_component(ie)

    ics_bytes = ical.to_ical()

    return RawResponse(
        content=ics_bytes,
        media_type="text/calendar",
        headers={
            "Content-Disposition": "attachment; filename=therese-calendrier.ics",
        },
    )
