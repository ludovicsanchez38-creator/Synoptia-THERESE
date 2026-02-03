"""
THERESE v2 - CRM Router Tests (Full)

Tests for CRM pipeline, activities, deliverables, export/import, and sync endpoints.
Contacts are created via /api/memory/contacts (memory router) or /api/crm/contacts.
External services (Google Sheets, LLM) are mocked.
"""

import io
import json
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from httpx import AsyncClient

from tests.conftest import assert_response_ok, assert_contains_keys


# ============================================================
# Fixtures
# ============================================================


@pytest.fixture
def sample_crm_contact():
    """Sample CRM contact creation data."""
    return {
        "first_name": "Marie",
        "last_name": "Dupont",
        "company": "Synoptia",
        "email": "marie@synoptia.fr",
        "phone": "+33612345678",
        "source": "website",
        "stage": "contact",
    }


@pytest.fixture
def sample_crm_contact_2():
    """Second sample CRM contact for list tests."""
    return {
        "first_name": "Pierre",
        "last_name": "Martin",
        "company": "TechCorp",
        "email": "pierre@techcorp.fr",
        "phone": "+33698765432",
        "source": "linkedin",
        "stage": "discovery",
    }


@pytest.fixture
def sample_memory_contact():
    """Sample contact via memory router (first_name only required)."""
    return {
        "first_name": "Jean",
        "last_name": "Dupont",
        "company": "Synoptia",
        "email": "jean@synoptia.fr",
        "phone": "+33612345678",
        "notes": "Contact test CRM",
        "tags": ["client", "vip"],
    }


@pytest.fixture
def sample_project():
    """Sample project data."""
    return {
        "name": "Projet Formation IA",
        "description": "Formation IA pour 15 collaborateurs",
        "status": "active",
        "budget": 2490.0,
        "tags": ["formation", "ia"],
    }


@pytest.fixture
def sample_activity():
    """Sample activity data."""
    return {
        "type": "call",
        "title": "Appel decouverte",
        "description": "Premier appel pour comprendre les besoins",
        "extra_data": None,
    }


@pytest.fixture
def sample_deliverable():
    """Sample deliverable data."""
    return {
        "title": "Rapport audit IA",
        "description": "Audit flash des processus IA existants",
        "status": "a_faire",
        "due_date": "2026-03-15",
    }


async def _create_crm_contact(client: AsyncClient, data: dict) -> dict:
    """Helper to create a contact via CRM router."""
    response = await client.post("/api/crm/contacts", json=data)
    assert response.status_code == 200, f"Failed to create CRM contact: {response.text}"
    return response.json()


async def _create_memory_contact(client: AsyncClient, data: dict) -> dict:
    """Helper to create a contact via memory router."""
    response = await client.post("/api/memory/contacts", json=data)
    assert response.status_code == 200, f"Failed to create contact: {response.text}"
    return response.json()


async def _create_project(client: AsyncClient, data: dict, contact_id: str = None) -> dict:
    """Helper to create a project."""
    project_data = {**data}
    if contact_id:
        project_data["contact_id"] = contact_id
    response = await client.post("/api/memory/projects", json=project_data)
    assert response.status_code == 200, f"Failed to create project: {response.text}"
    return response.json()


# ============================================================
# CRM Contacts
# ============================================================


class TestCRMContacts:
    """Tests for CRM contact CRUD operations."""

    @pytest.mark.asyncio
    async def test_create_crm_contact(self, client: AsyncClient, sample_crm_contact):
        """POST /api/crm/contacts - should create a CRM contact."""
        response = await client.post("/api/crm/contacts", json=sample_crm_contact)
        assert_response_ok(response)
        data = response.json()

        assert data["first_name"] == "Marie"
        assert data["last_name"] == "Dupont"
        assert data["company"] == "Synoptia"
        assert data["email"] == "marie@synoptia.fr"
        assert data["stage"] == "contact"
        assert data["score"] == 50
        assert "id" in data

    @pytest.mark.asyncio
    async def test_create_crm_contact_default_source(self, client: AsyncClient):
        """POST /api/crm/contacts - should default source to THERESE."""
        response = await client.post("/api/crm/contacts", json={
            "first_name": "Test",
        })
        assert_response_ok(response)
        data = response.json()

        assert data["source"] == "THERESE"

    @pytest.mark.asyncio
    async def test_create_crm_contact_with_custom_source(self, client: AsyncClient, sample_crm_contact):
        """POST /api/crm/contacts - should use provided source."""
        contact_data = {**sample_crm_contact, "source": "referral"}
        response = await client.post("/api/crm/contacts", json=contact_data)
        assert_response_ok(response)

        assert response.json()["source"] == "referral"

    @pytest.mark.asyncio
    async def test_list_contacts_via_memory(self, client: AsyncClient, sample_crm_contact):
        """CRM contacts should appear in memory contacts list."""
        await _create_crm_contact(client, sample_crm_contact)

        response = await client.get("/api/memory/contacts")
        assert_response_ok(response)
        data = response.json()

        assert isinstance(data, list)
        assert len(data) >= 1
        emails = [c.get("email") for c in data]
        assert "marie@synoptia.fr" in emails


# ============================================================
# Pipeline (Stage & Scoring)
# ============================================================


class TestCRMPipeline:
    """Tests for pipeline stage management and scoring."""

    @pytest.mark.asyncio
    async def test_update_contact_stage(self, client: AsyncClient, sample_crm_contact):
        """PATCH /api/crm/contacts/{id}/stage - should update stage."""
        contact = await _create_crm_contact(client, sample_crm_contact)
        contact_id = contact["id"]

        response = await client.patch(
            f"/api/crm/contacts/{contact_id}/stage",
            json={"stage": "discovery"},
        )
        assert_response_ok(response)
        data = response.json()

        assert data["stage"] == "discovery"

    @pytest.mark.asyncio
    async def test_update_contact_stage_not_found(self, client: AsyncClient):
        """PATCH /api/crm/contacts/{id}/stage - should 404 for nonexistent contact."""
        response = await client.patch(
            "/api/crm/contacts/nonexistent/stage",
            json={"stage": "discovery"},
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_stage_creates_activity(self, client: AsyncClient, sample_crm_contact):
        """Changing stage should create a stage_change activity."""
        contact = await _create_crm_contact(client, sample_crm_contact)
        contact_id = contact["id"]

        await client.patch(
            f"/api/crm/contacts/{contact_id}/stage",
            json={"stage": "proposition"},
        )

        # Check activities
        response = await client.get(f"/api/crm/activities?contact_id={contact_id}")
        assert_response_ok(response)
        activities = response.json()

        # Should have at least one stage_change activity
        stage_activities = [a for a in activities if a["type"] == "stage_change"]
        assert len(stage_activities) >= 1

    @pytest.mark.asyncio
    async def test_pipeline_stats_empty(self, client: AsyncClient):
        """GET /api/crm/pipeline/stats - should return empty stats."""
        response = await client.get("/api/crm/pipeline/stats")
        assert_response_ok(response)
        data = response.json()

        assert "total_contacts" in data
        assert "stages" in data

    @pytest.mark.asyncio
    async def test_pipeline_stats_with_contacts(
        self, client: AsyncClient, sample_crm_contact, sample_crm_contact_2
    ):
        """GET /api/crm/pipeline/stats - should count contacts by stage."""
        await _create_crm_contact(client, sample_crm_contact)
        await _create_crm_contact(client, sample_crm_contact_2)

        response = await client.get("/api/crm/pipeline/stats")
        assert_response_ok(response)
        data = response.json()

        assert data["total_contacts"] >= 2

    @pytest.mark.asyncio
    async def test_recalculate_score(self, client: AsyncClient, sample_crm_contact):
        """POST /api/crm/contacts/{id}/recalculate-score - should recalculate."""
        contact = await _create_crm_contact(client, sample_crm_contact)
        contact_id = contact["id"]

        response = await client.post(
            f"/api/crm/contacts/{contact_id}/recalculate-score"
        )
        assert_response_ok(response)
        data = response.json()

        assert_contains_keys(data, ["contact_id", "old_score", "new_score", "reason"])
        assert data["contact_id"] == contact_id
        assert data["reason"] == "manual_recalculation"

    @pytest.mark.asyncio
    async def test_recalculate_score_not_found(self, client: AsyncClient):
        """POST /api/crm/contacts/{id}/recalculate-score - should 404."""
        response = await client.post(
            "/api/crm/contacts/nonexistent/recalculate-score"
        )
        assert response.status_code == 404


# ============================================================
# Activities
# ============================================================


class TestCRMActivities:
    """Tests for activity timeline management."""

    @pytest.mark.asyncio
    async def test_list_activities_empty(self, client: AsyncClient):
        """GET /api/crm/activities - should return empty list."""
        response = await client.get("/api/crm/activities")
        assert_response_ok(response)
        data = response.json()

        assert isinstance(data, list)
        assert len(data) == 0

    @pytest.mark.asyncio
    async def test_create_activity(self, client: AsyncClient, sample_crm_contact, sample_activity):
        """POST /api/crm/activities - should create an activity."""
        contact = await _create_crm_contact(client, sample_crm_contact)

        activity_data = {**sample_activity, "contact_id": contact["id"]}
        response = await client.post("/api/crm/activities", json=activity_data)
        assert_response_ok(response)
        data = response.json()

        assert data["type"] == "call"
        assert data["title"] == "Appel decouverte"
        assert data["contact_id"] == contact["id"]
        assert "id" in data

    @pytest.mark.asyncio
    async def test_create_activity_contact_not_found(self, client: AsyncClient, sample_activity):
        """POST /api/crm/activities - should 404 if contact doesn't exist."""
        activity_data = {**sample_activity, "contact_id": "nonexistent"}
        response = await client.post("/api/crm/activities", json=activity_data)
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_list_activities_by_contact(
        self, client: AsyncClient, sample_crm_contact, sample_activity
    ):
        """GET /api/crm/activities?contact_id=xxx - should filter by contact."""
        contact = await _create_crm_contact(client, sample_crm_contact)
        activity_data = {**sample_activity, "contact_id": contact["id"]}
        await client.post("/api/crm/activities", json=activity_data)

        response = await client.get(
            f"/api/crm/activities?contact_id={contact['id']}"
        )
        assert_response_ok(response)
        data = response.json()

        assert len(data) >= 1
        assert all(a["contact_id"] == contact["id"] for a in data)

    @pytest.mark.asyncio
    async def test_list_activities_by_type(
        self, client: AsyncClient, sample_crm_contact, sample_activity
    ):
        """GET /api/crm/activities?type=call - should filter by type."""
        contact = await _create_crm_contact(client, sample_crm_contact)
        activity_data = {**sample_activity, "contact_id": contact["id"]}
        await client.post("/api/crm/activities", json=activity_data)

        response = await client.get("/api/crm/activities?type=call")
        assert_response_ok(response)
        data = response.json()

        assert all(a["type"] == "call" for a in data)

    @pytest.mark.asyncio
    async def test_delete_activity(self, client: AsyncClient, sample_crm_contact, sample_activity):
        """DELETE /api/crm/activities/{id} - should delete activity."""
        contact = await _create_crm_contact(client, sample_crm_contact)
        activity_data = {**sample_activity, "contact_id": contact["id"]}
        create_resp = await client.post("/api/crm/activities", json=activity_data)
        activity_id = create_resp.json()["id"]

        response = await client.delete(f"/api/crm/activities/{activity_id}")
        assert_response_ok(response)

        assert response.json()["message"] == "Activity deleted successfully"

    @pytest.mark.asyncio
    async def test_delete_activity_not_found(self, client: AsyncClient):
        """DELETE /api/crm/activities/{id} - should 404."""
        response = await client.delete("/api/crm/activities/nonexistent")
        assert response.status_code == 404


# ============================================================
# Deliverables
# ============================================================


class TestCRMDeliverables:
    """Tests for deliverable management."""

    @pytest.mark.asyncio
    async def test_list_deliverables_empty(self, client: AsyncClient):
        """GET /api/crm/deliverables - should return empty list."""
        response = await client.get("/api/crm/deliverables")
        assert_response_ok(response)
        data = response.json()

        assert isinstance(data, list)
        assert len(data) == 0

    @pytest.mark.asyncio
    async def test_create_deliverable(
        self, client: AsyncClient, sample_project, sample_deliverable
    ):
        """POST /api/crm/deliverables - should create a deliverable."""
        project = await _create_project(client, sample_project)

        deliverable_data = {**sample_deliverable, "project_id": project["id"]}
        response = await client.post("/api/crm/deliverables", json=deliverable_data)
        assert_response_ok(response)
        data = response.json()

        assert data["title"] == "Rapport audit IA"
        assert data["status"] == "a_faire"
        assert data["project_id"] == project["id"]
        assert "id" in data

    @pytest.mark.asyncio
    async def test_create_deliverable_project_not_found(self, client: AsyncClient, sample_deliverable):
        """POST /api/crm/deliverables - should 404 if project doesn't exist."""
        deliverable_data = {**sample_deliverable, "project_id": "nonexistent"}
        response = await client.post("/api/crm/deliverables", json=deliverable_data)
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_list_deliverables_by_project(
        self, client: AsyncClient, sample_project, sample_deliverable
    ):
        """GET /api/crm/deliverables?project_id=xxx - should filter by project."""
        project = await _create_project(client, sample_project)
        deliverable_data = {**sample_deliverable, "project_id": project["id"]}
        await client.post("/api/crm/deliverables", json=deliverable_data)

        response = await client.get(
            f"/api/crm/deliverables?project_id={project['id']}"
        )
        assert_response_ok(response)
        data = response.json()

        assert len(data) >= 1
        assert all(d["project_id"] == project["id"] for d in data)

    @pytest.mark.asyncio
    async def test_update_deliverable(
        self, client: AsyncClient, sample_project, sample_deliverable
    ):
        """PUT /api/crm/deliverables/{id} - should update deliverable."""
        project = await _create_project(client, sample_project)
        deliverable_data = {**sample_deliverable, "project_id": project["id"]}
        create_resp = await client.post("/api/crm/deliverables", json=deliverable_data)
        deliv_id = create_resp.json()["id"]

        response = await client.put(
            f"/api/crm/deliverables/{deliv_id}",
            json={"title": "Rapport modifie", "status": "en_cours"},
        )
        assert_response_ok(response)
        data = response.json()

        assert data["title"] == "Rapport modifie"
        assert data["status"] == "en_cours"

    @pytest.mark.asyncio
    async def test_update_deliverable_valide_sets_completed_at(
        self, client: AsyncClient, sample_project, sample_deliverable
    ):
        """PUT /api/crm/deliverables/{id} - status 'valide' should set completed_at."""
        project = await _create_project(client, sample_project)
        deliverable_data = {**sample_deliverable, "project_id": project["id"]}
        create_resp = await client.post("/api/crm/deliverables", json=deliverable_data)
        deliv_id = create_resp.json()["id"]

        response = await client.put(
            f"/api/crm/deliverables/{deliv_id}",
            json={"status": "valide"},
        )
        assert_response_ok(response)
        data = response.json()

        assert data["status"] == "valide"
        assert data["completed_at"] is not None

    @pytest.mark.asyncio
    async def test_update_deliverable_not_found(self, client: AsyncClient):
        """PUT /api/crm/deliverables/{id} - should 404."""
        response = await client.put(
            "/api/crm/deliverables/nonexistent",
            json={"title": "Updated"},
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_deliverable(
        self, client: AsyncClient, sample_project, sample_deliverable
    ):
        """DELETE /api/crm/deliverables/{id} - should delete deliverable."""
        project = await _create_project(client, sample_project)
        deliverable_data = {**sample_deliverable, "project_id": project["id"]}
        create_resp = await client.post("/api/crm/deliverables", json=deliverable_data)
        deliv_id = create_resp.json()["id"]

        response = await client.delete(f"/api/crm/deliverables/{deliv_id}")
        assert_response_ok(response)

        assert response.json()["message"] == "Deliverable deleted successfully"

    @pytest.mark.asyncio
    async def test_delete_deliverable_not_found(self, client: AsyncClient):
        """DELETE /api/crm/deliverables/{id} - should 404."""
        response = await client.delete("/api/crm/deliverables/nonexistent")
        assert response.status_code == 404


# ============================================================
# Export
# ============================================================


class TestCRMExport:
    """Tests for CRM export endpoints."""

    @pytest.mark.asyncio
    async def test_export_contacts_csv(self, client: AsyncClient, sample_crm_contact):
        """POST /api/crm/export/contacts?format=csv - should export CSV."""
        await _create_crm_contact(client, sample_crm_contact)

        response = await client.post("/api/crm/export/contacts?format=csv")
        assert_response_ok(response)

        assert "text/csv" in response.headers.get("content-type", "")
        assert "attachment" in response.headers.get("content-disposition", "")
        # CSV should contain at least header + 1 row
        content = response.text
        lines = content.strip().split("\n")
        assert len(lines) >= 2

    @pytest.mark.asyncio
    async def test_export_contacts_json(self, client: AsyncClient, sample_crm_contact):
        """POST /api/crm/export/contacts?format=json - should export JSON."""
        await _create_crm_contact(client, sample_crm_contact)

        response = await client.post("/api/crm/export/contacts?format=json")
        assert_response_ok(response)

        assert "application/json" in response.headers.get("content-type", "")

    @pytest.mark.asyncio
    async def test_export_contacts_empty(self, client: AsyncClient):
        """POST /api/crm/export/contacts - should export even with no contacts."""
        response = await client.post("/api/crm/export/contacts?format=csv")
        assert_response_ok(response)

    @pytest.mark.asyncio
    async def test_export_projects_csv(self, client: AsyncClient, sample_project):
        """POST /api/crm/export/projects?format=csv - should export projects CSV."""
        await _create_project(client, sample_project)

        response = await client.post("/api/crm/export/projects?format=csv")
        assert_response_ok(response)

        assert "text/csv" in response.headers.get("content-type", "")

    @pytest.mark.asyncio
    async def test_export_all_json(self, client: AsyncClient, sample_crm_contact, sample_project):
        """POST /api/crm/export/all?format=json - should export all CRM data."""
        await _create_crm_contact(client, sample_crm_contact)
        await _create_project(client, sample_project)

        response = await client.post("/api/crm/export/all?format=json")
        assert_response_ok(response)


# ============================================================
# Import
# ============================================================


class TestCRMImport:
    """Tests for CRM import endpoints."""

    @pytest.mark.asyncio
    async def test_import_contacts_csv(self, client: AsyncClient):
        """POST /api/crm/import/contacts - should import from CSV."""
        csv_content = (
            "Prenom,Nom,Entreprise,Email,Telephone,Source,Stage\n"
            "Alice,Legrand,StartupCo,alice@startup.co,+33600000001,website,contact\n"
            "Bob,Petit,BigCorp,bob@bigcorp.com,+33600000002,linkedin,discovery\n"
        )
        files = {"file": ("contacts.csv", csv_content.encode(), "text/csv")}

        response = await client.post(
            "/api/crm/import/contacts?update_existing=true",
            files=files,
        )
        assert_response_ok(response)
        data = response.json()

        assert data["success"] is True
        assert data["total_rows"] >= 2

    @pytest.mark.asyncio
    async def test_import_contacts_json(self, client: AsyncClient):
        """POST /api/crm/import/contacts - should import from JSON."""
        json_content = json.dumps([
            {
                "first_name": "Claire",
                "last_name": "Moreau",
                "company": "TechFR",
                "email": "claire@techfr.com",
            },
        ])
        files = {"file": ("contacts.json", json_content.encode(), "application/json")}

        response = await client.post(
            "/api/crm/import/contacts?update_existing=true",
            files=files,
        )
        assert_response_ok(response)
        data = response.json()

        assert data["success"] is True

    @pytest.mark.asyncio
    async def test_import_contacts_preview(self, client: AsyncClient):
        """POST /api/crm/import/contacts/preview - should return preview without importing."""
        csv_content = (
            "Prenom,Nom,Email\n"
            "Test,User,test@example.com\n"
        )
        files = {"file": ("preview.csv", csv_content.encode(), "text/csv")}

        response = await client.post(
            "/api/crm/import/contacts/preview",
            files=files,
        )
        assert_response_ok(response)
        data = response.json()

        assert "total_rows" in data
        assert "detected_columns" in data
        assert "can_import" in data


# ============================================================
# Sync Config (Google Sheets)
# ============================================================


class TestCRMSyncConfig:
    """Tests for CRM sync configuration."""

    @pytest.mark.asyncio
    async def test_get_sync_config_empty(self, client: AsyncClient):
        """GET /api/crm/sync/config - should return unconfigured state."""
        response = await client.get("/api/crm/sync/config")
        assert_response_ok(response)
        data = response.json()

        assert data["configured"] is False
        assert data["has_token"] is False
        assert data["spreadsheet_id"] is None
        assert data["last_sync"] is None

    @pytest.mark.asyncio
    async def test_set_sync_config(self, client: AsyncClient):
        """POST /api/crm/sync/config - should store spreadsheet ID."""
        response = await client.post(
            "/api/crm/sync/config",
            json={"spreadsheet_id": "1gXhiy43tvaDW0Y9FEGPmfB7BBCbUCOl_Xb6nkWtnnUk"},
        )
        assert_response_ok(response)
        data = response.json()

        assert data["spreadsheet_id"] is not None

    @pytest.mark.asyncio
    async def test_set_sync_config_empty_id(self, client: AsyncClient):
        """POST /api/crm/sync/config - should reject empty spreadsheet ID."""
        response = await client.post(
            "/api/crm/sync/config",
            json={"spreadsheet_id": "   "},
        )
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_get_sync_config_after_set(self, client: AsyncClient):
        """GET /api/crm/sync/config - should reflect configured spreadsheet."""
        await client.post(
            "/api/crm/sync/config",
            json={"spreadsheet_id": "test-spreadsheet-123"},
        )

        response = await client.get("/api/crm/sync/config")
        assert_response_ok(response)
        data = response.json()

        assert data["spreadsheet_id"] == "test-spreadsheet-123"


# ============================================================
# Sync Import (Direct JSON - bypass OAuth)
# ============================================================


class TestCRMSyncImport:
    """Tests for direct CRM data import (bypass Google Sheets OAuth)."""

    @pytest.mark.asyncio
    async def test_sync_import_clients(self, client: AsyncClient):
        """POST /api/crm/sync/import - should import client data."""
        response = await client.post(
            "/api/crm/sync/import",
            json={
                "clients": [
                    {
                        "ID": "client-001",
                        "Nom": "Alice Dupont",
                        "Entreprise": "StartupCo",
                        "Email": "alice@startup.co",
                        "Tel": "+33600000001",
                        "Source": "website",
                        "Stage": "contact",
                        "Score": "75",
                        "Tags": "vip,client",
                    },
                ],
            },
        )
        assert_response_ok(response)
        data = response.json()

        assert data["success"] is True
        assert data["stats"]["contacts_created"] == 1

    @pytest.mark.asyncio
    async def test_sync_import_projects(self, client: AsyncClient):
        """POST /api/crm/sync/import - should import project data."""
        response = await client.post(
            "/api/crm/sync/import",
            json={
                "projects": [
                    {
                        "ID": "project-001",
                        "Name": "Projet Test",
                        "Description": "Description test",
                        "ClientID": "",
                        "Status": "active",
                        "Budget": "5000",
                    },
                ],
            },
        )
        assert_response_ok(response)
        data = response.json()

        assert data["success"] is True
        assert data["stats"]["projects_created"] == 1

    @pytest.mark.asyncio
    async def test_sync_import_tasks(self, client: AsyncClient):
        """POST /api/crm/sync/import - should import task data."""
        response = await client.post(
            "/api/crm/sync/import",
            json={
                "tasks": [
                    {
                        "ID": "task-001",
                        "Title": "Envoyer devis",
                        "Description": "Devis pour formation IA",
                        "Priority": "high",
                        "Status": "todo",
                        "DueDate": "2026-03-01",
                    },
                ],
            },
        )
        assert_response_ok(response)
        data = response.json()

        assert data["success"] is True
        assert data["stats"]["tasks_created"] == 1

    @pytest.mark.asyncio
    async def test_sync_import_update_existing(self, client: AsyncClient):
        """POST /api/crm/sync/import - should update existing records on re-import."""
        # First import
        await client.post(
            "/api/crm/sync/import",
            json={
                "clients": [
                    {
                        "ID": "client-update-001",
                        "Nom": "Original Name",
                        "Email": "original@example.com",
                        "Stage": "contact",
                    },
                ],
            },
        )

        # Second import with updated data
        response = await client.post(
            "/api/crm/sync/import",
            json={
                "clients": [
                    {
                        "ID": "client-update-001",
                        "Nom": "Updated Name",
                        "Email": "updated@example.com",
                        "Stage": "discovery",
                    },
                ],
            },
        )
        assert_response_ok(response)
        data = response.json()

        assert data["stats"]["contacts_updated"] == 1
        assert data["stats"]["contacts_created"] == 0

    @pytest.mark.asyncio
    async def test_sync_import_empty_data(self, client: AsyncClient):
        """POST /api/crm/sync/import - should handle empty import gracefully."""
        response = await client.post(
            "/api/crm/sync/import",
            json={},
        )
        assert_response_ok(response)
        data = response.json()

        assert data["success"] is True
        assert data["stats"]["total_synced"] == 0

    @pytest.mark.asyncio
    async def test_sync_import_updates_last_sync(self, client: AsyncClient):
        """POST /api/crm/sync/import - should update last sync timestamp."""
        await client.post(
            "/api/crm/sync/import",
            json={"clients": [{"ID": "ts-test", "Nom": "Timestamp Test"}]},
        )

        config_resp = await client.get("/api/crm/sync/config")
        config = config_resp.json()

        assert config["last_sync"] is not None


# ============================================================
# Sync via Google Sheets (mocked)
# ============================================================


class TestCRMSyncGoogleSheets:
    """Tests for CRM sync via Google Sheets API (mocked)."""

    @pytest.mark.asyncio
    async def test_sync_no_config(self, client: AsyncClient):
        """POST /api/crm/sync - should fail without spreadsheet configured."""
        response = await client.post("/api/crm/sync")
        assert response.status_code == 400
        data = response.json()
        # Custom exception handler wraps detail into {"code": ..., "message": ...}
        error_text = data.get("detail") or data.get("message", "")
        assert "Spreadsheet ID" in error_text

    @pytest.mark.asyncio
    async def test_sync_no_auth(self, client: AsyncClient):
        """POST /api/crm/sync - should fail without OAuth token or API key."""
        # Set spreadsheet config first
        await client.post(
            "/api/crm/sync/config",
            json={"spreadsheet_id": "test-sheet-id"},
        )

        response = await client.post("/api/crm/sync")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_connect_sheets_no_credentials(self, client: AsyncClient):
        """POST /api/crm/sync/connect - should fail without Google credentials."""
        with patch("app.services.mcp_service.get_mcp_service") as mock_mcp:
            mock_instance = MagicMock()
            mock_instance.list_servers.return_value = []
            mock_mcp.return_value = mock_instance

            response = await client.post("/api/crm/sync/connect")
            assert response.status_code == 400
            data = response.json()
            # Custom exception handler wraps detail into {"code": ..., "message": ...}
            error_text = data.get("detail", "") or data.get("message", "")
            assert "credentials" in error_text.lower()
