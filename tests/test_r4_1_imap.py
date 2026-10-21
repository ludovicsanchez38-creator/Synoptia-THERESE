"""#103 : vrai imap_tools, imaplib doublé, boîte de 50 000 messages."""
import time
from contextlib import contextmanager
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from imap_tools import MailBox
from app.services.email.imap_smtp_provider import ImapSmtpProvider


class ServeurImapMemoire:
    def __init__(self, total=50000):
        self.total = total
        self.fetches = []

    def uid(self, operation, *args):
        if operation.upper() == 'SEARCH':
            return 'OK', [' '.join(map(str, range(1, self.total + 1))).encode()]
        assert operation.lower() == 'fetch'
        uids = [int(uid) for uid in args[0].split(',')]
        self.fetches.append((uids, args[1]))
        donnees = []
        for uid in sorted(uids):
            entetes = (f'From: camille@example.test\r\nTo: moi@example.test\r\nSubject: Message {uid}\r\nDate: Wed, 21 Oct 2026 10:00:00 +0200\r\n\r\n').encode()
            donnees.extend([(f'{uid} (UID {uid} FLAGS () RFC822.SIZE 3000000 BODY[HEADER] {{{len(entetes)}}}'.encode(), entetes), b')'])
        return 'OK', donnees


@pytest.mark.asyncio
@pytest.mark.parametrize('offset', [0, 10000, 49980])
async def test_fetch_borne_aux_entetes_de_la_page(monkeypatch, offset, record_property):
    serveur = ServeurImapMemoire()
    mailbox = object.__new__(MailBox)
    mailbox.client = serveur
    provider = ImapSmtpProvider('moi@example.test', 'fictif', 'imap.example.test')
    @contextmanager
    def connexion(**kwargs):
        yield mailbox
    monkeypatch.setattr(provider, '_connect_mailbox', connexion)
    debut = time.monotonic()
    messages, token = await provider.list_messages(max_results=20, page_token=str(offset))
    duree = time.monotonic() - debut
    nombre = sum(len(uids) for uids, _ in serveur.fetches)
    record_property('messages_fetches', nombre)
    record_property('duree_secondes', duree)
    assert nombre <= 21, (offset, nombre)
    assert len(serveur.fetches) == 1
    assert all('BODY.PEEK[HEADER]' in champs for _, champs in serveur.fetches)
    assert messages[0].subject == f'Message {50000 - offset}'
    assert len(messages) == 20
    assert token == (str(offset + 20) if offset < 49980 else None)
    assert duree < 1


@pytest.mark.asyncio
async def test_timeout_http_explicite_jamais_liste_vide(client, db_session, monkeypatch):
    from app.models.entities import EmailAccount
    from app.routers import email
    compte = EmailAccount(id='r4-imap', email='moi@example.test', provider='imap', imap_host='imap.example.test', imap_password='fictif')
    db_session.add(compte)
    await db_session.commit()
    fake = SimpleNamespace(list_messages=AsyncMock(side_effect=TimeoutError('fictif')))
    monkeypatch.setattr(email, 'get_email_provider', lambda **kw: fake)
    monkeypatch.setattr(email, 'decrypt_value', lambda v: 'fictif')
    rep = await client.get('/api/email/messages', params={'account_id': compte.id})
    assert rep.status_code == 504
    assert 'Réessaie' in rep.text
    assert 'aucun' not in rep.text.lower()
    assert 'messages' not in rep.json()
