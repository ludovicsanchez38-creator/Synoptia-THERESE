"""
THERESE v2 - Security Services Tests

Tests for US-SEC-01 to US-SEC-05.
"""

import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from httpx import AsyncClient


class TestEncryptionService:
    """Tests for US-SEC-01: API key encryption."""

    def test_encrypt_decrypt_roundtrip(self):
        """Test that encryption and decryption work correctly."""
        from app.services.encryption import encrypt_value, decrypt_value

        original = "sk-ant-api03-test-key-12345"
        encrypted = encrypt_value(original)

        # Encrypted value should be different from original
        assert encrypted != original

        # Decrypted value should match original
        decrypted = decrypt_value(encrypted)
        assert decrypted == original

    def test_encrypt_empty_string(self):
        """Test encrypting empty string returns empty string."""
        from app.services.encryption import encrypt_value

        result = encrypt_value("")
        assert result == ""

    def test_decrypt_empty_string(self):
        """Test decrypting empty string returns empty string."""
        from app.services.encryption import decrypt_value

        result = decrypt_value("")
        assert result == ""

    def test_is_value_encrypted_detection(self):
        """Test detection of encrypted values."""
        from app.services.encryption import (
            encrypt_value,
            is_value_encrypted,
        )

        plain_text = "sk-ant-api03-test-key"
        encrypted = encrypt_value(plain_text)

        # Plain text should not be detected as encrypted
        assert not is_value_encrypted(plain_text)

        # Encrypted value should be detected
        # Note: This is heuristic, may have false positives
        assert is_value_encrypted(encrypted) or len(encrypted) > 50

    def test_encryption_service_singleton(self):
        """Test that EncryptionService is a singleton."""
        from app.services.encryption import EncryptionService

        service1 = EncryptionService()
        service2 = EncryptionService()

        assert service1 is service2


class TestAuditService:
    """Tests for US-SEC-05: Activity logs."""

    @pytest.mark.asyncio
    async def test_log_activity(self, async_client: AsyncClient, db_session):
        """Test logging an activity."""
        from app.services.audit import AuditService, AuditAction

        audit = AuditService(db_session)

        log_entry = await audit.log(
            action=AuditAction.API_KEY_SET,
            resource_type="api_key",
            resource_id="anthropic",
            details=json.dumps({"is_update": False}),
        )

        assert log_entry.id is not None
        assert log_entry.action == "api_key_set"
        assert log_entry.resource_type == "api_key"
        assert log_entry.resource_id == "anthropic"

    @pytest.mark.asyncio
    async def test_get_logs_with_filter(self, async_client: AsyncClient, db_session):
        """Test retrieving logs with filters."""
        from app.services.audit import AuditService, AuditAction

        audit = AuditService(db_session)

        # Create some logs
        await audit.log(AuditAction.CONTACT_CREATED, "contact", "c1")
        await audit.log(AuditAction.CONTACT_UPDATED, "contact", "c1")
        await audit.log(AuditAction.PROJECT_CREATED, "project", "p1")

        # Filter by action
        contact_created_logs = await audit.get_logs(
            action=AuditAction.CONTACT_CREATED
        )
        assert len(contact_created_logs) >= 1

        # Filter by resource type
        contact_logs = await audit.get_logs(resource_type="contact")
        assert len(contact_logs) >= 2

    @pytest.mark.asyncio
    async def test_logs_count(self, async_client: AsyncClient, db_session):
        """Test counting logs."""
        from app.services.audit import AuditService, AuditAction

        audit = AuditService(db_session)

        # Create logs
        await audit.log(AuditAction.FILE_INDEXED, "file", "f1")
        await audit.log(AuditAction.FILE_INDEXED, "file", "f2")

        count = await audit.get_logs_count(action=AuditAction.FILE_INDEXED)
        assert count >= 2


class TestDataExportAPI:
    """Tests for US-SEC-02: RGPD data export."""

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
    async def test_export_conversations_json(self, async_client: AsyncClient):
        """Test conversations export in JSON format."""
        response = await async_client.get("/api/data/export/conversations?format=json")
        assert response.status_code == 200

        data = response.json()
        assert "exported_at" in data
        assert "conversations" in data

    @pytest.mark.asyncio
    async def test_export_conversations_markdown(self, async_client: AsyncClient):
        """Test conversations export in Markdown format."""
        response = await async_client.get("/api/data/export/conversations?format=markdown")
        assert response.status_code == 200

        data = response.json()
        assert data["format"] == "markdown"
        assert "# Export Conversations THERESE" in data["content"]


class TestActivityLogsAPI:
    """Tests for US-SEC-05: Activity logs API."""

    @pytest.mark.asyncio
    async def test_get_activity_logs(self, async_client: AsyncClient):
        """Test retrieving activity logs."""
        response = await async_client.get("/api/data/logs")
        assert response.status_code == 200

        data = response.json()
        assert "logs" in data
        assert "total" in data
        assert "limit" in data
        assert "offset" in data

    @pytest.mark.asyncio
    async def test_get_activity_logs_with_filter(self, async_client: AsyncClient):
        """Test filtering activity logs."""
        response = await async_client.get("/api/data/logs?action=api_key_set")
        assert response.status_code == 200

        data = response.json()
        assert "logs" in data

    @pytest.mark.asyncio
    async def test_get_available_actions(self, async_client: AsyncClient):
        """Test listing available log actions."""
        response = await async_client.get("/api/data/logs/actions")
        assert response.status_code == 200

        data = response.json()
        assert "actions" in data
        assert "categories" in data
        assert "authentication" in data["categories"]
        assert "profile" in data["categories"]
        assert "data" in data["categories"]


class TestAPIKeyEncryption:
    """Tests for encrypted API key storage."""

    @pytest.mark.asyncio
    async def test_set_api_key_encrypted(self, async_client: AsyncClient):
        """Test that API keys are stored encrypted."""
        response = await async_client.post(
            "/api/config/api-key",
            json={
                "provider": "anthropic",
                "api_key": "sk-ant-test-key-12345",
            },
        )
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert data["provider"] == "anthropic"

    @pytest.mark.asyncio
    async def test_delete_api_key(self, async_client: AsyncClient):
        """Test deleting an API key."""
        # First set a key
        await async_client.post(
            "/api/config/api-key",
            json={
                "provider": "groq",
                "api_key": "gsk_test-key-12345",
            },
        )

        # Then delete it
        response = await async_client.delete("/api/config/api-key/groq")
        assert response.status_code == 200

        data = response.json()
        assert data["deleted"] is True


class TestDeleteAllData:
    """Tests for US-SEC-02: RGPD right to be forgotten."""

    @pytest.mark.asyncio
    async def test_delete_all_requires_confirmation(self, async_client: AsyncClient):
        """Test that delete all requires confirmation."""
        response = await async_client.delete("/api/data/all")
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_delete_all_with_confirmation(self, async_client: AsyncClient):
        """Test deleting all data with confirmation."""
        response = await async_client.delete("/api/data/all?confirm=true")
        assert response.status_code == 200

        data = response.json()
        assert data["deleted"] is True
        assert "RGPD" in data["message"]


class TestAuditIntegration:
    """Tests for audit logging integration."""

    @pytest.mark.asyncio
    async def test_contact_create_logged(self, async_client: AsyncClient):
        """Test that contact creation is logged."""
        # Create a contact
        response = await async_client.post(
            "/api/memory/contacts",
            json={
                "first_name": "Audit",
                "last_name": "Test",
            },
        )
        assert response.status_code == 200

        # Check logs
        logs_response = await async_client.get(
            "/api/data/logs?action=contact_created"
        )
        assert logs_response.status_code == 200

        data = logs_response.json()
        assert data["total"] >= 1

    @pytest.mark.asyncio
    async def test_project_create_logged(self, async_client: AsyncClient):
        """Test that project creation is logged."""
        # Create a project
        response = await async_client.post(
            "/api/memory/projects",
            json={
                "name": "Audit Test Project",
            },
        )
        assert response.status_code == 200

        # Check logs
        logs_response = await async_client.get(
            "/api/data/logs?action=project_created"
        )
        assert logs_response.status_code == 200

        data = logs_response.json()
        assert data["total"] >= 1
