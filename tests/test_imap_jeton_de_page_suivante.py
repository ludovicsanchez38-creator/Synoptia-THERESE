"""B-351 (05/09/2026) : IMAP ne produisait jamais de jeton de page suivante.

La limite envoyée au serveur (`offset + max_results`) et le seuil de
détection d'une page suivante (`len(all_msgs) > offset + max_results`)
étaient la même expression : avec un serveur qui respecte la limite, la
condition ne pouvait jamais être vraie. Une boîte de 500 messages tenait en
une page de 20, sans suite. Il faut demander un message de plus pour savoir
qu'il en reste.
"""

from __future__ import annotations

from contextlib import contextmanager
from types import SimpleNamespace

import pytest


class _BoiteFactice:
    """Un serveur IMAP qui respecte scrupuleusement la limite demandée."""

    def __init__(self, total: int):
        self.total = total
        self.limites: list[int | None] = []

    def fetch(self, criteria, reverse=False, limit=None, **kwargs):
        self.limites.append(limit)
        n = self.total if limit is None else min(limit, self.total)
        return [SimpleNamespace(uid=str(i)) for i in range(n)]


def _provider(monkeypatch, boite: _BoiteFactice):
    from app.services.email.imap_smtp_provider import ImapSmtpProvider

    provider = ImapSmtpProvider(
        email_address="marie@atelier.test",
        password="secret",
        imap_host="imap.atelier.test",
    )

    @contextmanager
    def _connexion(**kwargs):
        yield boite

    monkeypatch.setattr(provider, "_connect_mailbox", _connexion)
    monkeypatch.setattr(provider, "_imap_to_dto", lambda msg, include_attachments=False: msg)
    return provider


@pytest.mark.asyncio
async def test_une_boite_de_500_messages_a_une_page_suivante(monkeypatch):
    boite = _BoiteFactice(total=500)
    provider = _provider(monkeypatch, boite)

    messages, jeton = await provider.list_messages(max_results=20)

    assert len(messages) == 20
    assert jeton == "20", "la page suivante n'est pas annoncée"


@pytest.mark.asyncio
async def test_la_derniere_page_n_annonce_pas_de_suite(monkeypatch):
    boite = _BoiteFactice(total=25)
    provider = _provider(monkeypatch, boite)

    messages, jeton = await provider.list_messages(max_results=20, page_token="20")

    assert len(messages) == 5
    assert jeton is None
