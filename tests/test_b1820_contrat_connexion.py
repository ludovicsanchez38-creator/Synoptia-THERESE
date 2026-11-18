"""B-1820 : un échec IMAP/SMTP doit être faux pour le contrat commun."""
from unittest.mock import AsyncMock, patch

import pytest
from app.services.email.imap_smtp_provider import ImapSmtpProvider


@pytest.mark.imap_reel
async def test_echec_et_succes_de_connexion_sont_des_booleens():
    provider = ImapSmtpProvider("moi@example.test", "fictif", "imap.example.test")
    with (
        patch.object(provider, "_connect_mailbox", side_effect=ConnectionError("refus")),
        patch("app.services.email.imap_smtp_provider.aiosmtplib.SMTP", return_value=AsyncMock()),
    ):
        resultat = await provider.test_connection()
    assert resultat is False, "un échec IMAP doit renvoyer False"

    with (
        patch.object(provider, "_connect_mailbox"),
        patch("app.services.email.imap_smtp_provider.aiosmtplib.SMTP", return_value=AsyncMock()),
    ):
        assert await provider.test_connection() is True
