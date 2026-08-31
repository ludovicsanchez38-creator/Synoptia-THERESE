"""Une date de relance e-mail est un jour civil Europe/Paris."""

from datetime import UTC, datetime

import pytest
from app.models.entities import EmailAccount, EmailFollowUp, EmailMessage
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_due_utilise_le_jour_de_paris_a_la_frontiere_utc(
    client: AsyncClient, db_session, monkeypatch
):
    """À 22 h 30 UTC en été, la relance du lendemain UTC est déjà due à Paris."""
    class DateUTC(datetime):
        @classmethod
        def now(cls, tz=None):
            instant = cls(2026, 8, 29, 22, 30, tzinfo=UTC)
            return instant.astimezone(tz) if tz else instant.replace(tzinfo=None)

    account = EmailAccount(id="account-follow-up-clock", email="ludo@example.test")
    message = EmailMessage(
        id="message-follow-up-clock",
        thread_id="thread-follow-up-clock",
        account_id=account.id,
        subject="Relance civile",
        from_email="client@example.test",
        to_emails='["ludo@example.test"]',
        date=datetime(2026, 8, 1, tzinfo=UTC),
        internal_date=datetime(2026, 8, 1, tzinfo=UTC),
        labels="[]",
    )
    follow_up = EmailFollowUp(
        id="follow-up-clock",
        email_message_id=message.id,
        due_date="2026-08-30T09:00:00",
    )
    db_session.add_all([account, message, follow_up])
    await db_session.commit()
    monkeypatch.setattr("app.routers.follow_ups.datetime", DateUTC)

    response = await client.get("/api/follow-ups/due")

    assert response.status_code == 200
    assert [item["id"] for item in response.json()] == [follow_up.id]
