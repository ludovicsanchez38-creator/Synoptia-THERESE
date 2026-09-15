"""B-819 (cycle 9) : l'envoi SMTP était hors de tout try ; une panne du serveur
sortait en 500 générique là où les neuf branches IMAP rendent un 502 nommé."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

TEMOIN = "TEMOIN-SMTP-C9-boom"


async def _poser_compte_imap(client) -> str:
    reponse = await client.post(
        "/api/email/auth/imap-setup",
        json={
            "email": "b819@example.invalid", "password": "mot-de-passe",
            "imap_host": "127.0.0.1", "imap_port": 9, "smtp_host": "127.0.0.1", "smtp_port": 9,
        },
    )
    assert reponse.status_code == 200, reponse.text
    return reponse.json()["id"]


@pytest.mark.asyncio
async def test_une_panne_smtp_rend_un_502_nomme_sans_recopier_l_exception(client, caplog):
    compte = await _poser_compte_imap(client)
    provider = MagicMock()
    provider.send_message = AsyncMock(side_effect=RuntimeError(TEMOIN))
    with (
        patch("app.routers.email.get_email_provider", return_value=provider),
        patch("app.routers.email.decrypt_value", return_value="secret"),
        caplog.at_level("ERROR", logger="app.routers.email"),
    ):
        reponse = await client.post(
            f"/api/email/messages?account_id={compte}",
            json={"to": ["dest@example.invalid"], "subject": "objet", "body": "corps"},
        )
    assert reponse.status_code == 502, f"{reponse.status_code} {reponse.text[:200]}"
    assert TEMOIN not in reponse.text
    assert "SMTP" in reponse.json().get("message", ""), reponse.text[:200]
    assert TEMOIN in caplog.text
