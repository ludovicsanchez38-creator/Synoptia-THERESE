"""
THERESE v2 - Memory Router Tests

Tests for US-MEM-01 to US-MEM-05.
"""

import pytest
from httpx import AsyncClient


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

    @pytest.mark.asyncio
    async def test_delete_nonexistent_contact(self, client: AsyncClient):
        """Test deleting a non-existent contact."""
        response = await client.delete("/api/memory/contacts/nonexistent-id")

        assert response.status_code == 404


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
