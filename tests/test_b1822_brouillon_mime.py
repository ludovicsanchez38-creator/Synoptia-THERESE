"""B-1822 : les brouillons IMAP conservent leur fil et leurs pièces jointes."""
from contextlib import contextmanager
from email import message_from_bytes
from types import SimpleNamespace

import pytest
from app.services.email.base_provider import SendEmailRequest
from app.services.email.imap_smtp_provider import ImapSmtpProvider


@pytest.mark.parametrize("operation", ["create", "update"])
@pytest.mark.parametrize("html", [False, True])
async def test_brouillon_enregistre_conserve_fil_et_piece(monkeypatch, operation, html):
    provider = ImapSmtpProvider("moi@example.test", "fictif", "imap.example.test")
    archives = []
    mailbox = SimpleNamespace(
        append=lambda data, folder, **kw: (archives.append(data) or ("OK", [b"[APPENDUID 1 42]"])),
        folder=SimpleNamespace(set=lambda dossier: None),
        delete=lambda ids: None,
    )

    @contextmanager
    def connexion(**kwargs):
        yield mailbox

    monkeypatch.setattr(provider, "_connect_mailbox", connexion)
    monkeypatch.setattr(provider, "_dossier_brouillons", lambda _mailbox: "Drafts")
    demande = SendEmailRequest(
        to=["toi@example.test"], bcc=["copie@example.test"], subject="Réponse", body="Bonjour",
        is_html=html, in_reply_to="<origine@example.test>", references="<origine@example.test>",
        attachments=[("devis.pdf", b"piece-test", "application/pdf")],
    )
    if operation == "create":
        await provider.create_draft(demande)
    else:
        await provider.update_draft("21", demande)

    message = message_from_bytes(archives[0])
    assert message["In-Reply-To"] == "<origine@example.test>"
    assert message["References"] == "<origine@example.test>"
    assert message["Bcc"] == "copie@example.test"
    pieces = [part for part in message.walk() if part.get_filename()]
    assert len(pieces) == 1
    assert pieces[0].get_filename() == "devis.pdf"
    assert pieces[0].get_content_type() == "application/pdf"
    assert pieces[0].get_payload(decode=True) == b"piece-test"
    assert message.get_content_type() == "multipart/mixed"
