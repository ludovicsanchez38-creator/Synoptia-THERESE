"""Le message ne prétend pas qu'un renouvellement a eu lieu sans appel."""

from datetime import UTC, datetime, timedelta
from unittest.mock import Mock

import pytest
from app.models.entities import EmailAccount
from app.routers import email


@pytest.mark.asyncio
async def test_mise_a_jour_sans_renouvellement_ne_l_annonce_pas(client, db_session, monkeypatch):
    db_session.add(EmailAccount(
        id="compte-test", email="personne@example.test",
        access_token="acces-fictif", refresh_token="renouvellement-fictif",
        token_expiry=datetime.now(UTC) + timedelta(hours=2),
    ))
    await db_session.commit()
    monkeypatch.setattr(email, "encrypt_value", lambda valeur: valeur)
    service = Mock(side_effect=AssertionError("aucun appel OAuth attendu"))
    monkeypatch.setattr(email, "get_oauth_service", service)

    reponse = await client.post(
        "/api/email/auth/update-credentials/compte-test",
        json={"client_id": "identifiant-fictif", "client_secret": "donnee-fictive"},
    )
    assert reponse.status_code == 200
    service.assert_not_called()
    message = reponse.json()["message"].lower()
    assert "refreshed" not in message
    assert "rafraîchi" not in message
