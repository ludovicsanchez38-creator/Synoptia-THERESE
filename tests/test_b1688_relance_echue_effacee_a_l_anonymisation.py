"""B-1688 (lecteur de carte c13r-4) : B-1640 ne retirait que les préavis de
purge. La notification « Relance échue » (« Relance de Hélène Ménard prévue
il y a 3 jours ») survivait à l'anonymisation, manuelle ou automatique, et
gardait le nom de la personne effacée.
"""

import pytest
from sqlmodel import select


@pytest.mark.asyncio
async def test_anonymiser_retire_la_relance_echue_qui_nomme_la_personne(client, db_session):
    from app.models.entities import Contact, Notification

    db_session.add(Contact(id="c-relance-nom", first_name="Hélène", last_name="Ménard"))
    db_session.add(Notification(title="Relance echue", message="Relance de Hélène Ménard prevue il y a 3 jours",
                                type="action", source="crm", action_url="/crm/contacts/c-relance-nom",
                                action_label="Relancer"))
    await db_session.commit()

    reponse = await client.post("/api/rgpd/anonymize/c-relance-nom", json={"reason": "Demande"})
    assert reponse.status_code == 200, reponse.text

    db_session.expire_all()
    messages = [n.message for n in (await db_session.execute(select(Notification))).scalars().all()]
    assert all("Ménard" not in (m or "") for m in messages), messages
