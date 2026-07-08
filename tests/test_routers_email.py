"""
THERESE v2 - Email Router Tests

Tests for email endpoints (Gmail OAuth, IMAP/SMTP, messages, labels, smart features).
All external services (Gmail API, IMAP, SMTP, LLM) are mocked.
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient

from tests.conftest import assert_response_ok

# ============================================================
# Fixtures
# ============================================================


@pytest.fixture
def sample_imap_setup():
    """Sample IMAP/SMTP account setup data."""
    return {
        "email": "test@example.com",
        "password": "app-password-test",
        "imap_host": "imap.example.com",
        "imap_port": 993,
        "smtp_host": "smtp.example.com",
        "smtp_port": 587,
        "smtp_use_tls": True,
    }


@pytest.fixture
def sample_send_email():
    """Sample send email request."""
    return {
        "to": ["destinataire@example.com"],
        "subject": "Test email",
        "body": "Bonjour, ceci est un test.",
        "cc": None,
        "bcc": None,
        "html": False,
    }


@pytest.fixture
def sample_draft_email():
    """Sample draft email request."""
    return {
        "to": ["draft@example.com"],
        "subject": "Brouillon test",
        "body": "Contenu du brouillon",
        "html": False,
    }


# ============================================================
# OAuth & Auth Status
# ============================================================


class TestEmailAuthStatus:
    """Tests for email authentication status."""

    @pytest.mark.asyncio
    async def test_get_auth_status_not_connected(self, client: AsyncClient):
        """GET /api/email/auth/status - should return not connected when no accounts."""
        response = await client.get("/api/email/auth/status")
        assert_response_ok(response)
        data = response.json()

        assert data["connected"] is False
        assert data["accounts"] == []

    @pytest.mark.asyncio
    async def test_get_auth_status_with_account(self, client: AsyncClient, sample_imap_setup):
        """GET /api/email/auth/status - should return connected after IMAP setup."""
        # Setup an IMAP account first (mock the provider)
        with patch("app.routers.email.get_email_provider") as mock_provider:
            mock_instance = MagicMock()
            mock_instance.test_connection = AsyncMock(return_value={"success": True})
            mock_provider.return_value = mock_instance

            await client.post("/api/email/auth/imap-setup", json=sample_imap_setup)

        response = await client.get("/api/email/auth/status")
        assert_response_ok(response)
        data = response.json()

        assert data["connected"] is True
        assert len(data["accounts"]) == 1
        assert data["accounts"][0]["email"] == "test@example.com"
        assert data["accounts"][0]["provider"] == "imap"


# ============================================================
# IMAP/SMTP Account Management
# ============================================================


class TestImapAccountSetup:
    """Tests for IMAP/SMTP account setup."""

    @pytest.mark.asyncio
    async def test_setup_imap_account(self, client: AsyncClient, sample_imap_setup):
        """POST /api/email/auth/imap-setup - should create an IMAP account."""
        response = await client.post("/api/email/auth/imap-setup", json=sample_imap_setup)
        assert_response_ok(response)
        data = response.json()

        assert data["email"] == "test@example.com"
        assert data["provider"] == "imap"
        assert "id" in data
        assert "created_at" in data

    @pytest.mark.asyncio
    async def test_setup_imap_account_update_existing(self, client: AsyncClient, sample_imap_setup):
        """POST /api/email/auth/imap-setup - should update existing account."""
        # Create first
        response1 = await client.post("/api/email/auth/imap-setup", json=sample_imap_setup)
        assert_response_ok(response1)
        first_id = response1.json()["id"]

        # Update with same email
        updated_data = {**sample_imap_setup, "imap_host": "new-imap.example.com"}
        response2 = await client.post("/api/email/auth/imap-setup", json=updated_data)
        assert_response_ok(response2)
        data = response2.json()

        assert data["id"] == first_id
        assert data["email"] == "test@example.com"

    @pytest.mark.asyncio
    async def test_test_connection_success(self, client: AsyncClient, sample_imap_setup):
        """POST /api/email/auth/test-connection - mock successful connection."""
        with patch("app.routers.email.get_email_provider") as mock_provider:
            mock_instance = MagicMock()
            mock_instance.test_connection = AsyncMock(return_value={
                "success": True,
                "message": "Connexion IMAP/SMTP reussie",
            })
            mock_provider.return_value = mock_instance

            response = await client.post("/api/email/auth/test-connection", json=sample_imap_setup)
            assert_response_ok(response)
            data = response.json()

            assert data["success"] is True

    @pytest.mark.asyncio
    async def test_test_connection_failure(self, client: AsyncClient, sample_imap_setup):
        """POST /api/email/auth/test-connection - mock failed connection."""
        with patch("app.routers.email.get_email_provider") as mock_provider:
            mock_instance = MagicMock()
            mock_instance.test_connection = AsyncMock(
                side_effect=Exception("Connection refused")
            )
            mock_provider.return_value = mock_instance

            response = await client.post("/api/email/auth/test-connection", json=sample_imap_setup)
            assert_response_ok(response)
            data = response.json()

            assert data["success"] is False
            assert "Échec de connexion" in data["message"]


# ============================================================
# Email Providers
# ============================================================


class TestEmailProviders:
    """Tests for listing email providers."""

    @pytest.mark.asyncio
    async def test_list_email_providers(self, client: AsyncClient):
        """GET /api/email/providers - should return preconfigured providers."""
        with patch("app.routers.email.list_common_providers") as mock_providers:
            mock_providers.return_value = [
                {"name": "Gmail", "imap_host": "imap.gmail.com", "imap_port": 993},
                {"name": "Outlook", "imap_host": "outlook.office365.com", "imap_port": 993},
            ]

            response = await client.get("/api/email/providers")
            assert_response_ok(response)
            data = response.json()

            assert isinstance(data, list)
            assert len(data) == 2


# ============================================================
# Messages
# ============================================================


class TestEmailMessages:
    """Tests for message CRUD operations."""

    @pytest.mark.asyncio
    async def test_list_messages_no_account(self, client: AsyncClient):
        """GET /api/email/messages - should 404 with invalid account_id."""
        response = await client.get("/api/email/messages?account_id=nonexistent")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_list_messages_imap_empty(self, client: AsyncClient, sample_imap_setup):
        """GET /api/email/messages - should return empty list for new IMAP account."""
        # Create IMAP account
        create_resp = await client.post("/api/email/auth/imap-setup", json=sample_imap_setup)
        account_id = create_resp.json()["id"]

        # Mock IMAP provider
        with patch("app.routers.email.get_email_provider") as mock_provider:
            mock_instance = MagicMock()
            mock_instance.list_messages = AsyncMock(return_value=([], None))
            mock_provider.return_value = mock_instance

            response = await client.get(f"/api/email/messages?account_id={account_id}")
            assert_response_ok(response)
            data = response.json()

            assert data["messages"] == []
            assert data["resultSizeEstimate"] == 0

    @pytest.mark.asyncio
    async def test_list_messages_imap_with_data(self, client: AsyncClient, sample_imap_setup):
        """GET /api/email/messages - should return messages from IMAP."""
        create_resp = await client.post("/api/email/auth/imap-setup", json=sample_imap_setup)
        account_id = create_resp.json()["id"]

        # Mock message DTO
        mock_msg = MagicMock()
        mock_msg.id = "msg-001"
        mock_msg.thread_id = "thread-001"
        mock_msg.snippet = "Bonjour, voici un test"
        mock_msg.subject = "Test subject"
        mock_msg.from_name = "Jean Dupont"
        mock_msg.from_email = "jean@example.com"
        mock_msg.date = datetime(2026, 1, 15, 10, 30)
        mock_msg.labels = ["INBOX"]

        with patch("app.routers.email.get_email_provider") as mock_provider:
            mock_instance = MagicMock()
            mock_instance.list_messages = AsyncMock(return_value=([mock_msg], None))
            mock_provider.return_value = mock_instance

            response = await client.get(f"/api/email/messages?account_id={account_id}")
            assert_response_ok(response)
            data = response.json()

            assert len(data["messages"]) == 1
            assert data["messages"][0]["id"] == "msg-001"
            assert data["messages"][0]["subject"] == "Test subject"

    @pytest.mark.asyncio
    async def test_get_message_imap_route_provider_pas_gmail(self, client: AsyncClient, sample_imap_setup):
        """BUG-123 : GET /messages/{id} d'un compte IMAP doit passer par le
        provider IMAP, JAMAIS par Gmail. Forcer Gmail envoyait un token OAuth
        vide (`Authorization: Bearer `) -> 500 « Illegal header value b'Bearer ' »
        et l'UI retombait sur l'aperçu tronqué."""
        create_resp = await client.post("/api/email/auth/imap-setup", json=sample_imap_setup)
        account_id = create_resp.json()["id"]

        dto = MagicMock()
        dto.id = "3"
        dto.thread_id = "thread-3"
        dto.subject = "Re: test"
        dto.from_email = "jd@tictec.fr"
        dto.from_name = "Jérôme DELAUNAY"
        dto.to_emails = ["me@imap.fr"]
        dto.date = datetime(2026, 7, 8, 16, 26)
        dto.labels = ["INBOX"]
        dto.is_read = True
        dto.is_starred = False
        dto.body_plain = "Contenu COMPLET du message, pas juste l'aperçu."
        dto.body_html = "<p>Contenu COMPLET du message</p>"

        def _boom_gmail(*args, **kwargs):
            raise AssertionError("Gmail ne doit pas être appelé pour un compte IMAP (BUG-123)")

        with patch("app.routers.email.get_email_provider") as mock_provider, patch(
            "app.routers.email.get_gmail_service_for_account", _boom_gmail
        ):
            mock_instance = MagicMock()
            mock_instance.get_message = AsyncMock(return_value=dto)
            mock_provider.return_value = mock_instance

            response = await client.get(f"/api/email/messages/3?account_id={account_id}")

        assert_response_ok(response)
        data = response.json()
        assert data["id"] == "3"
        # Le contenu COMPLET est renvoyé, pas seulement un aperçu tronqué.
        assert "COMPLET" in data["body_plain"]
        assert data["body_html"] == "<p>Contenu COMPLET du message</p>"
        mock_instance.get_message.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_delete_message_not_found_account(self, client: AsyncClient):
        """DELETE /api/email/messages/{id} - should 404 with invalid account."""
        response = await client.delete(
            "/api/email/messages/msg-001?account_id=nonexistent"
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_send_email_no_account(self, client: AsyncClient, sample_send_email):
        """POST /api/email/messages - should 404 with invalid account_id."""
        response = await client.post(
            "/api/email/messages?account_id=nonexistent",
            json=sample_send_email,
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_send_email_imap(self, client: AsyncClient, sample_imap_setup, sample_send_email):
        """POST /api/email/messages - should send via IMAP/SMTP provider."""
        create_resp = await client.post("/api/email/auth/imap-setup", json=sample_imap_setup)
        account_id = create_resp.json()["id"]

        with patch("app.routers.email.get_email_provider") as mock_provider, \
             patch("app.routers.email.decrypt_value", return_value="password"):
            mock_instance = MagicMock()
            mock_instance.send_message = AsyncMock(return_value="sent-msg-001")
            mock_provider.return_value = mock_instance

            response = await client.post(
                f"/api/email/messages?account_id={account_id}",
                json=sample_send_email,
            )
            assert_response_ok(response)
            data = response.json()

            assert data["id"] == "sent-msg-001"
            assert "SENT" in data["labelIds"]


# ============================================================
# Labels
# ============================================================


class TestEmailLabels:
    """Tests for label management."""

    @pytest.mark.asyncio
    async def test_list_labels_no_account(self, client: AsyncClient):
        """GET /api/email/labels - should 404 with invalid account_id."""
        response = await client.get("/api/email/labels?account_id=nonexistent")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_list_labels_imap(self, client: AsyncClient, sample_imap_setup):
        """GET /api/email/labels - should return IMAP folders."""
        create_resp = await client.post("/api/email/auth/imap-setup", json=sample_imap_setup)
        account_id = create_resp.json()["id"]

        mock_folder = MagicMock()
        mock_folder.id = "INBOX"
        mock_folder.name = "Inbox"
        mock_folder.type = "system"
        mock_folder.messages_total = 42
        mock_folder.messages_unread = 5

        with patch("app.routers.email.get_email_provider") as mock_provider, \
             patch("app.routers.email.decrypt_value", return_value="password"):
            mock_instance = MagicMock()
            mock_instance.list_folders = AsyncMock(return_value=[mock_folder])
            mock_provider.return_value = mock_instance

            response = await client.get(f"/api/email/labels?account_id={account_id}")
            assert_response_ok(response)
            data = response.json()

            assert isinstance(data, list)
            assert len(data) == 1
            assert data[0]["id"] == "INBOX"
            assert data[0]["name"] == "Inbox"
            assert data[0]["messagesTotal"] == 42

    @pytest.mark.asyncio
    async def test_create_label_gmail_mock(self, client: AsyncClient, sample_imap_setup):
        """POST /api/email/labels - should create a label via Gmail API."""
        create_resp = await client.post("/api/email/auth/imap-setup", json=sample_imap_setup)
        account_id = create_resp.json()["id"]

        with patch("app.routers.email.get_gmail_service_for_account") as mock_factory:
            mock_gmail = AsyncMock()
            mock_gmail.create_label = AsyncMock(return_value={
                "id": "Label_123",
                "name": "Mon label",
                "type": "user",
            })
            mock_factory.return_value = mock_gmail

            response = await client.post(
                f"/api/email/labels?account_id={account_id}",
                json={"name": "Mon label"},
            )
            assert_response_ok(response)
            data = response.json()

            assert data["name"] == "Mon label"


# ============================================================
# Smart Features (Classification & Response Generation)
# ============================================================


class TestEmailSmartFeatures:
    """Tests for AI-powered email features."""

    @pytest.mark.asyncio
    async def test_classify_message_not_found(self, client: AsyncClient):
        """POST /api/email/messages/{id}/classify - should 404 when account doesn't exist."""
        # With no account in DB matching "fake-account", get_gmail_service_for_account
        # will raise HTTPException(404) before trying to fetch the message.
        response = await client.post(
            "/api/email/messages/nonexistent/classify?account_id=fake-account",
            json={"force_reclassify": False},
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_generate_response_not_found(self, client: AsyncClient):
        """POST /api/email/messages/{id}/generate-response - 404 for non-existent message."""
        response = await client.post(
            "/api/email/messages/nonexistent/generate-response?account_id=fake-account",
            json={"tone": "formal", "length": "medium"},
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_priority_invalid(self, client: AsyncClient):
        """PATCH /api/email/messages/{id}/priority - invalid priority value."""
        response = await client.patch(
            "/api/email/messages/msg-001/priority?account_id=fake-account",
            json={"priority": "invalid"},
        )
        # Should be 400 (invalid priority) or 404 (message not found)
        assert response.status_code in [400, 404]


# ============================================================
# Email Stats
# ============================================================


class TestEmailStats:
    """Tests for email statistics."""

    @pytest.mark.asyncio
    async def test_get_email_stats_empty(self, client: AsyncClient, sample_imap_setup):
        """GET /api/email/messages/stats - should return zero counts for new account."""
        create_resp = await client.post("/api/email/auth/imap-setup", json=sample_imap_setup)
        account_id = create_resp.json()["id"]

        response = await client.get(f"/api/email/messages/stats?account_id={account_id}")
        assert_response_ok(response)
        data = response.json()

        assert data["high"] == 0
        assert data["medium"] == 0
        assert data["low"] == 0
        assert data["total_unread"] == 0
        assert data["total"] == 0


# ============================================================
# Disconnect Account
# ============================================================


class TestEmailDisconnect:
    """Tests for disconnecting email accounts."""

    @pytest.mark.asyncio
    async def test_disconnect_nonexistent_account(self, client: AsyncClient):
        """DELETE /api/email/auth/disconnect/{id} - should 404."""
        response = await client.delete("/api/email/auth/disconnect/nonexistent")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_disconnect_imap_account(self, client: AsyncClient, sample_imap_setup):
        """DELETE /api/email/auth/disconnect/{id} - should delete IMAP account."""
        create_resp = await client.post("/api/email/auth/imap-setup", json=sample_imap_setup)
        account_id = create_resp.json()["id"]

        response = await client.delete(f"/api/email/auth/disconnect/{account_id}")
        assert_response_ok(response)
        data = response.json()

        assert data["deleted"] is True
        assert data["account_id"] == account_id

        # Verify account is gone
        status_resp = await client.get("/api/email/auth/status")
        assert status_resp.json()["connected"] is False


# ============================================================
# Draft Creation
# ============================================================


class TestEmailDrafts:
    """Tests for draft email creation."""

    @pytest.mark.asyncio
    async def test_create_draft_gmail_mock(self, client: AsyncClient, sample_imap_setup, sample_draft_email):
        """POST /api/email/messages/draft - should create draft via Gmail API."""
        create_resp = await client.post("/api/email/auth/imap-setup", json=sample_imap_setup)
        account_id = create_resp.json()["id"]

        with patch("app.routers.email.get_gmail_service_for_account") as mock_factory:
            mock_gmail = AsyncMock()
            mock_gmail.create_draft = AsyncMock(return_value={
                "id": "draft-001",
                "message": {"id": "msg-draft-001"},
            })
            mock_factory.return_value = mock_gmail

            response = await client.post(
                f"/api/email/messages/draft?account_id={account_id}",
                json=sample_draft_email,
            )
            assert_response_ok(response)
            data = response.json()

            assert data["id"] == "draft-001"


# ============================================================
# Modify Message (Labels)
# ============================================================


class TestEmailModifyMessage:
    """Tests for modifying message labels."""

    @pytest.mark.asyncio
    async def test_modify_message_no_account(self, client: AsyncClient):
        """PUT /api/email/messages/{id} - should 404 with invalid account."""
        response = await client.put(
            "/api/email/messages/msg-001?account_id=nonexistent",
            json={"add_label_ids": ["STARRED"]},
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_modify_message_gmail_mock(self, client: AsyncClient, sample_imap_setup):
        """PUT /api/email/messages/{id} - should modify labels via Gmail API."""
        create_resp = await client.post("/api/email/auth/imap-setup", json=sample_imap_setup)
        account_id = create_resp.json()["id"]

        with patch("app.routers.email.get_gmail_service_for_account") as mock_factory:
            mock_gmail = AsyncMock()
            mock_gmail.modify_message = AsyncMock(return_value={
                "id": "msg-001",
                "labelIds": ["INBOX", "STARRED"],
            })
            mock_factory.return_value = mock_gmail

            response = await client.put(
                f"/api/email/messages/msg-001?account_id={account_id}",
                json={"add_label_ids": ["STARRED"]},
            )
            assert_response_ok(response)
            data = response.json()

            assert "STARRED" in data["labelIds"]


# ============================================================
# Score CRM expéditeur (bug lcjp 11/06/2026)
# L'ancien code appelait qdrant.search(entity_type=...) - paramètre
# inexistant - et lisait .payload sur des dicts : le score CRM était
# silencieusement mort. La source de vérité est la table Contact (SQL).
# ============================================================


class TestCRMContactByEmail:
    """get_crm_contact_by_email : lookup SQL du contact CRM par email."""

    @pytest.mark.asyncio
    async def test_trouve_contact_insensible_a_la_casse(self, client: AsyncClient):
        import app.models.database as db_module
        from app.models.entities import Contact
        from app.routers.email import get_crm_contact_by_email

        async with db_module.AsyncSessionLocal() as session:
            contact = Contact(
                first_name="Léo", last_name="Martin",
                email="Leo.Martin@Aura-Conseil.fr", score=85, company="AURA",
            )
            session.add(contact)
            await session.commit()

            found = await get_crm_contact_by_email(session, "leo.martin@aura-conseil.fr")
            assert found is not None
            assert found.score == 85
            assert found.company == "AURA"

    @pytest.mark.asyncio
    async def test_absent_retourne_none(self, client: AsyncClient):
        import app.models.database as db_module
        from app.routers.email import get_crm_contact_by_email

        async with db_module.AsyncSessionLocal() as session:
            found = await get_crm_contact_by_email(session, "inconnu@nulle-part.fr")
            assert found is None

    @pytest.mark.asyncio
    async def test_email_vide_retourne_none(self, client: AsyncClient):
        import app.models.database as db_module
        from app.routers.email import get_crm_contact_by_email

        async with db_module.AsyncSessionLocal() as session:
            assert await get_crm_contact_by_email(session, "") is None
            assert await get_crm_contact_by_email(session, None) is None

    def test_plus_aucun_appel_qdrant_entity_type(self):
        """Le paramètre entity_type n'existe pas dans QdrantService.search."""
        from pathlib import Path

        content = Path("src/backend/app/routers/email.py").read_text(encoding="utf-8")
        assert "entity_type" not in content, (
            "email.py ne doit plus appeler qdrant.search(entity_type=...) - "
            "paramètre inexistant, le score CRM vient de la table Contact (SQL)"
        )
