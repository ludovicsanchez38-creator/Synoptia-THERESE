"""Les heures de notification correspondent à des instants UTC explicites."""

from datetime import UTC, datetime, timedelta

import pytest
from app.models.entities import Notification


@pytest.mark.asyncio
async def test_notifications_renvoient_des_instants_dates_en_utc(client, db_session):
    db_session.add(Notification(
        id="notification-test", title="Rappel", message="Donnée fictive",
        is_read=True, created_at=datetime(2026, 11, 16, 9, 0),
        read_at=datetime(2026, 11, 16, 9, 3),
    ))
    await db_session.commit()

    reponse = await client.get("/api/notifications")
    assert reponse.status_code == 200
    notification = next(n for n in reponse.json() if n["id"] == "notification-test")
    for champ, minute in (("created_at", 0), ("read_at", 3)):
        instant = datetime.fromisoformat(notification[champ].replace("Z", "+00:00"))
        assert instant.utcoffset() == timedelta(0)
        assert instant == datetime(2026, 11, 16, 9, minute, tzinfo=UTC)
