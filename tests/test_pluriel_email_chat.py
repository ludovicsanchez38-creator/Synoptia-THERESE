"""Finding 1 (revue 30/08) : le chat e-mail parlait au premier compte de la table.

Deux comptes, aucun identifiant : on refuse. Un identifiant : on parle à
CE compte. Un seul compte : on le prend, comme avant.
"""

from __future__ import annotations

import pytest
from app.models.entities import EmailAccount


async def _deux_comptes(session):
    premier = EmailAccount(
        id="acc-gmail-a",
        email="a@gmail.com",
        provider="gmail",
        access_token="enc-a",
    )
    second = EmailAccount(
        id="acc-imap-b",
        email="b@imap.fr",
        provider="imap",
        imap_host="imap.imap.fr",
        imap_password="enc-b",
    )
    session.add(premier)
    session.add(second)
    await session.commit()
    return premier, second


@pytest.mark.asyncio
async def test_deux_comptes_sans_id_refuse_au_lieu_du_premier(db_session):
    """Gmail A créé en premier, IMAP B ensuite : sans id, aucun des deux."""
    await _deux_comptes(db_session)
    from app.services.workspace_tools import _get_email_provider

    provider, error = await _get_email_provider(db_session)

    assert provider is None
    assert error is not None
    assert "a@gmail.com" in error
    assert "b@imap.fr" in error


@pytest.mark.asyncio
async def test_deux_comptes_avec_id_prend_le_compte_demande(db_session, monkeypatch):
    """L'identifiant de l'écran (B) gagne, même si A est le premier de la table."""
    _premier, second = await _deux_comptes(db_session)
    vus: list[str] = []

    async def fake_ensure(account, session):
        vus.append(account.email)
        return "ya29.token-b"

    monkeypatch.setattr("app.routers.email.ensure_valid_access_token", fake_ensure)

    from app.services.email.gmail_provider import GmailProvider
    from app.services.workspace_tools import _get_email_provider

    # On force B en Gmail pour inspecter le token : le repro réel est
    # IMAP sélectionné vs Gmail premier, le critère est l'id, pas le provider.
    second.provider = "gmail"
    second.access_token = "enc-b"
    db_session.add(second)
    await db_session.commit()

    provider, error = await _get_email_provider(db_session, account_id="acc-imap-b")

    assert error is None
    assert isinstance(provider, GmailProvider)
    assert vus == ["b@imap.fr"]


@pytest.mark.asyncio
async def test_un_seul_compte_sans_id_lutilise(db_session, monkeypatch):
    """Un seul compte : on le prend, l'écran n'a pas à le répéter."""
    db_session.add(
        EmailAccount(id="acc-seul", email="seul@gmail.com", provider="gmail", access_token="enc")
    )
    await db_session.commit()

    async def fake_ensure(account, session):
        return "ya29.token-seul"

    monkeypatch.setattr("app.routers.email.ensure_valid_access_token", fake_ensure)

    from app.services.email.gmail_provider import GmailProvider
    from app.services.workspace_tools import _get_email_provider

    provider, error = await _get_email_provider(db_session)
    assert error is None
    assert isinstance(provider, GmailProvider)


@pytest.mark.asyncio
async def test_id_inconnu_refuse_sans_repli_sur_le_premier(db_session, monkeypatch):
    """Un id qui n'existe pas ne doit pas tomber silencieusement sur A."""
    await _deux_comptes(db_session)

    async def fake_ensure(account, session):
        raise AssertionError(f"aucun token ne doit être demandé, reçu {account.email}")

    monkeypatch.setattr("app.routers.email.ensure_valid_access_token", fake_ensure)

    from app.services.workspace_tools import _get_email_provider

    provider, error = await _get_email_provider(db_session, account_id="acc-absent")
    assert provider is None
    assert error is not None
    assert "introuvable" in error.lower() or "inconnu" in error.lower()


@pytest.mark.asyncio
async def test_destination_de_confirmation_nomme_l_expediteur(db_session):
    """La carte d'envoi doit dire DE QUI ça part, comme la carte agenda."""
    await _deux_comptes(db_session)
    from app.services.workspace_tools import get_email_confirmation_destination

    dest = await get_email_confirmation_destination(db_session, account_id="acc-imap-b")
    assert dest["account"] == "b@imap.fr"
    assert dest["account_id"] == "acc-imap-b"
