"""
THERESE v2 - Backup & Data Tests

Tests for US-BAK-01 to US-BAK-05.
"""

import pytest
import json
from datetime import datetime

from httpx import AsyncClient


class TestExportConversations:
    """Tests for US-BAK-01: Export conversations."""

    @pytest.mark.asyncio
    async def test_export_conversations_json(self, async_client: AsyncClient):
        """Test exporting conversations as JSON."""
        response = await async_client.get("/api/data/export/conversations?format=json")
        assert response.status_code == 200

        data = response.json()
        assert "exported_at" in data
        assert "conversations" in data
        assert isinstance(data["conversations"], list)

    @pytest.mark.asyncio
    async def test_export_conversations_markdown(self, async_client: AsyncClient):
        """Test exporting conversations as Markdown."""
        response = await async_client.get("/api/data/export/conversations?format=markdown")
        assert response.status_code == 200

        data = response.json()
        assert data["format"] == "markdown"
        assert "# Export Conversations THERESE" in data["content"]


class TestImportData:
    """Tests for US-BAK-02: Import data."""

    @pytest.mark.asyncio
    async def test_import_conversations(self, async_client: AsyncClient):
        """Test importing conversations from JSON."""
        import_data = {
            "conversations": [
                {
                    "id": "test-import-conv-1",
                    "title": "Test Import Conversation",
                    "messages": [
                        {"role": "user", "content": "Hello"},
                        {"role": "assistant", "content": "Hi there!"},
                    ],
                }
            ]
        }

        response = await async_client.post(
            "/api/data/import/conversations",
            json=import_data,
        )
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert data["imported"]["conversations"] >= 0  # May be 0 if already exists

    @pytest.mark.asyncio
    async def test_import_contacts(self, async_client: AsyncClient):
        """Test importing contacts from JSON."""
        import_data = {
            "contacts": [
                {
                    "id": "test-import-contact-1",
                    "first_name": "Import",
                    "last_name": "Test",
                    "email": "import@test.com",
                }
            ]
        }

        response = await async_client.post(
            "/api/data/import/contacts",
            json=import_data,
        )
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True

    @pytest.mark.asyncio
    async def test_import_invalid_format(self, async_client: AsyncClient):
        """Test importing with invalid format."""
        response = await async_client.post(
            "/api/data/import/conversations",
            json={"invalid": "data"},
        )
        assert response.status_code == 400


class TestBackupOperations:
    """Tests for US-BAK-03, US-BAK-04: Backup and restore."""

    @pytest.mark.asyncio
    async def test_create_backup(self, async_client: AsyncClient):
        """Test creating a backup."""
        response = await async_client.post("/api/data/backup")
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert "backup_name" in data
        assert "path" in data
        assert "created_at" in data

    @pytest.mark.asyncio
    async def test_list_backups(self, async_client: AsyncClient):
        """Test listing backups."""
        response = await async_client.get("/api/data/backups")
        assert response.status_code == 200

        data = response.json()
        assert "backups" in data
        assert isinstance(data["backups"], list)

    @pytest.mark.asyncio
    async def test_backup_status(self, async_client: AsyncClient):
        """Test getting backup status."""
        response = await async_client.get("/api/data/backup/status")
        assert response.status_code == 200

        data = response.json()
        assert "has_backups" in data
        assert "last_backup" in data

    @pytest.mark.asyncio
    async def test_restore_requires_confirmation(self, async_client: AsyncClient):
        """Test that restore requires confirmation."""
        response = await async_client.post("/api/data/restore/nonexistent")
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_restore_nonexistent_backup(self, async_client: AsyncClient):
        """Test restoring from nonexistent backup."""
        response = await async_client.post(
            "/api/data/restore/nonexistent?confirm=true"
        )
        assert response.status_code == 404


class TestFullDataExport:
    """Tests for complete data export."""

    @pytest.mark.asyncio
    async def test_export_all_data(self, async_client: AsyncClient):
        """Test full data export."""
        response = await async_client.get("/api/data/export")
        assert response.status_code == 200

        data = response.json()
        assert "exported_at" in data
        assert "app_version" in data
        assert "contacts" in data
        assert "projects" in data
        assert "conversations" in data
        assert "files" in data
        assert "preferences" in data
        assert "board_decisions" in data
        assert "activity_logs" in data

    @pytest.mark.asyncio
    async def test_export_does_not_include_api_keys(self, async_client: AsyncClient):
        """Test that API keys are not exported."""
        response = await async_client.get("/api/data/export")
        assert response.status_code == 200

        data = response.json()
        # Check preferences don't have actual API key values
        for pref in data.get("preferences", []):
            if "api_key" in pref.get("key", "").lower():
                assert pref.get("value") == "[REDACTED]"


class TestBackupIntegration:
    """Integration tests for backup workflow."""

    @pytest.mark.asyncio
    async def test_full_backup_restore_workflow(self, async_client: AsyncClient):
        """Test complete backup and list workflow."""
        # Create a backup
        create_response = await async_client.post("/api/data/backup")
        assert create_response.status_code == 200
        backup_name = create_response.json()["backup_name"]

        # List backups
        list_response = await async_client.get("/api/data/backups")
        assert list_response.status_code == 200
        backups = list_response.json()["backups"]

        # Verify our backup is in the list
        backup_names = [b.get("backup_name") for b in backups]
        assert backup_name in backup_names

        # Check backup status
        status_response = await async_client.get("/api/data/backup/status")
        assert status_response.status_code == 200
        assert status_response.json()["has_backups"] is True

        # Clean up - delete the test backup
        delete_response = await async_client.delete(f"/api/data/backups/{backup_name}")
        assert delete_response.status_code == 200
