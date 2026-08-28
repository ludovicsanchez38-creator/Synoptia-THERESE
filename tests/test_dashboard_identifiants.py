"""Entrée 8 : le brief doit pouvoir ouvrir l'objet, pas seulement le module.

Le serveur connaît l'identifiant du message d'une relance — il s'en sert pour
récupérer l'objet et l'expéditeur — puis il le jette au moment de composer sa
réponse. Le brief ne peut donc pas ouvrir ce message : il ne peut qu'envoyer
vers la boîte entière, en laissant l'utilisateur retrouver la ligne à la main.

C'est le préalable de l'entrée 8, relevé en écrivant la table des
destinations : sans cet identifiant, « ouvrir l'objet » n'a rien à ouvrir.
"""
from datetime import UTC, datetime, timedelta

import pytest
from app.models.entities import Contact, EmailAccount, EmailFollowUp, EmailMessage


@pytest.mark.asyncio
async def test_une_relance_porte_l_identifiant_de_son_message(client, db_session):
    maintenant = datetime.now(UTC)
    contact = Contact(first_name="Paul", last_name="Rivière", email="p@forge.fr")
    compte = EmailAccount(id="acc-relance", email="ludo@example.test")
    message = EmailMessage(
        id="msg-relance",
        thread_id="thread-relance",
        account_id=compte.id,
        subject="Devis en attente",
        from_email="p@forge.fr",
        from_name="Paul Rivière",
        to_emails='["ludo@example.test"]',
        date=maintenant - timedelta(days=10),
        internal_date=maintenant - timedelta(days=10),
        labels='["INBOX"]',
    )
    db_session.add(contact)
    db_session.add(compte)
    db_session.add(message)
    await db_session.commit()

    db_session.add(
        EmailFollowUp(
            email_message_id="msg-relance",
            contact_id=contact.id,
            due_date=maintenant - timedelta(days=1),
            note="Relancer",
        )
    )
    await db_session.commit()

    reponse = await client.get("/api/dashboard/today")
    assert reponse.status_code == 200
    relances = reponse.json()["due_follow_ups"]
    assert relances, "la relance échue doit remonter"
    assert relances[0]["email_message_id"] == "msg-relance", (
        "sans cet identifiant, le brief ne peut ouvrir que la boîte entière"
    )
