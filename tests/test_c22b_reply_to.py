"""B-1296 : les adresses Reply-To traversent fournisseurs, cache et API."""
import json

import pytest
from imap_tools import MailMessage
from app.services.email.imap_smtp_provider import ImapSmtpProvider
from app.services.email.gmail_provider import GmailProvider
from app.services.gmail_service import format_message_for_storage
from app.routers.email import _message_cache_depuis_dto, _email_message_response


@pytest.mark.parametrize('entete,attendu', [
    ('"Dupont, Alice" <alice@example.fr>, bob@example.fr', ['alice@example.fr', 'bob@example.fr']),
    ('', []),
])
def test_imap_reply_to_puis_cache(entete, attendu):
    brut = f'From: robot@example.fr\r\nTo: moi@example.fr\r\nReply-To: {entete}\r\nSubject: Contact\r\n\r\nBonjour'.encode()
    message = MailMessage.from_bytes(brut)
    provider = ImapSmtpProvider.__new__(ImapSmtpProvider)
    dto = provider._imap_to_dto(message)
    assert dto.reply_to_emails == attendu
    assert _email_message_response(_message_cache_depuis_dto(dto, 'compte'))['reply_to_emails'] == attendu


def test_gmail_reply_to_puis_cache():
    message = {'id': 'm', 'threadId': 't', 'internalDate': '1000', 'payload': {
        'headers': [{'name': 'From', 'value': 'robot@example.fr'},
                    {'name': 'rEpLy-To', 'value': '"Dupont, Alice" <alice@example.fr>, bob@example.fr'}],
    }}
    stocke = format_message_for_storage(message)
    assert json.loads(stocke['reply_to_emails']) == ['alice@example.fr', 'bob@example.fr']
    dto = GmailProvider.__new__(GmailProvider)._gmail_to_dto(message)
    assert dto.reply_to_emails == ['alice@example.fr', 'bob@example.fr']


def test_migration_cache_existant_idempotente(tmp_path, monkeypatch):
    import sqlite3
    from app.models import database
    chemin = tmp_path / 'cache.db'
    with sqlite3.connect(chemin) as conn:
        conn.execute('CREATE TABLE email_messages (id TEXT PRIMARY KEY, contact_id TEXT)')
        conn.execute("INSERT INTO email_messages VALUES ('ancien', NULL)")
    monkeypatch.setattr(database, 'db_connect', sqlite3.connect)
    database.apply_adhoc_migrations(chemin)
    database.apply_adhoc_migrations(chemin)
    with sqlite3.connect(chemin) as conn:
        assert conn.execute('SELECT id, reply_to_emails FROM email_messages').fetchall() == [('ancien', None)]
