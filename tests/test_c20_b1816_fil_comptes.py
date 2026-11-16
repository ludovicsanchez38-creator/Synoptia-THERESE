"""Le contexte d'un brouillon ne mélange pas les comptes de messagerie."""

from datetime import UTC, datetime

import pytest
from app.models.entities import EmailMessage
from app.services.email_response_generator import EmailResponseGenerator


@pytest.mark.asyncio
async def test_contexte_fil_limite_au_compte_du_message(client, db_session, monkeypatch):
    maintenant = datetime.now(UTC)

    def message(identifiant, compte, extrait):
        return EmailMessage(
            id=identifiant, thread_id="fil-partage", account_id=compte,
            from_email="expediteur@example.test", to_emails="[]", labels="[]",
            date=maintenant, internal_date=maintenant, snippet=extrait,
        )

    db_session.add_all([
        message("cible", "compte-a", "Message courant"),
        message("precedent-a", "compte-a", "Extrait autorisé du compte A"),
        message("precedent-b", "compte-b", "Extrait privé du compte B"),
    ])
    await db_session.commit()
    contexte = {}

    async def generation_fictive(**kwargs):
        contexte.update(kwargs)
        return "Brouillon fictif"

    monkeypatch.setattr(EmailResponseGenerator, "generate_response", generation_fictive)
    reponse = await client.post(
        "/api/email/messages/cible/generate-response",
        params={"account_id": "compte-a"}, json={},
    )
    assert reponse.status_code == 200
    assert "Extrait autorisé du compte A" in contexte["thread_context"]
    assert "Extrait privé du compte B" not in contexte["thread_context"]


@pytest.mark.asyncio
async def test_fil_sans_identifiant_ne_reunit_pas_des_messages_sans_fil(client, db_session, monkeypatch):
    maintenant = datetime.now(UTC)
    for identifiant in ("cible-sans-fil", "autre-sans-fil"):
        db_session.add(EmailMessage(
            id=identifiant, thread_id="", account_id="compte-a",
            from_email="expediteur@example.test", to_emails="[]", labels="[]",
            date=maintenant, internal_date=maintenant, snippet=identifiant,
        ))
    await db_session.commit()
    contexte = {}

    async def generation_fictive(**kwargs):
        contexte.update(kwargs)
        return "Brouillon fictif"

    monkeypatch.setattr(EmailResponseGenerator, "generate_response", generation_fictive)
    reponse = await client.post(
        "/api/email/messages/cible-sans-fil/generate-response",
        params={"account_id": "compte-a"}, json={},
    )
    assert reponse.status_code == 200
    assert contexte["thread_context"] is None

    autre_compte = await client.post(
        "/api/email/messages/cible-sans-fil/generate-response",
        params={"account_id": "compte-b"}, json={},
    )
    assert autre_compte.status_code == 404
