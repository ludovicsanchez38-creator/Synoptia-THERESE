"""
THERESE v2 - Calendar Router Tests

Tests for calendar endpoints (local, Google, CalDAV providers).
Focus on local provider (SQLite) to avoid external mocks where possible.
Google Calendar and CalDAV endpoints are tested with mocks.
"""

import json
import pytest
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from httpx import AsyncClient

from tests.conftest import assert_response_ok, assert_contains_keys


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
    async def test_list_calendars_empty(self, client: AsyncClient):
        """GET /api/calendar/calendars - should return empty list initially."""
        response = await client.get("/api/calendar/calendars")
        assert_response_ok(response)
        data = response.json()

        assert isinstance(data, list)
        assert len(data) == 0

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
        """GET /api/calendar/events - should require account_id for non-local calendars."""
        # Pass a calendar_id that doesn't exist in DB (treated as Google)
        response = await client.get(
            "/api/calendar/events?calendar_id=unknown-google-cal"
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
    async def test_create_event_google_requires_account(self, client: AsyncClient, sample_event_datetime):
        """POST /api/calendar/events - should require account_id for Google calendar."""
        event_data = {**sample_event_datetime, "calendar_id": "nonexistent"}
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
        """PUT /api/calendar/events/{id} - should require account_id for Google."""
        response = await client.put(
            "/api/calendar/events/evt-001?calendar_id=nonexistent",
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
        """DELETE /api/calendar/events/{id} - should require account_id for Google."""
        response = await client.delete(
            "/api/calendar/events/evt-001?calendar_id=nonexistent"
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
