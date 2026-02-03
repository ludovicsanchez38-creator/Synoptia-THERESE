"""
THERESE v2 - Tasks Router Tests

Tests pour le CRUD des taches locales (Phase 3).
"""

import pytest
from httpx import AsyncClient


class TestTasksList:
    """Tests pour le listing des taches."""

    @pytest.mark.asyncio
    async def test_list_tasks_empty(self, client: AsyncClient):
        """GET /api/tasks/ retourne une liste vide quand aucune tache n'existe."""
        response = await client.get("/api/tasks/")

        assert response.status_code == 200
        tasks = response.json()

        assert isinstance(tasks, list)
        assert len(tasks) == 0

    @pytest.mark.asyncio
    async def test_list_tasks_filter_status(self, client: AsyncClient):
        """GET /api/tasks/?status=todo filtre par statut."""
        # Creer deux taches avec des statuts differents
        await client.post("/api/tasks/", json={
            "title": "Tache todo",
            "status": "todo",
        })
        await client.post("/api/tasks/", json={
            "title": "Tache done",
            "status": "done",
        })

        # Filtrer par status=todo
        response = await client.get("/api/tasks/?status=todo")

        assert response.status_code == 200
        tasks = response.json()
        assert len(tasks) == 1
        assert tasks[0]["title"] == "Tache todo"
        assert tasks[0]["status"] == "todo"

    @pytest.mark.asyncio
    async def test_list_tasks_filter_priority(self, client: AsyncClient):
        """GET /api/tasks/?priority=high filtre par priorite."""
        # Creer deux taches avec des priorites differentes
        await client.post("/api/tasks/", json={
            "title": "Tache haute priorite",
            "priority": "high",
        })
        await client.post("/api/tasks/", json={
            "title": "Tache basse priorite",
            "priority": "low",
        })

        # Filtrer par priority=high
        response = await client.get("/api/tasks/?priority=high")

        assert response.status_code == 200
        tasks = response.json()
        assert len(tasks) == 1
        assert tasks[0]["title"] == "Tache haute priorite"
        assert tasks[0]["priority"] == "high"


class TestTasksCRUD:
    """Tests pour le CRUD complet des taches."""

    @pytest.mark.asyncio
    async def test_create_task(self, client: AsyncClient):
        """POST /api/tasks/ cree une tache avec titre, priorite et date."""
        response = await client.post("/api/tasks/", json={
            "title": "Appeler le client",
            "description": "Discussion contrat annuel",
            "priority": "high",
            "due_date": "2026-02-15T10:00:00",
        })

        assert response.status_code == 200
        task = response.json()

        assert task["title"] == "Appeler le client"
        assert task["description"] == "Discussion contrat annuel"
        assert task["priority"] == "high"
        assert task["status"] == "todo"  # Valeur par defaut
        assert task["due_date"] is not None
        assert "id" in task
        assert "created_at" in task
        assert "updated_at" in task

    @pytest.mark.asyncio
    async def test_create_task_with_tags(self, client: AsyncClient):
        """POST /api/tasks/ cree une tache avec un tableau de tags."""
        response = await client.post("/api/tasks/", json={
            "title": "Preparer la presentation",
            "tags": ["client", "urgent", "Q1"],
        })

        assert response.status_code == 200
        task = response.json()

        assert task["title"] == "Preparer la presentation"
        assert task["tags"] == ["client", "urgent", "Q1"]

    @pytest.mark.asyncio
    async def test_get_task(self, client: AsyncClient):
        """GET /api/tasks/{id} recupere une tache specifique."""
        # Creer une tache
        create_response = await client.post("/api/tasks/", json={
            "title": "Tache a recuperer",
        })
        task_id = create_response.json()["id"]

        # La recuperer
        response = await client.get(f"/api/tasks/{task_id}")

        assert response.status_code == 200
        task = response.json()
        assert task["id"] == task_id
        assert task["title"] == "Tache a recuperer"

    @pytest.mark.asyncio
    async def test_get_task_not_found(self, client: AsyncClient):
        """GET /api/tasks/{id} retourne 404 si la tache n'existe pas."""
        response = await client.get("/api/tasks/id-inexistant-12345")

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_task(self, client: AsyncClient):
        """PUT /api/tasks/{id} met a jour une tache."""
        # Creer une tache
        create_response = await client.post("/api/tasks/", json={
            "title": "Tache originale",
            "priority": "low",
        })
        task_id = create_response.json()["id"]

        # La mettre a jour
        response = await client.put(f"/api/tasks/{task_id}", json={
            "title": "Tache modifiee",
            "priority": "urgent",
        })

        assert response.status_code == 200
        task = response.json()
        assert task["title"] == "Tache modifiee"
        assert task["priority"] == "urgent"

    @pytest.mark.asyncio
    async def test_update_task_status_sets_completed_at(self, client: AsyncClient):
        """PUT /api/tasks/{id} avec status=done auto-definit completed_at."""
        # Creer une tache
        create_response = await client.post("/api/tasks/", json={
            "title": "Tache a completer",
        })
        task_id = create_response.json()["id"]

        # Verifier que completed_at est None au depart
        task = create_response.json()
        assert task["completed_at"] is None

        # Passer le status a "done"
        response = await client.put(f"/api/tasks/{task_id}", json={
            "status": "done",
        })

        assert response.status_code == 200
        task = response.json()
        assert task["status"] == "done"
        assert task["completed_at"] is not None

        # Repasser a "todo" - completed_at doit redevenir None
        response = await client.put(f"/api/tasks/{task_id}", json={
            "status": "todo",
        })

        assert response.status_code == 200
        task = response.json()
        assert task["status"] == "todo"
        assert task["completed_at"] is None

    @pytest.mark.asyncio
    async def test_delete_task(self, client: AsyncClient):
        """DELETE /api/tasks/{id} supprime une tache."""
        # Creer une tache
        create_response = await client.post("/api/tasks/", json={
            "title": "Tache a supprimer",
        })
        task_id = create_response.json()["id"]

        # La supprimer
        response = await client.delete(f"/api/tasks/{task_id}")

        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True

        # Verifier qu'elle n'existe plus
        get_response = await client.get(f"/api/tasks/{task_id}")
        assert get_response.status_code == 404


class TestTasksActions:
    """Tests pour les actions sur les taches (complete/uncomplete)."""

    @pytest.mark.asyncio
    async def test_complete_task(self, client: AsyncClient):
        """PATCH /api/tasks/{id}/complete marque une tache comme terminee."""
        # Creer une tache
        create_response = await client.post("/api/tasks/", json={
            "title": "Tache a completer via PATCH",
        })
        task_id = create_response.json()["id"]

        # La completer
        response = await client.patch(f"/api/tasks/{task_id}/complete")

        assert response.status_code == 200
        task = response.json()
        assert task["status"] == "done"
        assert task["completed_at"] is not None

    @pytest.mark.asyncio
    async def test_uncomplete_task(self, client: AsyncClient):
        """PATCH /api/tasks/{id}/uncomplete remet une tache en todo."""
        # Creer et completer une tache
        create_response = await client.post("/api/tasks/", json={
            "title": "Tache a reouvrir",
        })
        task_id = create_response.json()["id"]
        await client.patch(f"/api/tasks/{task_id}/complete")

        # La reouvrir
        response = await client.patch(f"/api/tasks/{task_id}/uncomplete")

        assert response.status_code == 200
        task = response.json()
        assert task["status"] == "todo"
        assert task["completed_at"] is None
