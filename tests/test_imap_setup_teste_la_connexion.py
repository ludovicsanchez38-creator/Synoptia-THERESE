"""B-194 (P-008, décision de Ludo) : la configuration d'un compte IMAP annonçait
« configuré » sans jamais se connecter. La connexion est testée avant
d'enregistrer, et une panne dit pourquoi."""

from __future__ import annotations

import pytest
from sqlalchemy import func, select

CORPS = {
    "email": "marie@atelier.test",
    "password": "faux-mot-de-passe",
    "imap_host": "imap.atelier.test",
    "imap_port": 993,
    "smtp_host": "smtp.atelier.test",
    "smtp_port": 587,
}


@pytest.mark.asyncio
async def test_une_connexion_qui_echoue_refuse_la_configuration(client, db_session, monkeypatch):
    from app.models.entities import EmailAccount
    from app.services.email import imap_smtp_provider as module

    async def _panne(self):
        return {"success": False, "imap_ok": False, "smtp_ok": True, "message": "IMAP : identifiants refusés par le serveur"}

    monkeypatch.setattr(module.ImapSmtpProvider, "test_connection", _panne)

    reponse = await client.post("/api/email/auth/imap-setup", json=CORPS)
    assert reponse.status_code == 400, reponse.text
    texte = reponse.text
    assert "identifiants refusés" in texte
    compte = (await db_session.execute(select(func.count()).select_from(EmailAccount))).scalar_one()
    assert compte == 0, "un compte injoignable a été enregistré quand même"


@pytest.mark.asyncio
async def test_une_connexion_qui_reussit_enregistre_le_compte(client):
    reponse = await client.post("/api/email/auth/imap-setup", json=CORPS)
    assert reponse.status_code == 200, reponse.text
    assert reponse.json()["provider"] == "imap"


@pytest.mark.imap_reel
@pytest.mark.asyncio
async def test_la_vraie_sonde_qui_reussit_enregistre_le_compte(client, monkeypatch):
    """Revue COCO 0.68.0 (P1) : la route lisait `verdict["ok"]` alors que la vraie
    `test_connection()` répond `success` (+ `imap_ok`, `smtp_ok`). Tout compte
    IMAP valide sortait en 400 ; la fixture de test masquait le contrat."""
    from unittest.mock import AsyncMock, patch

    from app.services.email import imap_smtp_provider as module

    with patch.object(module.ImapSmtpProvider, "_connect_mailbox"), patch(
        "app.services.email.imap_smtp_provider.aiosmtplib.SMTP"
    ) as faux_smtp:
        faux_smtp.return_value = AsyncMock()
        reponse = await client.post("/api/email/auth/imap-setup", json=CORPS)
    assert reponse.status_code == 200, reponse.text
    assert reponse.json()["provider"] == "imap"
