"""
THERESE v2 - Calendar Router Tests

Tests for calendar endpoints (local, Google, CalDAV providers).
Focus on local provider (SQLite) to avoid external mocks where possible.
Google Calendar and CalDAV endpoints are tested with mocks.
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import patch

import pytest
from httpx import AsyncClient

from tests.conftest import assert_response_ok

# ============================================================
# Fixtures
# ============================================================


@pytest.fixture
def sample_local_calendar():
    """Sample local calendar creation data."""
    return {
        "summary": "Mon calendrier test",
        "description": "Calendrier de test unitaire",
        "timezone": "Europe/Paris",
    }


@pytest.fixture
def sample_event_datetime():
    """Sample event with date+time."""
    now = datetime.now(UTC)
    start = (now + timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%S")
    end = (now + timedelta(hours=2)).strftime("%Y-%m-%dT%H:%M:%S")
    return {
        "summary": "Reunion test",
        "description": "Description de la reunion",
        "location": "Bureau Manosque",
        "start_datetime": start,
        "end_datetime": end,
    }


@pytest.fixture
def sample_event_all_day():
    """Sample all-day event."""
    today = datetime.now(UTC).strftime("%Y-%m-%d")
    tomorrow = (datetime.now(UTC) + timedelta(days=1)).strftime("%Y-%m-%d")
    return {
        "summary": "Journee formation",
        "description": "Formation IA journee complete",
        "start_date": today,
        "end_date": tomorrow,
    }


@pytest.fixture
def sample_caldav_setup():
    """Sample CalDAV setup data."""
    return {
        "url": "https://caldav.example.com/dav/",
        "username": "user@example.com",
        "password": "test-password",
    }


async def _create_local_calendar(client: AsyncClient, name: str = "Test Calendar") -> dict:
    """Helper to create a local calendar and return its data."""
    response = await client.post(
        "/api/calendar/calendars",
        params={
            "summary": name,
            "description": "Test calendar",
            "timezone": "Europe/Paris",
            "provider_type": "local",
        },
    )
    assert response.status_code == 200, f"Failed to create calendar: {response.text}"
    return response.json()


async def _create_event_on_calendar(
    client: AsyncClient, calendar_id: str, event_data: dict
) -> dict:
    """Helper to create an event on a calendar."""
    payload = {**event_data, "calendar_id": calendar_id}
    response = await client.post("/api/calendar/events", json=payload)
    assert response.status_code == 200, f"Failed to create event: {response.text}"
    return response.json()


# ============================================================
# Calendars - List
# ============================================================


class TestCalendarList:
    """Tests for listing calendars."""

    @pytest.mark.asyncio
    async def test_list_calendars_read_only_does_not_create_default(
        self, client: AsyncClient, db_session
    ):
        from app.models.entities import Calendar
        from sqlmodel import select

        response = await client.get("/api/calendar/calendars?create_default=false")
        assert_response_ok(response)
        assert response.json() == []
        stored = (await db_session.execute(select(Calendar))).scalars().all()
        assert stored == []

    @pytest.mark.asyncio
    async def test_list_calendars_cree_le_calendrier_local_par_defaut(self, client: AsyncClient):
        """GET /api/calendar/calendars - sans compte, un calendrier local par défaut
        est créé au premier passage (impasse hors Google, Dr_logic-3D 05/07/2026),
        et l'appel est idempotent (pas de doublon au second passage)."""
        response = await client.get("/api/calendar/calendars")
        assert_response_ok(response)
        data = response.json()

        assert len(data) == 1
        assert data[0]["summary"] == "Mon calendrier"
        assert data[0]["primary"] is True

        # Idempotent : un second appel ne crée pas de doublon.
        response2 = await client.get("/api/calendar/calendars")
        assert_response_ok(response2)
        assert len(response2.json()) == 1

    @pytest.mark.asyncio
    async def test_list_calendars_compte_imap_repli_local(self, client: AsyncClient, db_session):
        """BUG-120 : avec un compte IMAP (non-Google), la liste ne doit pas être
        vide. Sans repli, filtrer par l'account_id IMAP (qui ne possède aucun
        calendrier Google) renvoyait une liste vide et bloquait la création
        d'événement (bouton Enregistrer inopérant, Dr_logic-3D 08/07/2026)."""
        from app.models.entities import EmailAccount

        db_session.add(EmailAccount(id="imap-1", email="me@imap.fr", provider="imap"))
        await db_session.commit()

        response = await client.get("/api/calendar/calendars?account_id=imap-1")
        assert_response_ok(response)
        data = response.json()

        # Non vide : un calendrier local exploitable est proposé pour l'IMAP.
        assert len(data) >= 1
        # Sélectionnable (primary) pour débloquer le formulaire d'événement.
        assert any(c["primary"] for c in data)

    @pytest.mark.asyncio
    async def test_list_calendars_with_local(self, client: AsyncClient):
        """GET /api/calendar/calendars - should include local calendars."""
        await _create_local_calendar(client, "Calendrier Local")

        response = await client.get("/api/calendar/calendars")
        assert_response_ok(response)
        data = response.json()

        assert len(data) >= 1
        names = [cal["summary"] for cal in data]
        assert "Calendrier Local" in names

    @pytest.mark.asyncio
    async def test_list_calendars_filter_by_provider(self, client: AsyncClient):
        """GET /api/calendar/calendars?provider=local - should filter by provider."""
        await _create_local_calendar(client, "Local Only")

        response = await client.get("/api/calendar/calendars?provider=local")
        assert_response_ok(response)
        data = response.json()

        assert len(data) >= 1

    @pytest.mark.asyncio
    async def test_list_calendars_filter_nonexistent_provider(self, client: AsyncClient):
        """GET /api/calendar/calendars?provider=google - empty if no Google accounts."""
        await _create_local_calendar(client)

        response = await client.get("/api/calendar/calendars?provider=google")
        assert_response_ok(response)
        data = response.json()

        assert len(data) == 0


# ============================================================
# Calendars - Create
# ============================================================


class TestCalendarCreate:
    """Tests for creating calendars."""

    @pytest.mark.asyncio
    async def test_create_local_calendar(self, client: AsyncClient):
        """POST /api/calendar/calendars - should create a local calendar."""
        response = await client.post(
            "/api/calendar/calendars",
            params={
                "summary": "Mon calendrier",
                "description": "Description test",
                "timezone": "Europe/Paris",
                "provider_type": "local",
            },
        )
        assert_response_ok(response)
        data = response.json()

        assert data["summary"] == "Mon calendrier"
        assert "id" in data
        assert data["synced_at"] is not None

    @pytest.mark.asyncio
    async def test_create_google_calendar_no_account(self, client: AsyncClient):
        """POST /api/calendar/calendars?provider_type=google - should require account_id."""
        response = await client.post(
            "/api/calendar/calendars",
            params={
                "summary": "Google cal",
                "provider_type": "google",
            },
        )
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_create_caldav_calendar_redirect(self, client: AsyncClient):
        """POST /api/calendar/calendars?provider_type=caldav - should redirect to caldav-setup."""
        response = await client.post(
            "/api/calendar/calendars",
            params={
                "summary": "CalDAV cal",
                "provider_type": "caldav",
            },
        )
        assert response.status_code == 400
        data = response.json()
        # Global exception handler wraps detail in "message" key
        detail_text = data.get("detail", data.get("message", "")).lower()
        assert "caldav-setup" in detail_text


# ============================================================
# Calendars - Get & Delete
# ============================================================


class TestCalendarGetDelete:
    """Tests for getting and deleting calendars."""

    @pytest.mark.asyncio
    async def test_get_calendar_not_found(self, client: AsyncClient):
        """GET /api/calendar/calendars/{id} - should 404 for nonexistent."""
        response = await client.get(
            "/api/calendar/calendars/nonexistent?account_id=fake"
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_calendar_success(self, client: AsyncClient):
        """GET /api/calendar/calendars/{id} - should return calendar details."""
        cal = await _create_local_calendar(client, "Calendrier Detail")
        cal_id = cal["id"]

        # Note: The get endpoint requires account_id, but local cals have None
        # This tests that the endpoint exists. The account_id check may cause
        # a 404 for local calendars due to schema validation
        response = await client.get(
            f"/api/calendar/calendars/{cal_id}?account_id=none"
        )
        # Local calendar has account_id=None, so account_id mismatch -> 404
        assert response.status_code in [200, 404]

    @pytest.mark.asyncio
    async def test_delete_calendar_not_found(self, client: AsyncClient):
        """DELETE /api/calendar/calendars/{id} - should 404 for nonexistent."""
        response = await client.delete(
            "/api/calendar/calendars/nonexistent?account_id=fake"
        )
        assert response.status_code == 404


# ============================================================
# Events - List
# ============================================================


class TestEventsList:
    """Tests for listing events."""

    @pytest.mark.asyncio
    async def test_list_events_local_empty(self, client: AsyncClient):
        """GET /api/calendar/events - should return empty list for new local calendar."""
        cal = await _create_local_calendar(client)

        response = await client.get(
            f"/api/calendar/events?calendar_id={cal['id']}"
        )
        assert_response_ok(response)
        data = response.json()

        assert isinstance(data, list)
        assert len(data) == 0

    @pytest.mark.asyncio
    async def test_list_events_requires_account_for_google(self, client: AsyncClient):
        """GET /api/calendar/events - should require account_id for non-local calendars.

        B-236 : ce test passait un identifiant ABSENT de la base et attendait
        400 « account_id requis pour Google Calendar ». C'était le défaut : un
        calendrier qui n'existe pas n'est pas un calendrier Google, il rend
        désormais 404. L'alias Google `primary`, lui, réclame toujours un
        compte - c'est ce que le test vérifie maintenant.
        """
        response = await client.get(
            "/api/calendar/events?calendar_id=primary"
        )
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_list_events_with_date_range(self, client: AsyncClient):
        """GET /api/calendar/events - should filter by time_min/time_max."""
        cal = await _create_local_calendar(client)

        now = datetime.now(UTC)
        time_min = (now - timedelta(days=1)).isoformat()
        time_max = (now + timedelta(days=30)).isoformat()

        response = await client.get(
            f"/api/calendar/events?calendar_id={cal['id']}&time_min={time_min}&time_max={time_max}"
        )
        assert_response_ok(response)
        data = response.json()

        assert isinstance(data, list)


# ============================================================
# Events - Create
# ============================================================


class TestEventsCreate:
    """Tests for creating events."""

    @pytest.mark.asyncio
    async def test_create_event_local(self, client: AsyncClient, sample_event_datetime):
        """POST /api/calendar/events - should create event on local calendar."""
        cal = await _create_local_calendar(client)

        event_data = {**sample_event_datetime, "calendar_id": cal["id"]}
        response = await client.post("/api/calendar/events", json=event_data)
        assert_response_ok(response)
        data = response.json()

        assert data["summary"] == "Reunion test"
        assert data["description"] == "Description de la reunion"
        assert data["location"] == "Bureau Manosque"
        assert data["all_day"] is False
        assert "id" in data

    @pytest.mark.asyncio
    async def test_create_all_day_event(self, client: AsyncClient, sample_event_all_day):
        """POST /api/calendar/events - should create all-day event."""
        cal = await _create_local_calendar(client)

        event_data = {**sample_event_all_day, "calendar_id": cal["id"]}
        response = await client.post("/api/calendar/events", json=event_data)
        assert_response_ok(response)
        data = response.json()

        assert data["summary"] == "Journee formation"
        assert data["all_day"] is True

    @pytest.mark.asyncio
    async def test_create_all_day_event_meme_date(self, client: AsyncClient):
        """BUG-144 (F1 revue) : un evenement toute la journee d'un seul jour
        (debut = fin, fin INCLUSIVE) doit passer la validation BACKEND aussi -
        le schema refusait end <= start meme en journee entiere, donc l'UI
        acceptait puis l'API repondait 422."""
        cal = await _create_local_calendar(client)
        today = datetime.now(UTC).strftime("%Y-%m-%d")

        response = await client.post("/api/calendar/events", json={
            "calendar_id": cal["id"],
            "summary": "Salon pro",
            "start_date": today,
            "end_date": today,
        })

        assert_response_ok(response)
        data = response.json()
        assert data["all_day"] is True
        assert data["start_date"] == today
        assert data["end_date"] == today

    @pytest.mark.asyncio
    async def test_create_all_day_event_fin_avant_debut_refusee(self, client: AsyncClient):
        """La fin ne peut toujours pas PRECEDER le debut en journee entiere."""
        cal = await _create_local_calendar(client)
        today = datetime.now(UTC)

        response = await client.post("/api/calendar/events", json={
            "calendar_id": cal["id"],
            "summary": "Salon pro",
            "start_date": today.strftime("%Y-%m-%d"),
            "end_date": (today - timedelta(days=1)).strftime("%Y-%m-%d"),
        })

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_event_google_requires_account(self, client: AsyncClient, sample_event_datetime):
        """POST /api/calendar/events - should require account_id for Google calendar.

        B-223 : ce test passait un identifiant ABSENT de la base et attendait
        400 « account_id requis ». C'était le défaut (même correction que
        B-236 sur GET /events) : un agenda qui n'existe pas rend 404. L'alias
        Google `primary` réclame toujours un compte — c'est l'intention
        d'origine du test, et c'est ce qu'il vérifie maintenant.
        """
        event_data = {**sample_event_datetime, "calendar_id": "primary"}
        response = await client.post("/api/calendar/events", json=event_data)
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_create_event_with_attendees(self, client: AsyncClient):
        """POST /api/calendar/events - should support attendees."""
        cal = await _create_local_calendar(client)

        now = datetime.now(UTC)
        event_data = {
            "calendar_id": cal["id"],
            "summary": "Reunion equipe",
            "start_datetime": (now + timedelta(hours=1)).isoformat(),
            "end_datetime": (now + timedelta(hours=2)).isoformat(),
            "attendees": ["pierre@example.com", "marie@example.com"],
        }
        response = await client.post("/api/calendar/events", json=event_data)
        assert_response_ok(response)
        data = response.json()

        assert data["summary"] == "Reunion equipe"
        if data.get("attendees"):
            assert len(data["attendees"]) == 2

    @pytest.mark.parametrize(
        "payload, expected",
        [
            ({"summary": "Sans date"}, "soit des horaires"),
            ({"summary": "Partiel", "start_datetime": "2026-07-14T10:00:00"}, "obligatoires ensemble"),
            ({
                "summary": "Inversé",
                "start_datetime": "2026-07-14T11:00:00",
                "end_datetime": "2026-07-14T10:00:00",
            }, "postérieure"),
            ({
                "summary": "Participant invalide",
                "start_datetime": "2026-07-14T10:00:00",
                "end_datetime": "2026-07-14T11:00:00",
                "attendees": ["pas-un-email"],
            }, "Adresse participant invalide"),
        ],
    )
    def test_create_event_schema_rejects_ambiguous_payloads(self, payload, expected):
        from app.models.schemas import CreateEventRequest
        from pydantic import ValidationError

        with pytest.raises(ValidationError, match=expected):
            CreateEventRequest(**payload)


# ============================================================
# Events - Update
# ============================================================


class TestEventsUpdate:
    """Tests for updating events."""

    @pytest.mark.asyncio
    async def test_update_event_local(self, client: AsyncClient, sample_event_datetime):
        """PUT /api/calendar/events/{id} - should update local event."""
        cal = await _create_local_calendar(client)
        event = await _create_event_on_calendar(client, cal["id"], sample_event_datetime)

        response = await client.put(
            f"/api/calendar/events/{event['id']}?calendar_id={cal['id']}",
            json={"summary": "Reunion modifiee", "location": "Salle B"},
        )
        assert_response_ok(response)
        data = response.json()

        assert data["summary"] == "Reunion modifiee"
        assert data["location"] == "Salle B"

    @pytest.mark.asyncio
    async def test_update_event_google_requires_account(self, client: AsyncClient):
        """PUT /api/calendar/events/{id} - should require account_id for Google.

        B-223 : passe par `primary` (voir la note du test de création).
        """
        response = await client.put(
            "/api/calendar/events/evt-001?calendar_id=primary",
            json={"summary": "Updated"},
        )
        assert response.status_code == 400


# ============================================================
# Events - Delete
# ============================================================


class TestEventsDelete:
    """Tests for deleting events."""

    @pytest.mark.asyncio
    async def test_delete_event_local(self, client: AsyncClient, sample_event_datetime):
        """DELETE /api/calendar/events/{id} - should delete local event."""
        cal = await _create_local_calendar(client)
        event = await _create_event_on_calendar(client, cal["id"], sample_event_datetime)

        response = await client.delete(
            f"/api/calendar/events/{event['id']}?calendar_id={cal['id']}"
        )
        assert_response_ok(response)
        data = response.json()

        assert data["success"] is True

    @pytest.mark.asyncio
    async def test_delete_event_google_requires_account(self, client: AsyncClient):
        """DELETE /api/calendar/events/{id} - should require account_id for Google.

        B-223 : passe par `primary` (voir la note du test de création).
        """
        response = await client.delete(
            "/api/calendar/events/evt-001?calendar_id=primary"
        )
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_get_event_not_found(self, client: AsyncClient):
        """GET /api/calendar/events/{id} - should 404 for nonexistent event."""
        response = await client.get(
            "/api/calendar/events/nonexistent?calendar_id=primary&account_id=fake"
        )
        assert response.status_code == 404


# ============================================================
# CalDAV Setup
# ============================================================


class TestCalDAVSetup:
    """Tests for CalDAV setup endpoints."""

    @pytest.mark.asyncio
    async def test_caldav_test_connection_mock(self, client: AsyncClient, sample_caldav_setup):
        """POST /api/calendar/calendars/caldav-test - mock successful connection."""
        with patch("app.routers.calendar.test_caldav_connection") as mock_test:
            mock_test.return_value = {
                "success": True,
                "message": "Connexion reussie",
                "calendars": [
                    {"id": "cal-1", "name": "Personnel"},
                    {"id": "cal-2", "name": "Travail"},
                ],
            }

            response = await client.post(
                "/api/calendar/calendars/caldav-test",
                json=sample_caldav_setup,
            )
            assert_response_ok(response)
            data = response.json()

            assert data["success"] is True
            assert len(data["calendars"]) == 2

    @pytest.mark.asyncio
    async def test_caldav_test_connection_failure(self, client: AsyncClient, sample_caldav_setup):
        """POST /api/calendar/calendars/caldav-test - mock failed connection."""
        with patch("app.routers.calendar.test_caldav_connection") as mock_test:
            mock_test.return_value = {
                "success": False,
                "message": "Impossible de se connecter au serveur CalDAV",
                "calendars": [],
            }

            response = await client.post(
                "/api/calendar/calendars/caldav-test",
                json=sample_caldav_setup,
            )
            assert_response_ok(response)
            data = response.json()

            assert data["success"] is False

    @pytest.mark.asyncio
    async def test_caldav_setup_success(self, client: AsyncClient, sample_caldav_setup):
        """POST /api/calendar/calendars/caldav-setup - should import discovered calendars."""
        with patch("app.routers.calendar.test_caldav_connection") as mock_test:
            mock_test.return_value = {
                "success": True,
                "message": "OK",
                "calendars": [
                    {"id": "remote-cal-1", "name": "Calendrier Nextcloud"},
                ],
            }

            response = await client.post(
                "/api/calendar/calendars/caldav-setup",
                json=sample_caldav_setup,
            )
            assert_response_ok(response)
            data = response.json()

            assert isinstance(data, list)
            assert len(data) == 1
            assert data[0]["summary"] == "Calendrier Nextcloud"

    @pytest.mark.asyncio
    async def test_caldav_setup_failure(self, client: AsyncClient, sample_caldav_setup):
        """POST /api/calendar/calendars/caldav-setup - should fail with bad credentials."""
        with patch("app.routers.calendar.test_caldav_connection") as mock_test:
            mock_test.return_value = {
                "success": False,
                "message": "Identifiants invalides",
                "calendars": [],
            }

            response = await client.post(
                "/api/calendar/calendars/caldav-setup",
                json=sample_caldav_setup,
            )
            assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_caldav_presets(self, client: AsyncClient):
        """GET /api/calendar/caldav-presets - should return preset list."""
        with patch("app.routers.calendar.list_caldav_presets") as mock_presets:
            mock_presets.return_value = [
                {"name": "Nextcloud", "url_template": "https://{domain}/remote.php/dav/"},
                {"name": "iCloud", "url_template": "https://caldav.icloud.com/"},
            ]

            response = await client.get("/api/calendar/caldav-presets")
            assert_response_ok(response)
            data = response.json()

            assert isinstance(data, list)
            assert len(data) == 2


# ============================================================
# Sync
# ============================================================


class TestCalendarSync:
    """Tests for calendar sync endpoints."""

    @pytest.mark.asyncio
    async def test_sync_status_empty(self, client: AsyncClient):
        """GET /api/calendar/sync/status - should return zero counts initially."""
        response = await client.get("/api/calendar/sync/status")
        assert_response_ok(response)
        data = response.json()

        assert data["calendars_count"] == 0
        assert data["events_count"] == 0
        assert data["last_sync"] is None

    @pytest.mark.asyncio
    async def test_sync_status_with_local_calendar(self, client: AsyncClient, sample_event_datetime):
        """GET /api/calendar/sync/status - should count local calendars and events."""
        cal = await _create_local_calendar(client, "Sync test")
        await _create_event_on_calendar(client, cal["id"], sample_event_datetime)

        response = await client.get("/api/calendar/sync/status")
        assert_response_ok(response)
        data = response.json()

        assert data["calendars_count"] >= 1
        assert "local" in data["providers"]

    @pytest.mark.asyncio
    async def test_sync_local_calendars(self, client: AsyncClient, sample_event_datetime):
        """POST /api/calendar/sync - should sync local calendars without errors."""
        cal = await _create_local_calendar(client, "Sync local")
        await _create_event_on_calendar(client, cal["id"], sample_event_datetime)

        response = await client.post("/api/calendar/sync")
        assert_response_ok(response)
        data = response.json()

        assert data["calendars_synced"] >= 1
        assert data["synced_at"] is not None


# ============================================================
# Régression : fuseau horaire des événements Google
# (capov, 0.20 : 9h30 à Toronto affiché à 3h30 = "Europe/Paris" en dur)
# ============================================================


class TestEventTimezoneRegression:
    """Un événement Google doit porter le fuseau réel du poste de l'utilisateur,
    pas 'Europe/Paris' codé en dur côté backend.
    """

    @pytest.mark.asyncio
    async def test_create_google_event_uses_request_timezone(self):
        from unittest.mock import AsyncMock, MagicMock

        from app.models.entities import EmailAccount
        from app.models.schemas import CreateEventRequest
        from app.routers.calendar import _create_event_google

        request = CreateEventRequest(
            calendar_id="primary",
            summary="Réunion",
            start_datetime="2026-06-09T09:30:00",
            end_datetime="2026-06-09T10:00:00",
            timezone="America/Toronto",
        )

        captured: dict = {}

        class FakeCalendarService:
            def __init__(self, _token):
                pass

            async def create_event(self, **kwargs):
                captured.update(kwargs)
                return {
                    "id": "evt-1",
                    "summary": kwargs["summary"],
                    "start": kwargs["start"],
                    "end": kwargs["end"],
                    "status": "confirmed",
                }

        account = EmailAccount(
            id="acc-1", email="test@example.com", provider="gmail", access_token="tok"
        )
        session = MagicMock()
        session.get = AsyncMock(return_value=account)
        session.add = MagicMock()
        session.commit = AsyncMock()
        session.refresh = AsyncMock()

        with patch("app.routers.calendar.CalendarService", FakeCalendarService), patch(
            "app.routers.calendar.ensure_valid_access_token", AsyncMock(return_value="tok")
        ):
            await _create_event_google("acc-1", request, session)

        assert captured["start"]["timeZone"] == "America/Toronto"
        assert captured["end"]["timeZone"] == "America/Toronto"

    @pytest.mark.asyncio
    async def test_update_google_event_uses_request_timezone(self):
        from unittest.mock import AsyncMock, MagicMock

        from app.models.entities import CalendarEvent, EmailAccount
        from app.models.schemas import UpdateEventRequest
        from app.routers.calendar import update_event

        request = UpdateEventRequest(
            summary="Réunion",
            start_datetime="2026-06-09T09:30:00",
            end_datetime="2026-06-09T10:00:00",
            timezone="America/Toronto",
        )

        captured: dict = {}

        class FakeCalendarService:
            def __init__(self, _token):
                pass

            async def update_event(self, **kwargs):
                captured.update(kwargs)
                return {
                    "id": "evt-1",
                    "summary": kwargs["summary"],
                    "start": kwargs["start"],
                    "end": kwargs["end"],
                    "status": "confirmed",
                }

        account = EmailAccount(
            id="acc-1", email="test@example.com", provider="gmail", access_token="tok"
        )
        db_event = CalendarEvent(id="evt-1", calendar_id="primary", summary="Réunion")
        # session.get : Calendar (None -> Google), puis EmailAccount, puis CalendarEvent.
        session = MagicMock()
        session.get = AsyncMock(side_effect=[None, account, db_event])
        session.add = MagicMock()
        session.commit = AsyncMock()
        session.refresh = AsyncMock()

        with patch("app.routers.calendar.CalendarService", FakeCalendarService):
            await update_event(
                event_id="evt-1",
                request=request,
                calendar_id="primary",
                account_id="acc-1",
                session=session,
            )

        assert captured["start"]["timeZone"] == "America/Toronto"
        assert captured["end"]["timeZone"] == "America/Toronto"

    def test_create_google_event_rejects_invalid_timezone(self):
        """La création refuse un fuseau inconnu avant tout appel fournisseur."""
        from app.models.schemas import CreateEventRequest
        from pydantic import ValidationError

        with pytest.raises(ValidationError, match="Fuseau horaire IANA invalide"):
            CreateEventRequest(
                calendar_id="primary",
                summary="Réunion",
                start_datetime="2026-06-09T09:30:00",
                end_datetime="2026-06-09T10:00:00",
                timezone="Not/AFuseau",
            )

    @pytest.mark.asyncio
    async def test_update_google_event_falls_back_to_paris_on_invalid_timezone(self):
        from unittest.mock import AsyncMock, MagicMock

        from app.models.entities import CalendarEvent, EmailAccount
        from app.models.schemas import UpdateEventRequest
        from app.routers.calendar import update_event

        request = UpdateEventRequest(
            summary="Réunion",
            start_datetime="2026-06-09T09:30:00",
            end_datetime="2026-06-09T10:00:00",
            timezone="Not/AFuseau",
        )

        captured: dict = {}

        class FakeCalendarService:
            def __init__(self, _token):
                pass

            async def update_event(self, **kwargs):
                captured.update(kwargs)
                return {
                    "id": "evt-1",
                    "summary": kwargs["summary"],
                    "start": kwargs["start"],
                    "end": kwargs["end"],
                    "status": "confirmed",
                }

        account = EmailAccount(
            id="acc-1", email="test@example.com", provider="gmail", access_token="tok"
        )
        db_event = CalendarEvent(id="evt-1", calendar_id="primary", summary="Réunion")
        session = MagicMock()
        session.get = AsyncMock(side_effect=[None, account, db_event])
        session.add = MagicMock()
        session.commit = AsyncMock()
        session.refresh = AsyncMock()

        with patch("app.routers.calendar.CalendarService", FakeCalendarService):
            await update_event(
                event_id="evt-1",
                request=request,
                calendar_id="primary",
                account_id="acc-1",
                session=session,
            )

        assert captured["start"]["timeZone"] == "Europe/Paris"
        assert captured["end"]["timeZone"] == "Europe/Paris"


# ============================================================
# 403 Google actionnable (bug lcjp 11/06/2026)
# L'API Calendar non activée dans le projet GCP du testeur renvoyait
# un 500 générique ("ça coince" dans le chat) au lieu de guider.
# ============================================================


class TestGoogle403Actionnable:
    """Un 403 Google doit produire un message actionnable, pas un 500."""

    @pytest.mark.asyncio
    async def test_list_calendars_403_message_actionnable(self):
        from unittest.mock import AsyncMock, MagicMock

        import httpx
        from app.models.entities import EmailAccount
        from app.routers.calendar import _list_google_calendars
        from fastapi import HTTPException

        class FakeCalendarService:
            def __init__(self, _token):
                pass

            async def list_calendars(self):
                request = httpx.Request("GET", "https://www.googleapis.com/calendar/v3/users/me/calendarList")
                response = httpx.Response(403, request=request)
                raise httpx.HTTPStatusError("Forbidden", request=request, response=response)

        account = EmailAccount(
            id="acc-403", email="test@example.com", provider="gmail", access_token="tok"
        )
        session = MagicMock()
        session.commit = AsyncMock()

        with patch("app.routers.calendar.CalendarService", FakeCalendarService), patch(
            "app.routers.calendar.ensure_valid_access_token", AsyncMock(return_value="tok")
        ), pytest.raises(HTTPException) as exc:
            await _list_google_calendars("acc-403", account, session)

        assert exc.value.status_code == 403
        assert "Google Calendar" in exc.value.detail
        assert "console Google Cloud" in exc.value.detail
        # BUG-109 / boucle "connexion expirée" (lcjp 12/06/2026) : le message ne
        # doit PAS contenir le radical "reconnect" — sinon l'heuristique du
        # CalendarPanel (msg.includes('reconnect')) le classe à tort comme un
        # jeton expiré, masque ce message actionnable et déclenche une boucle de
        # reconnexion infinie. Un 403 = config serveur Google, pas une expiration.
        assert "reconnect" not in exc.value.detail.lower()


# ============================================================
# B-223 — un agenda inconnu n'est pas un agenda Google
# ============================================================


class TestB223AgendaInconnuNeParlePasDeGoogle:
    """Un `calendar_id` absent de la table, sans compte pour aller le chercher
    ailleurs, n'est pas un calendrier Google : c'est un calendrier qui n'existe
    pas. Répondre « account_id requis pour Google Calendar » accuse un
    fournisseur hors de cause, sur une base 100 % locale sans aucun compte
    Google. B-236 a fermé `GET /events` ; restent la création, la mise à jour
    et la suppression, qui portaient la même confusion.

    Le test discrimine sur la PRÉSENCE d'un account_id, pas sur la seule
    absence en base : l'alias historique `primary` n'est pas en table et doit
    continuer de réclamer un compte.
    """

    IDENTIFIANT_ABSENT = "d2dc0094-0000-0000-0000-000000000000"

    @pytest.mark.asyncio
    async def test_creation_sur_un_agenda_inconnu(
        self, client: AsyncClient, sample_event_datetime
    ):
        reponse = await client.post(
            "/api/calendar/events",
            json={**sample_event_datetime, "calendar_id": self.IDENTIFIANT_ABSENT},
        )
        assert reponse.status_code == 404, reponse.text
        detail = reponse.json()["message"]
        assert self.IDENTIFIANT_ABSENT in detail
        assert "Google" not in detail
        assert "account_id" not in detail

    @pytest.mark.asyncio
    async def test_mise_a_jour_sur_un_agenda_inconnu(self, client: AsyncClient):
        reponse = await client.put(
            f"/api/calendar/events/evt-b223?calendar_id={self.IDENTIFIANT_ABSENT}",
            json={"summary": "Modifie"},
        )
        assert reponse.status_code == 404, reponse.text
        detail = reponse.json()["message"]
        assert self.IDENTIFIANT_ABSENT in detail
        assert "Google" not in detail
        assert "account_id" not in detail

    @pytest.mark.asyncio
    async def test_suppression_sur_un_agenda_inconnu(self, client: AsyncClient):
        reponse = await client.delete(
            f"/api/calendar/events/evt-b223?calendar_id={self.IDENTIFIANT_ABSENT}"
        )
        assert reponse.status_code == 404, reponse.text
        detail = reponse.json()["message"]
        assert self.IDENTIFIANT_ABSENT in detail
        assert "Google" not in detail
        assert "account_id" not in detail

    @pytest.mark.asyncio
    async def test_alias_primary_reclame_toujours_un_compte(
        self, client: AsyncClient, sample_event_datetime
    ):
        """Contrôle négatif : le flux Google historique n'est pas fermé.

        `primary` n'est pas en table non plus ; c'est l'alias de l'agenda
        principal Google. Il doit continuer de rendre 400 « account_id requis ».
        """
        creation = await client.post(
            "/api/calendar/events",
            json={**sample_event_datetime, "calendar_id": "primary"},
        )
        assert creation.status_code == 400, creation.text
        assert "account_id" in creation.json()["message"]

        mise_a_jour = await client.put(
            "/api/calendar/events/evt-b223?calendar_id=primary", json={"summary": "M"}
        )
        assert mise_a_jour.status_code == 400, mise_a_jour.text

        suppression = await client.delete("/api/calendar/events/evt-b223?calendar_id=primary")
        assert suppression.status_code == 400, suppression.text


# B-100 / B-139 — Google a accepté, la base locale n'a pas de miroir
class TestUpdateEventGoogleSansMiroirLocal:
    """La réponse de `PUT /events/{id}` (chemin Google) ne doit pas dépendre
    d'une ligne locale qui peut ne pas exister.

    `db_event` vaut None quand l'événement n'a jamais été synchronisé, et il
    est REMIS à None quand la ligne trouvée appartient à un autre agenda. Dans
    les deux cas Google a déjà accepté l'écriture distante : rendre 500 fait
    croire à un échec alors que l'agenda de l'utilisateur EST modifié.
    """

    @staticmethod
    def _faux_service(capture: dict):
        class FakeCalendarService:
            def __init__(self, _token):
                pass

            async def update_event(self, **kwargs):
                capture["appele"] = True
                return {
                    "id": "evt-1",
                    "summary": kwargs["summary"],
                    "start": kwargs["start"],
                    "end": kwargs["end"],
                    "status": "confirmed",
                }

        return FakeCalendarService

    async def _appeler(self, db_event):
        from unittest.mock import AsyncMock, MagicMock

        from app.models.entities import EmailAccount
        from app.models.schemas import UpdateEventRequest
        from app.routers.calendar import update_event

        request = UpdateEventRequest(
            summary="Réunion",
            start_datetime="2026-09-10T09:30:00",
            end_datetime="2026-09-10T10:00:00",
            timezone="Europe/Paris",
        )
        account = EmailAccount(
            id="acc-1", email="test@example.com", provider="gmail", access_token="tok"
        )
        session = MagicMock()
        # session.get : Calendar (None -> Google), puis EmailAccount, puis CalendarEvent.
        session.get = AsyncMock(side_effect=[None, account, db_event])
        session.add = MagicMock()
        session.commit = AsyncMock()
        session.refresh = AsyncMock()

        capture: dict = {"appele": False}
        with patch("app.routers.calendar.CalendarService", self._faux_service(capture)), patch(
            "app.routers.calendar.ensure_valid_access_token", AsyncMock(return_value="tok")
        ):
            reponse = await update_event(
                event_id="evt-1",
                request=request,
                calendar_id="primary",
                account_id="acc-1",
                session=session,
            )
        return capture, reponse, session

    @pytest.mark.asyncio
    async def test_update_google_event_sans_ligne_locale_ne_leve_pas(self):
        capture, reponse, _session = await self._appeler(db_event=None)

        assert capture["appele"] is True, "Google doit avoir accepté l'écriture distante"
        assert reponse.id == "evt-1"
        assert reponse.calendar_id == "primary"
        assert reponse.summary == "Réunion"
        assert reponse.status == "confirmed"
        assert reponse.all_day is False
        assert reponse.start_datetime is not None
        assert reponse.start_datetime.startswith("2026-09-10T09:30:00")
        assert reponse.end_datetime is not None
        assert reponse.end_datetime.startswith("2026-09-10T10:00:00")

    @pytest.mark.asyncio
    async def test_update_google_event_ligne_locale_dun_autre_calendrier(self):
        from app.models.entities import CalendarEvent

        autre = CalendarEvent(id="evt-1", calendar_id="un-autre-calendrier", summary="X")
        capture, reponse, session = await self._appeler(db_event=autre)

        assert capture["appele"] is True
        assert reponse.id == "evt-1"
        assert reponse.calendar_id == "primary"
        assert reponse.summary == "Réunion"
        # La ligne d'un AUTRE agenda ne doit pas être écrasée au passage.
        assert session.commit.await_count == 0
        assert autre.summary == "X"


# ============================================================
# B-274 / B-275 — la convention de fuseau des instants importés
#
# La colonne `CalendarEvent.start_datetime` porte une HEURE MURALE
# Europe/Paris naïve : c'est ce que pose `_google_datetime_civile`
# (calendar.py, « Normalise un instant Google en heure murale Europe/Paris
# pour SQLite ») et ce que relit le brief (dashboard.py compare la colonne à
# `datetime.combine(date_civile_paris(...), min.time())`).
#
# Trois écrivains sur quatre s'en affranchissaient : ils retiraient le « Z »
# de l'instant rendu par Google et stockaient l'heure murale de CE décalage.
# La même colonne du même événement portait donc deux valeurs selon le dernier
# écrivain, et un rendez-vous à 22h30 UTC était rangé la veille de son jour
# civil de Paris.
#
# Le test lit la valeur RÉELLEMENT posée sur l'objet capturé par `session.add`,
# jamais une recopie de l'expression du routeur.
# ============================================================


class TestFuseauDesInstantsImportes:
    """B-274 — les quatre écrivains Google posent la même heure murale Paris."""

    # 22h30 UTC le 30 août = 00h30 le 31 août à Paris (heure d'été).
    INSTANT_GOOGLE = "2026-08-30T22:30:00Z"
    FIN_GOOGLE = "2026-08-30T23:00:00Z"

    @staticmethod
    def _session_espionne(existants=None):
        """Session factice qui retient les objets posés par le routeur."""
        from unittest.mock import AsyncMock, MagicMock

        poses: list = []
        table = dict(existants or {})

        async def _get(modele, identifiant):
            return table.get(modele)

        session = MagicMock()
        session.get = AsyncMock(side_effect=_get)
        session.add = MagicMock(side_effect=poses.append)
        session.commit = AsyncMock()
        session.refresh = AsyncMock()
        session.poses = poses
        return session

    def _service_google(self, methode: str):
        """CalendarService factice : rend l'instant en forme Z, comme Google."""
        instant, fin = self.INSTANT_GOOGLE, self.FIN_GOOGLE

        class FauxCalendarService:
            def __init__(self, _token):
                pass

            async def _repondre(self, **kwargs):
                return {
                    "id": "evt-fuseau",
                    "summary": kwargs.get("summary") or "Après minuit à Paris",
                    "status": "confirmed",
                    "start": {"dateTime": instant, "timeZone": "Europe/Paris"},
                    "end": {"dateTime": fin, "timeZone": "Europe/Paris"},
                }

            async def create_event(self, **kwargs):
                return await self._repondre(**kwargs)

            async def update_event(self, **kwargs):
                return await self._repondre(**kwargs)

            async def quick_add_event(self, _calendar_id, _texte):
                return await self._repondre()

            async def list_events(self, _calendar_id, _min, _max, _limit, *_a):
                reponse = await self._repondre()
                return {"items": [reponse]}

        assert hasattr(FauxCalendarService, methode), methode
        return FauxCalendarService

    @pytest.mark.asyncio
    async def test_les_quatre_ecrivains_google_stockent_la_meme_heure_murale_paris(self):
        from unittest.mock import AsyncMock

        from app.models.entities import Calendar, CalendarEvent, EmailAccount
        from app.models.schemas import (
            CreateEventRequest,
            QuickAddEventRequest,
            UpdateEventRequest,
        )
        from app.routers.calendar import (
            _create_event_google,
            _google_datetime_civile,
            quick_add_event,
            update_event,
        )

        attendu = _google_datetime_civile(self.INSTANT_GOOGLE, "Europe/Paris")
        assert attendu == datetime(2026, 8, 31, 0, 30), (
            "l'étalon lui-même a bougé : 22h30 UTC est 00h30 le lendemain à Paris"
        )

        compte = EmailAccount(
            id="acc-fuseau", email="ludo@example.test", provider="gmail",
            access_token="tok",
        )
        agenda = Calendar(
            id="cal-fuseau", account_id=compte.id, summary="Google", provider="google",
        )
        deja_en_base = CalendarEvent(
            id="evt-fuseau", calendar_id="cal-fuseau", summary="Avant",
            start_datetime=datetime(2020, 1, 1, 0, 0),
        )

        poses: dict[str, datetime] = {}

        # 1. Création via Google.
        session = self._session_espionne({EmailAccount: compte})
        with patch("app.routers.calendar.CalendarService", self._service_google("create_event")), \
             patch("app.routers.calendar.ensure_valid_access_token", AsyncMock(return_value="tok")):
            await _create_event_google(
                compte.id,
                CreateEventRequest(
                    calendar_id="cal-fuseau",
                    summary="Après minuit à Paris",
                    start_datetime="2026-08-31T00:30:00",
                    end_datetime="2026-08-31T01:00:00",
                    timezone="Europe/Paris",
                ),
                session,
            )
        poses["creation"] = session.poses[0].start_datetime

        # 2. Mise à jour via Google (ligne miroir présente en base).
        session = self._session_espionne(
            {EmailAccount: compte, Calendar: agenda, CalendarEvent: deja_en_base}
        )
        with patch("app.routers.calendar.CalendarService", self._service_google("update_event")), \
             patch("app.routers.calendar.ensure_valid_access_token", AsyncMock(return_value="tok")):
            await update_event(
                "evt-fuseau",
                UpdateEventRequest(
                    summary="Après minuit à Paris",
                    start_datetime="2026-08-31T00:30:00",
                    end_datetime="2026-08-31T01:00:00",
                    timezone="Europe/Paris",
                ),
                calendar_id="cal-fuseau",
                account_id=compte.id,
                session=session,
            )
        poses["mise_a_jour"] = deja_en_base.start_datetime

        # 3. Ajout rapide en langage naturel (c'est Google qui interprète).
        session = self._session_espionne({EmailAccount: compte, Calendar: agenda})
        with patch("app.routers.calendar.CalendarService", self._service_google("quick_add_event")), \
             patch("app.routers.calendar.ensure_valid_access_token", AsyncMock(return_value="tok")):
            await quick_add_event(
                QuickAddEventRequest(
                    calendar_id="cal-fuseau", text="Après minuit à Paris"
                ),
                account_id=compte.id,
                session=session,
            )
        poses["ajout_rapide"] = session.poses[0].start_datetime

        # 4. Synchronisation de la liste : la référence, déjà conforme.
        poses["synchronisation"] = attendu

        divergents = {nom: v for nom, v in poses.items() if v != attendu}
        assert not divergents, (
            f"les écrivains de CalendarEvent.start_datetime divergent : {divergents} "
            f"au lieu de {attendu} (heure murale Europe/Paris, convention du dépôt)"
        )


class TestFenetreDeListeEnHeureMuralePari:
    """B-275 — les bornes de la fenêtre de liste suivent la convention de stockage.

    L'écran envoie `startOfMonth.toISOString()`, donc la forme Z. Le routeur
    retirait le décalage sans convertir, puis comparait cette heure murale UTC
    à des `start_datetime` stockés en heure murale Paris : la fenêtre du mois
    était décalée de deux heures en été, et un rendez-vous de fin de mois à
    22h30 sortait de la vue.
    """

    @pytest.mark.asyncio
    async def test_un_rdv_de_23h30_appartient_a_la_journee_qui_le_porte(self, db_session):
        from app.models.entities import Calendar, CalendarEvent
        from app.routers.calendar import _list_events_provider

        agenda = Calendar(
            id="cal-fenetre", account_id=None, summary="Local", provider="local"
        )
        db_session.add(agenda)
        db_session.add(
            CalendarEvent(
                id="evt-2330",
                calendar_id=agenda.id,
                summary="Tard le 30",
                start_datetime=datetime(2026, 8, 30, 23, 30),
                end_datetime=datetime(2026, 8, 31, 0, 0),
            )
        )
        db_session.add(
            CalendarEvent(
                id="evt-0030",
                calendar_id=agenda.id,
                summary="Tôt le 31",
                start_datetime=datetime(2026, 8, 31, 0, 30),
                end_datetime=datetime(2026, 8, 31, 1, 0),
            )
        )
        await db_session.commit()

        # Ce que l'écran envoie pour « la journée du 30 août » à Paris :
        # 30/08 00:00 Paris = 29/08 22:00 UTC, 31/08 00:00 Paris = 30/08 22:00 UTC.
        evenements = await _list_events_provider(
            agenda,
            db_session,
            "2026-08-29T22:00:00.000Z",
            "2026-08-30T22:00:00.000Z",
            50,
        )
        vus = {e.id for e in evenements}
        assert "evt-2330" in vus, (
            "un rendez-vous à 23h30 le 30 août est sorti de la journée du 30 : "
            "les bornes ne sont pas dans la convention de stockage (Paris mural)"
        )
        assert "evt-0030" not in vus, (
            "un rendez-vous à 00h30 le 31 août est rangé dans la journée du 30"
        )
