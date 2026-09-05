"""B-335 (05/09/2026) : un compte IMAP/SMTP enregistré laissait l'écran de
mise en route réclamer une messagerie.

L'assistant cherchait un compte `provider == 'smtp'` ; les deux seules
écritures du routeur posent `'imap'` (email.py:795 et :811). `has_smtp`
restait faux et voyageait jusqu'à l'interface (services/api/email.ts:96).
"""

from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_un_compte_imap_compte_comme_messagerie_configuree(client):
    from app.models import database as db_module
    from app.models.entities import EmailAccount
    from app.services.email_setup_assistant import EmailSetupAssistant

    async with db_module.AsyncSessionLocal() as session:
        session.add(EmailAccount(email="marie@atelier.test", provider="imap"))
        await session.commit()

    async with db_module.AsyncSessionLocal() as session:
        statut = await EmailSetupAssistant.detect_existing_credentials(session)

    assert statut.has_smtp is True
    assert statut.smtp_email == "marie@atelier.test"
    assert statut.has_gmail is False
