from datetime import UTC, datetime

import pytest
from app.models.entities import Contact, EmailAccount, EmailMessage
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_follow_up_crud_returns_email_context(
    async_client: AsyncClient,
    db_session,
):
    now = datetime.now(UTC)
    contact = Contact(first_name="Camille", last_name="Martin")
    account = EmailAccount(email="ludo@example.test")
    message = EmailMessage(
        id="message-follow-up",
        thread_id="thread-follow-up",
        account_id=account.id,
        subject="Proposition à valider",
        from_email="camille@example.test",
        from_name="Camille Martin",
        to_emails='["ludo@example.test"]',
        date=now,
        internal_date=now,
        labels='["INBOX"]',
        contact_id=contact.id,
    )
    db_session.add_all([contact, account, message])
    await db_session.commit()

    created_response = await async_client.post(
        "/api/follow-ups",
        json={
            "email_message_id": message.id,
            "contact_id": contact.id,
            "due_date": "2026-07-16T09:00:00",
            "note": "Rappeler après lecture",
        },
    )
    assert created_response.status_code == 200, created_response.text
    created = created_response.json()
    assert created["email_subject"] == "Proposition à valider"
    assert created["email_from"] == "Camille Martin"
    assert created["contact_name"] == "Camille Martin"

    list_response = await async_client.get("/api/follow-ups?status=pending")
    assert list_response.status_code == 200
    assert list_response.json()[0]["email_subject"] == "Proposition à valider"

    updated_response = await async_client.put(
        f"/api/follow-ups/{created['id']}",
        json={"status": "done", "due_date": "2026-07-17T09:00:00"},
    )
    assert updated_response.status_code == 200
    assert updated_response.json()["status"] == "done"

    delete_response = await async_client.delete(f"/api/follow-ups/{created['id']}")
    assert delete_response.status_code == 200
    assert (await async_client.get("/api/follow-ups")).json() == []
