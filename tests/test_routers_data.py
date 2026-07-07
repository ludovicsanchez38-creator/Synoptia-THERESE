"""
THERESE v2 - Data Router Tests

Tests pour les endpoints d'export, import, backup et logs (US-SEC-02, US-BAK-01 a US-BAK-05).
"""

import pytest
from httpx import AsyncClient

# ============================================================
# Helpers
# ============================================================


async def _create_contact(client: AsyncClient, first_name: str = "Jean") -> str:
    """Cree un contact de test et retourne son ID."""
    response = await client.post("/api/memory/contacts", json={
        "first_name": first_name,
        "last_name": "Dupont",
        "company": "Synoptia",
        "email": f"{first_name.lower()}@synoptia.fr",
    })
    assert response.status_code == 200
    return response.json()["id"]


async def _create_document_with_section_and_piste(client: AsyncClient) -> dict:
    """Cree un document de l'atelier documentaire avec une section redigee
    et une piste, pour verrouiller sa presence dans export/delete RGPD."""
    doc_response = await client.post(
        "/api/documents", json={"title": "Doc RGPD", "brief": "Brief du besoin"}
    )
    assert doc_response.status_code == 200, doc_response.text
    document = doc_response.json()

    section_response = await client.post(
        f"/api/documents/{document['id']}/sections",
        json={"title": "Section RGPD", "brief": "", "order": 0.0, "depth": 0},
    )
    assert section_response.status_code == 200, section_response.text
    section = section_response.json()

    await client.patch(
        f"/api/documents/sections/{section['id']}",
        json={"content": "Contenu redige a exporter/supprimer."},
    )

    piste_response = await client.post(
        f"/api/documents/{document['id']}/pistes",
        json={"texte": "Piste RGPD a retrouver dans l'export"},
    )
    assert piste_response.status_code == 200, piste_response.text
    piste = piste_response.json()

    return {"document": document, "section": section, "piste": piste}


# ============================================================
# Export Tests
# ============================================================


class TestDataExport:
    """Tests pour les endpoints d'export RGPD."""

    @pytest.mark.asyncio
    async def test_export_all_data_empty(self, client: AsyncClient):
        """GET /api/data/export retourne une structure avec des tableaux vides."""
        response = await client.get("/api/data/export")

        assert response.status_code == 200
        data = response.json()

        # Verifier la structure de base
        assert "exported_at" in data
        assert "contacts" in data
        assert "projects" in data
        assert "conversations" in data
        assert "files" in data
        assert "preferences" in data
        assert "board_decisions" in data
        assert "activity_logs" in data

        assert isinstance(data["contacts"], list)
        assert isinstance(data["projects"], list)
        assert isinstance(data["conversations"], list)

    @pytest.mark.asyncio
    async def test_export_all_data_with_contacts(self, client: AsyncClient):
        """GET /api/data/export contient les contacts crees."""
        # Creer des contacts
        await _create_contact(client, "Alice")
        await _create_contact(client, "Bob")

        response = await client.get("/api/data/export")

        assert response.status_code == 200
        data = response.json()

        assert len(data["contacts"]) >= 2
        first_names = [c["first_name"] for c in data["contacts"]]
        assert "Alice" in first_names
        assert "Bob" in first_names

    @pytest.mark.asyncio
    async def test_export_all_data_contains_documents_sections_pistes(self, client: AsyncClient):
        """GET /api/data/export (RGPD Art. 20) restitue l'atelier documentaire :
        un « supprimer toutes mes donnees » sans ces 3 tables laisserait un
        trou dans le droit a la portabilite."""
        created = await _create_document_with_section_and_piste(client)

        response = await client.get("/api/data/export")

        assert response.status_code == 200
        data = response.json()

        assert "documents" in data
        assert "document_sections" in data
        assert "document_pistes" in data
        assert isinstance(data["documents"], list)
        assert isinstance(data["document_sections"], list)
        assert isinstance(data["document_pistes"], list)

        doc_ids = [d["id"] for d in data["documents"]]
        assert created["document"]["id"] in doc_ids

        section_ids = [s["id"] for s in data["document_sections"]]
        assert created["section"]["id"] in section_ids
        exported_section = next(
            s for s in data["document_sections"] if s["id"] == created["section"]["id"]
        )
        assert exported_section["content"] == "Contenu redige a exporter/supprimer."
        assert exported_section["document_id"] == created["document"]["id"]

        piste_ids = [p["id"] for p in data["document_pistes"]]
        assert created["piste"]["id"] in piste_ids
        exported_piste = next(
            p for p in data["document_pistes"] if p["id"] == created["piste"]["id"]
        )
        assert exported_piste["texte"] == "Piste RGPD a retrouver dans l'export"

    @pytest.mark.asyncio
    async def test_export_conversations_json(self, client: AsyncClient):
        """GET /api/data/export/conversations retourne le format JSON."""
        response = await client.get("/api/data/export/conversations")

        assert response.status_code == 200
        data = response.json()

        assert "exported_at" in data
        assert "conversations" in data
        assert isinstance(data["conversations"], list)

    @pytest.mark.asyncio
    async def test_export_conversations_markdown(self, client: AsyncClient):
        """GET /api/data/export/conversations?format=markdown retourne du Markdown."""
        response = await client.get("/api/data/export/conversations?format=markdown")

        assert response.status_code == 200
        data = response.json()

        assert data["format"] == "markdown"
        assert "content" in data
        assert "# Export Conversations THERESE" in data["content"]


# ============================================================
# Delete All Data Tests
# ============================================================


class TestDataDeletion:
    """Tests pour la suppression de toutes les donnees (RGPD Art. 17)."""

    @pytest.mark.asyncio
    async def test_delete_all_data_requires_confirm(self, client: AsyncClient):
        """DELETE /api/data/all sans confirm=true retourne 400."""
        response = await client.delete("/api/data/all")

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_delete_all_data(self, client: AsyncClient):
        """DELETE /api/data/all?confirm=true supprime toutes les donnees."""
        # Creer des donnees d'abord
        await _create_contact(client, "ContactASupprimer")

        # Confirmer la suppression
        response = await client.delete("/api/data/all?confirm=true")

        assert response.status_code == 200
        result = response.json()
        assert result["deleted"] is True

        # Verifier que les contacts sont supprimes
        list_response = await client.get("/api/memory/contacts")
        assert list_response.status_code == 200
        assert len(list_response.json()) == 0

    @pytest.mark.asyncio
    async def test_delete_all_data_purges_documents_sections_pistes(self, client: AsyncClient):
        """DELETE /api/data/all?confirm=true (RGPD Art. 17) purge aussi
        l'atelier documentaire - sinon le droit a l'oubli laisse des
        documents en base apres un 'supprimer toutes mes donnees'."""
        created = await _create_document_with_section_and_piste(client)

        response = await client.delete("/api/data/all?confirm=true")

        assert response.status_code == 200
        assert response.json()["deleted"] is True

        list_response = await client.get("/api/documents")
        assert list_response.status_code == 200
        assert list_response.json() == []

        get_response = await client.get(f"/api/documents/{created['document']['id']}")
        assert get_response.status_code == 404


# ============================================================
# Activity Logs Tests
# ============================================================


class TestActivityLogs:
    """Tests pour les logs d'activite."""

    @pytest.mark.asyncio
    async def test_get_activity_logs(self, client: AsyncClient):
        """GET /api/data/logs retourne une structure paginee de logs."""
        response = await client.get("/api/data/logs")

        assert response.status_code == 200
        data = response.json()

        assert "logs" in data
        assert "total" in data
        assert "limit" in data
        assert "offset" in data
        assert isinstance(data["logs"], list)

    @pytest.mark.asyncio
    async def test_get_activity_logs_after_export(self, client: AsyncClient):
        """Un export genere un log d'activite."""
        # Lancer un export (cela cree un log)
        await client.get("/api/data/export")

        # Verifier que le log existe
        response = await client.get("/api/data/logs")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1


# ============================================================
# Backup Status Tests
# ============================================================


class TestBackupStatus:
    """Tests pour le statut des backups."""

    @pytest.mark.asyncio
    async def test_backup_status(self, client: AsyncClient):
        """GET /api/data/backup/status retourne le statut des sauvegardes."""
        response = await client.get("/api/data/backup/status")

        assert response.status_code == 200
        data = response.json()

        assert "has_backups" in data
        assert "last_backup" in data


# ============================================================
# Import Tests
# ============================================================


class TestDataImport:
    """Tests pour l'import de donnees."""

    @pytest.mark.asyncio
    async def test_import_conversations(self, client: AsyncClient):
        """POST /api/data/import/conversations importe des conversations JSON."""
        import_data = {
            "conversations": [
                {
                    "title": "Conversation importee",
                    "messages": [
                        {
                            "role": "user",
                            "content": "Bonjour THERESE",
                            "created_at": "2026-01-15T10:00:00",
                        },
                        {
                            "role": "assistant",
                            "content": "Bonjour ! Comment puis-je vous aider ?",
                            "created_at": "2026-01-15T10:00:05",
                        },
                    ],
                }
            ]
        }

        response = await client.post("/api/data/import/conversations", json=import_data)

        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        assert result["imported"]["conversations"] == 1
        assert result["imported"]["messages"] == 2

    @pytest.mark.asyncio
    async def test_import_conversations_invalid_format(self, client: AsyncClient):
        """POST /api/data/import/conversations echoue si le format est invalide."""
        response = await client.post("/api/data/import/conversations", json={
            "invalid_key": "pas de conversations",
        })

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_import_contacts(self, client: AsyncClient):
        """POST /api/data/import/contacts importe des contacts JSON."""
        import_data = {
            "contacts": [
                {
                    "first_name": "ImporteAlice",
                    "last_name": "Durand",
                    "company": "Import Co",
                    "email": "alice.import@test.fr",
                },
                {
                    "first_name": "ImporteBob",
                    "last_name": "Leroy",
                    "email": "bob.import@test.fr",
                },
            ]
        }

        response = await client.post("/api/data/import/contacts", json=import_data)

        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        assert result["imported"] == 2

    @pytest.mark.asyncio
    async def test_import_contacts_invalid_format(self, client: AsyncClient):
        """POST /api/data/import/contacts echoue si le format est invalide."""
        response = await client.post("/api/data/import/contacts", json={
            "invalid_key": "pas de contacts",
        })

        assert response.status_code == 400
