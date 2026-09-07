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
        return {"ok": False, "message": "IMAP : identifiants refusés par le serveur"}

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
