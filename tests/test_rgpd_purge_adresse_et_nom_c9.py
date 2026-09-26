"""B-880 (cycle 9, relecteur U1) : l'anonymisation automatique laissait
l'adresse postale intacte et la notification qui lui survit gardait le nom de
la personne (« Paul Blanc a été anonymisé… ») : deux données personnelles
conservées après un effacement censé être complet (art. 17 RGPD)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, patch

import pytest
from app.models.entities import Contact, Notification, Preference
from app.services import rgpd_auto
from sqlmodel import select

from tests.rgpd_preavis import preavis_ancien_pour_tous


@pytest.mark.asyncio
async def test_l_adresse_est_effacee_et_la_notification_ne_nomme_personne(db_session) -> None:
    db_session.add(Preference(key="rgpd_purge_enabled", value="true"))
    db_session.add(Preference(key="rgpd_purge_months", value="12"))
    contact = Contact(
        first_name="Paul",
        last_name="Blanc",
        address="12 rue des Lilas, 04100 Manosque",
        last_interaction=datetime.now(UTC) - timedelta(days=13 * 30),
    )
    db_session.add(contact)
    await db_session.commit()
    cid = contact.id

    # B-1641 : l'anonymisation automatique exige un préavis de 30 jours.
    await preavis_ancien_pour_tous(db_session)
    with patch.object(rgpd_auto, "purge_contact_vector", new=AsyncMock(return_value=1)):
        resultat = await rgpd_auto.auto_purge_expired_contacts()
    assert resultat["anonymisations"] == 1

    db_session.expire_all()
    releve = (await db_session.execute(select(Contact).where(Contact.id == cid))).scalar_one()
    assert releve.address is None
    notifs = (
        (
            await db_session.execute(
                select(Notification).where(Notification.source == "rgpd_purge_done")
            )
        )
        .scalars()
        .all()
    )
    assert len(notifs) == 1
    assert "Paul" not in notifs[0].message and "Blanc" not in notifs[0].message, notifs[0].message
    assert "Lilas" not in notifs[0].message and "Manosque" not in notifs[0].message
