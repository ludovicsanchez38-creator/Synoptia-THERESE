"""#103 : tous les APPEND doivent fournir un instant avec fuseau."""
from contextlib import contextmanager
from email.utils import format_datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from app.services.email.base_provider import SendEmailRequest
from app.services.email.imap_smtp_provider import ImapSmtpProvider


@pytest.mark.asyncio
@pytest.mark.parametrize('operation', ['envoyer', 'creer_brouillon', 'modifier_brouillon'])
async def test_append_archive_avec_fuseau(monkeypatch, operation):
    from app.services.email import imap_smtp_provider as module
    provider = ImapSmtpProvider('moi@example.test', 'fictif', 'imap.example.test')
    archives = []
    def append(message, folder, dt=None, **kwargs):
        # Même précondition que imaplib.Time2Internaldate.
        assert dt.tzinfo is not None and dt.utcoffset() is not None
        format_datetime(dt)
        archives.append((folder, message, dt))
        return 'OK', [b'[APPENDUID 1 42]']
    mailbox = SimpleNamespace(append=append, delete=lambda ids: None, folder=SimpleNamespace(set=lambda f: None))
    @contextmanager
    def connexion(**kwargs):
        yield mailbox
    monkeypatch.setattr(provider, '_connect_mailbox', connexion)
    monkeypatch.setattr(provider, '_dossier_brouillons', lambda m: 'Drafts')
    monkeypatch.setattr(provider, 'resolve_folder_for_label', AsyncMock(return_value='Sent'))
    smtp = AsyncMock()
    monkeypatch.setattr(module.aiosmtplib, 'send', smtp)
    request = SendEmailRequest(to=['toi@example.test'], subject='Essai local', body='Fictif')
    if operation == 'envoyer':
        identifiant = await provider.send_message(request)
        smtp.assert_awaited_once()
    elif operation == 'creer_brouillon':
        identifiant = await provider.create_draft(request)
    else:
        identifiant = await provider.update_draft('21', request)
    assert identifiant == '42'
    assert len(archives) == 1
    assert archives[0][0] == ('Sent' if operation == 'envoyer' else 'Drafts')
    assert b'Essai local' in archives[0][1]
