"""
THERESE v2 - Memory Router Tests

Tests for US-MEM-01 to US-MEM-05.
"""

from unittest.mock import AsyncMock

import pytest
from app.models.entities import (
    Calendar,
    CalendarEvent,
    Contact,
    Conversation,
    Document,
    FileMetadata,
    Project,
)
from app.models.entities_sync import ProjectSyncRoot
from httpx import AsyncClient


async def _seed_project_references(db_session, project_id: str, contact_id: str | None = None):
    """Pose les références durables qui ne doivent pas survivre avec un id mort."""
    project = Project(id=project_id, name="Dossier durable", contact_id=contact_id)
    conversation = Conversation(
        id=f"conv-{project_id}",
        title="Conversation du dossier",
        project_id=project_id,
        memory_scope="project",
    )
    file = FileMetadata(
        id=f"file-{project_id}",
        path=f"/tmp/{project_id}.pdf",
        name=f"{project_id}.pdf",
        extension=".pdf",
        size=42,
        scope="project",
        scope_id=project_id,
    )
    document = Document(
        id=f"doc-{project_id}", title="Document du dossier", project_id=project_id
    )
    calendar = Calendar(id=f"cal-{project_id}", summary="Agenda local", provider="local")
    event = CalendarEvent(
        id=f"event-{project_id}",
        calendar_id=calendar.id,
        project_id=project_id,
        summary="Rendez-vous du dossier",
    )
    root = ProjectSyncRoot(
        id=f"root-{project_id}",
        project_id=project_id,
        racine=f"/tmp/racine-{project_id}",
        volume_id=1,
    )
    db_session.add_all([project, conversation, file, document, calendar, event, root])
    await db_session.commit()
    return conversation, file, document, event, root


class TestContactsCRUD:
    """Tests for US-MEM-01 and US-MEM-02: Contact CRUD operations."""

    @pytest.mark.asyncio
    async def test_create_contact(self, client: AsyncClient, sample_contact_data):
        """US-MEM-01: Create contact with professional info."""
        response = await client.post("/api/memory/contacts", json=sample_contact_data)

        assert response.status_code == 200
        contact = response.json()

        assert contact["first_name"] == "Jean"
        assert contact["last_name"] == "Dupont"
        assert contact["company"] == "Synoptia"
        assert contact["email"] == "jean@synoptia.fr"
        assert "id" in contact

    @pytest.mark.asyncio
    async def test_create_contact_minimal(self, client: AsyncClient):
        """Test creating contact with minimal info."""
        response = await client.post("/api/memory/contacts", json={
            "first_name": "Marie",
        })

        assert response.status_code == 200
        contact = response.json()
        assert contact["first_name"] == "Marie"

    @pytest.mark.asyncio
    async def test_list_contacts(self, client: AsyncClient, sample_contact_data):
        """US-MEM-02: List all contacts."""
        # Create a contact first
        await client.post("/api/memory/contacts", json=sample_contact_data)

        response = await client.get("/api/memory/contacts")

        assert response.status_code == 200
        contacts = response.json()

        assert isinstance(contacts, list)
        assert len(contacts) >= 1

    @pytest.mark.asyncio
    async def test_list_contacts_empty(self, client: AsyncClient):
        """Test listing contacts when none exist."""
        response = await client.get("/api/memory/contacts")

        assert response.status_code == 200
        contacts = response.json()

        assert isinstance(contacts, list)

    @pytest.mark.asyncio
    async def test_get_contact_by_id(self, client: AsyncClient, sample_contact_data):
        """Test getting a specific contact."""
        # Create a contact
        create_response = await client.post("/api/memory/contacts", json=sample_contact_data)
        contact_id = create_response.json()["id"]

        # Get it back
        response = await client.get(f"/api/memory/contacts/{contact_id}")

        assert response.status_code == 200
        contact = response.json()
        assert contact["id"] == contact_id

    @pytest.mark.asyncio
    async def test_update_contact(self, client: AsyncClient, sample_contact_data):
        """Test updating a contact."""
        # Create a contact
        create_response = await client.post("/api/memory/contacts", json=sample_contact_data)
        contact_id = create_response.json()["id"]

        # Update it (router uses PATCH, not PUT)
        response = await client.patch(f"/api/memory/contacts/{contact_id}", json={
            "company": "Synoptia SARL",
        })

        assert response.status_code == 200
        contact = response.json()
        assert contact["company"] == "Synoptia SARL"


class TestMemorySearch:
    """Tests for US-MEM-03: Search by keywords."""

    @pytest.mark.asyncio
    async def test_search_contacts(self, client: AsyncClient, sample_contact_data):
        """US-MEM-03: Search contacts by keywords."""
        # Create a contact
        await client.post("/api/memory/contacts", json=sample_contact_data)

        # Search for it
        response = await client.post("/api/memory/search", json={
            "query": "Jean Synoptia",
            "limit": 10,
        })

        assert response.status_code == 200
        results = response.json()

        assert "results" in results
        assert "total" in results

    @pytest.mark.asyncio
    async def test_search_empty_query(self, client: AsyncClient):
        """Test search with empty query."""
        response = await client.post("/api/memory/search", json={
            "query": "",
            "limit": 10,
        })

        # Empty query should still work
        assert response.status_code in [200, 422]


class TestProjectsCRUD:
    """Tests for US-MEM-04: Project CRUD operations."""

    @pytest.mark.asyncio
    async def test_create_project(self, client: AsyncClient, sample_project_data):
        """US-MEM-04: Create project linked to contact."""
        response = await client.post("/api/memory/projects", json=sample_project_data)

        assert response.status_code == 200
        project = response.json()

        assert project["name"] == "Projet Test"
        assert project["status"] == "active"
        assert "id" in project

    @pytest.mark.asyncio
    async def test_create_project_with_contact(
        self, client: AsyncClient, sample_contact_data, sample_project_data
    ):
        """Test creating project linked to a contact."""
        # Create contact first
        contact_response = await client.post("/api/memory/contacts", json=sample_contact_data)
        contact_id = contact_response.json()["id"]

        # Create project with contact link
        project_data = {**sample_project_data, "contact_id": contact_id}
        response = await client.post("/api/memory/projects", json=project_data)

        assert response.status_code == 200
        project = response.json()
        assert project.get("contact_id") == contact_id

    @pytest.mark.asyncio
    async def test_list_projects(self, client: AsyncClient, sample_project_data):
        """Test listing all projects."""
        # Create a project
        await client.post("/api/memory/projects", json=sample_project_data)

        response = await client.get("/api/memory/projects")

        assert response.status_code == 200
        projects = response.json()

        assert isinstance(projects, list)


class TestMemoryDeleteCascade:
    """Tests for US-MEM-05: Delete with cascade."""

    @pytest.mark.asyncio
    async def test_delete_contact(self, client: AsyncClient, sample_contact_data):
        """Test deleting a contact."""
        # Create a contact
        create_response = await client.post("/api/memory/contacts", json=sample_contact_data)
        contact_id = create_response.json()["id"]

        # Delete it
        response = await client.delete(f"/api/memory/contacts/{contact_id}")

        assert response.status_code == 200

        # Verify it's gone
        get_response = await client.get(f"/api/memory/contacts/{contact_id}")
        assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_contact_with_cascade(
        self, client: AsyncClient, sample_contact_data, sample_project_data
    ):
        """US-MEM-05: Delete contact cascades to projects."""
        # Create contact
        contact_response = await client.post("/api/memory/contacts", json=sample_contact_data)
        contact_id = contact_response.json()["id"]

        # Create project linked to contact
        project_data = {**sample_project_data, "contact_id": contact_id}
        project_response = await client.post("/api/memory/projects", json=project_data)
        project_id = project_response.json()["id"]

        # Delete contact with cascade
        response = await client.delete(f"/api/memory/contacts/{contact_id}?cascade=true")

        assert response.status_code == 200
        result = response.json()
        assert result.get("deleted") is True

        # Le projet lié doit avoir été supprimé en cascade (sinon le cascade ne
        # fait rien) : GET du projet renvoie 404.
        project_check = await client.get(f"/api/memory/projects/{project_id}")
        assert project_check.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_nonexistent_contact(self, client: AsyncClient):
        """Test deleting a non-existent contact."""
        response = await client.delete("/api/memory/contacts/nonexistent-id")

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_project_sans_cascade_ne_laisse_aucun_identifiant_mort(
        self, client: AsyncClient, db_session, monkeypatch
    ):
        """L'API par défaut doit nettoyer ce que l'interface ne sait pas demander."""
        project_id = "project-delete-direct"
        conversation, file, document, event, root = await _seed_project_references(
            db_session, project_id
        )
        conversation_id, file_id = conversation.id, file.id
        document_id, event_id, root_id = document.id, event.id, root.id
        delete_vectors = AsyncMock(return_value=1)
        monkeypatch.setattr(
            "app.routers.memory.get_qdrant_service",
            lambda: type("Qdrant", (), {"async_delete_by_entity": delete_vectors})(),
        )

        response = await client.delete(f"/api/memory/projects/{project_id}")

        assert response.status_code == 200, response.text
        db_session.expire_all()
        assert await db_session.get(Project, project_id) is None
        assert await db_session.get(FileMetadata, file_id) is None
        assert (await db_session.get(Conversation, conversation_id)).project_id is None
        assert (await db_session.get(Conversation, conversation_id)).memory_scope == "global"
        assert (await db_session.get(Document, document_id)).project_id is None
        assert (await db_session.get(CalendarEvent, event_id)).project_id is None
        assert (await db_session.get(ProjectSyncRoot, root_id)).detachee is True
        assert {call.args[0] for call in delete_vectors.await_args_list} >= {
            file_id,
            project_id,
        }

    @pytest.mark.asyncio
    async def test_delete_contact_cascade_reutilise_le_menage_du_projet(
        self, client: AsyncClient, db_session, monkeypatch
    ):
        """Le bouton Contacts ne doit pas court-circuiter le contrat dossier."""
        contact = Contact(id="contact-cascade-durable", first_name="Client")
        db_session.add(contact)
        await db_session.commit()
        project_id = "project-contact-cascade"
        conversation, file, document, event, root = await _seed_project_references(
            db_session, project_id, contact.id
        )
        conversation_id, file_id = conversation.id, file.id
        document_id, event_id, root_id = document.id, event.id, root.id
        delete_vectors = AsyncMock(return_value=1)
        monkeypatch.setattr(
            "app.routers.memory.get_qdrant_service",
            lambda: type("Qdrant", (), {"async_delete_by_entity": delete_vectors})(),
        )

        response = await client.delete(
            f"/api/memory/contacts/{contact.id}?cascade=true"
        )

        assert response.status_code == 200, response.text
        db_session.expire_all()
        assert await db_session.get(Project, project_id) is None
        assert await db_session.get(FileMetadata, file_id) is None
        assert (await db_session.get(Conversation, conversation_id)).project_id is None
        assert (await db_session.get(Document, document_id)).project_id is None
        assert (await db_session.get(CalendarEvent, event_id)).project_id is None
        assert (await db_session.get(ProjectSyncRoot, root_id)).detachee is True


class TestMemoryScope:
    """Tests for memory scope functionality."""

    @pytest.mark.asyncio
    async def test_list_contacts_with_scope(self, client: AsyncClient, sample_contact_data):
        """Test listing contacts with scope filter."""
        # Create a global contact
        await client.post("/api/memory/contacts", json=sample_contact_data)

        # List with global scope
        response = await client.get("/api/memory/contacts?scope=global")

        assert response.status_code == 200
        contacts = response.json()
        assert isinstance(contacts, list)

    @pytest.mark.asyncio
    async def test_list_projects_with_scope(self, client: AsyncClient, sample_project_data):
        """Test listing projects with scope filter."""
        await client.post("/api/memory/projects", json=sample_project_data)

        response = await client.get("/api/memory/projects?scope=global")

        assert response.status_code == 200
        projects = response.json()
        assert isinstance(projects, list)
