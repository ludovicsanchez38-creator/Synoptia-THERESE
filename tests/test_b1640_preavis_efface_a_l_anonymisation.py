"""B-1640 : la notification « Purge RGPD programmée » gardait le nom de la
personne après son anonymisation (« Hélène Ménard sera anonymisé le … »).
Rien ne l'effaçait, sauf l'effacement total. L'anonymisation, manuelle ou
automatique, retire désormais les préavis de la personne.
"""

import pytest
from sqlmodel import select


@pytest.mark.asyncio
async def test_anonymiser_retire_le_preavis_qui_nomme_la_personne(client, db_session):
    from app.models.entities import Contact, Notification

    db_session.add(Contact(id="c-preavis-nom", first_name="Hélène", last_name="Ménard"))
    db_session.add(Notification(title="Purge RGPD programmée", message="Hélène Ménard sera anonymisé le 01/01/2027",
                                type="warning", source="rgpd_purge", action_url="/crm/contacts/c-preavis-nom"))
    await db_session.commit()

    reponse = await client.post("/api/rgpd/anonymize/c-preavis-nom", json={"reason": "Demande"})
    assert reponse.status_code == 200, reponse.text

    db_session.expire_all()
    messages = [n.message for n in (await db_session.execute(select(Notification))).scalars().all()]
    assert all("Ménard" not in (m or "") for m in messages), messages
