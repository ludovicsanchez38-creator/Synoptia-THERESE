"""B-836 (cycle 9) : la branche IMAP de GET /messages/{id} rendait le message sans
l'écrire en base, alors que generate-response, PATCH /priority et link-contact
le lisent en base : 404 « Message not found » sur tout compte IMAP."""
from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from app.services.email.base_provider import EmailMessageDTO


async def _poser_compte_imap(client) -> str:
    reponse = await client.post(
        "/api/email/auth/imap-setup",
        json={
            "email": "b836@example.invalid", "password": "mot-de-passe",
            "imap_host": "127.0.0.1", "imap_port": 9, "smtp_host": "127.0.0.1", "smtp_port": 9,
        },
    )
    assert reponse.status_code == 200, reponse.text
    return reponse.json()["id"]


@pytest.mark.asyncio
async def test_un_message_imap_lu_est_ensuite_utilisable(client):
    compte = await _poser_compte_imap(client)
    provider = MagicMock()
    provider.get_message = AsyncMock(return_value=EmailMessageDTO(
        id="imap-42", thread_id="fil-1", subject="Contrat", snippet="Peux-tu valider ?",
        from_email="camille@example.invalid", from_name="Camille", to_emails=["b836@example.invalid"],
        date=datetime(2026, 9, 15, 10, 0, tzinfo=UTC), body_plain="Corps du message", body_html=None,
    ))
    with (
        patch("app.routers.email.get_email_provider", return_value=provider),
        patch("app.routers.email.decrypt_value", return_value="secret"),
    ):
        lecture = await client.get(f"/api/email/messages/imap-42?account_id={compte}")
        assert lecture.status_code == 200, lecture.text
        assert lecture.json()["subject"] == "Contrat"

        priorite = await client.patch(
            f"/api/email/messages/imap-42/priority?account_id={compte}", json={"priority": "high"}
        )
    assert priorite.status_code == 200, f"{priorite.status_code} {priorite.text[:200]}"
