"""B-1802 : le message envoyé et sa copie gardent une date exploitable."""
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from email import message_from_bytes
from email.utils import parsedate_to_datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

from app.services.email import imap_smtp_provider as module
from app.services.email.base_provider import SendEmailRequest
from app.services.email.imap_smtp_provider import ImapSmtpProvider
from imap_tools import MailMessage


async def test_envoi_et_copie_envoyes_portent_date_et_identifiant(monkeypatch):
    provider = ImapSmtpProvider("moi@example.test", "fictif", "imap.example.test")
    archives = []
    mailbox = SimpleNamespace(append=lambda message, folder, **kw: archives.append(message))

    @contextmanager
    def connexion(**kwargs):
        yield mailbox

    smtp = AsyncMock()
    monkeypatch.setattr(module.aiosmtplib, "send", smtp)
    monkeypatch.setattr(provider, "_connect_mailbox", connexion)
    monkeypatch.setattr(provider, "resolve_folder_for_label", AsyncMock(return_value="Sent"))
    await provider.send_message(SendEmailRequest(to=["toi@example.test"], subject="Essai", body="Bonjour"))

    envoye = smtp.call_args.args[0]
    assert envoye["Date"], "en-tête Date absent"
    assert envoye["Message-ID"], "en-tête Message-ID absent"
    instant = parsedate_to_datetime(envoye["Date"])
    assert instant.tzinfo is not None
    assert abs(datetime.now(UTC) - instant) < timedelta(minutes=5)
    copie = message_from_bytes(archives[0])
    assert copie["Date"] == envoye["Date"]
    assert copie["Message-ID"] == envoye["Message-ID"]
    assert abs(datetime.now(UTC) - MailMessage.from_bytes(archives[0]).date) < timedelta(minutes=5)
