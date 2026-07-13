"""Contrats du routeur Email partagés par l’interface classique et la 0.40."""

import base64

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.entities import EmailAccount


@pytest.mark.asyncio
async def test_create_draft_routes_to_imap_provider(client, db_session):
    account = EmailAccount(
        id="imap-draft-account",
        email="ludo@example.test",
        provider="imap",
        imap_host="imap.example.test",
        imap_port=993,
        imap_username="ludo@example.test",
        imap_password="encrypted-password",
        smtp_host="smtp.example.test",
        smtp_port=587,
        smtp_use_tls=True,
    )
    db_session.add(account)
    await db_session.commit()

    provider = MagicMock()
    provider.create_draft = AsyncMock(return_value="draft-imap-1")

    with (
        patch("app.routers.email.get_email_provider", return_value=provider),
        patch("app.routers.email.decrypt_value", return_value="secret"),
    ):
        response = await client.post(
            "/api/email/messages/draft",
            params={"account_id": account.id},
            json={
                "to": ["client@example.test"],
                "subject": "Proposition",
                "body": "Bonjour",
            },
        )

    assert response.status_code == 200, response.text
    assert response.json() == {"id": "draft-imap-1", "labelIds": ["DRAFT"]}
    request = provider.create_draft.await_args.args[0]
    assert request.to == ["client@example.test"]
    assert request.subject == "Proposition"
    assert request.body == "Bonjour"


@pytest.mark.asyncio
async def test_create_draft_returns_404_for_unknown_account(client):
    response = await client.post(
        "/api/email/messages/draft",
        params={"account_id": "missing"},
        json={"to": ["client@example.test"], "subject": "Test", "body": "Texte"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_gmail_message_returns_normalized_contract(client, db_session):
    account = EmailAccount(
        id="gmail-message-account",
        email="ludo@gmail.test",
        provider="gmail",
        access_token="encrypted-token",
    )
    db_session.add(account)
    await db_session.commit()

    raw_message = {
        "id": "gmail-message-1",
        "threadId": "thread-1",
        "internalDate": "1783931400000",
        "labelIds": ["INBOX", "UNREAD"],
        "snippet": "Aperçu Gmail",
        "payload": {
            "headers": [
                {"name": "From", "value": "Camille <camille@example.test>"},
                {"name": "To", "value": "ludo@gmail.test"},
                {"name": "Subject", "value": "Sujet réel"},
            ],
            "mimeType": "text/plain",
            "body": {
                "data": base64.urlsafe_b64encode(b"Corps Gmail normalise").decode(),
            },
        },
    }
    gmail = MagicMock()
    gmail.get_message = AsyncMock(return_value=raw_message)

    with patch(
        "app.routers.email.get_gmail_service_for_account",
        new=AsyncMock(return_value=gmail),
    ):
        response = await client.get(
            "/api/email/messages/gmail-message-1",
            params={"account_id": account.id},
        )

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["id"] == "gmail-message-1"
    assert data["thread_id"] == "thread-1"
    assert data["from_email"] == "camille@example.test"
    assert data["to_emails"] == ["ludo@gmail.test"]
    assert data["body_plain"] == "Corps Gmail normalise"
    assert data["is_read"] is False
