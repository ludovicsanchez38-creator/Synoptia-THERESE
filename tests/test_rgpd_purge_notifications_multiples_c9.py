"""B-878 (cycle 9, relecteur U3) : `scalar_one_or_none()` sur les notifications
de purge. Deux notifications d'avertissement pour un même contact (deux
campagnes à quelques jours d'intervalle, ou un doublon) faisaient lever
MultipleResultsFound, avalée par l'except global : toute la campagne du jour
s'arrêtait, avertissements et anonymisations compris."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, patch

import pytest
from app.models.entities import Contact, Notification, Preference
from app.services import rgpd_auto
from sqlmodel import select


@pytest.mark.asyncio
async def test_deux_notifications_pour_un_contact_n_arretent_pas_la_campagne(db_session) -> None:
    db_session.add(Preference(key="rgpd_purge_enabled", value="true"))
    db_session.add(Preference(key="rgpd_purge_months", value="12"))
    a_prevenir = Contact(
        first_name="Anne",
        last_name="Roux",
        last_interaction=datetime.now(UTC) - timedelta(days=12 * 30 - 10),
    )
    a_anonymiser = Contact(
        first_name="Paul",
        last_name="Blanc",
        last_interaction=datetime.now(UTC) - timedelta(days=13 * 30),
    )
    db_session.add(a_prevenir)
    db_session.add(a_anonymiser)
    await db_session.commit()
    for _ in range(2):
        db_session.add(
            Notification(
                title="Purge RGPD programmée",
                message="x",
                type="warning",
                source="rgpd_purge",
                action_url=f"/crm/contacts/{a_prevenir.id}",
            )
        )
    await db_session.commit()
    id_anonymiser = a_anonymiser.id

    with patch.object(rgpd_auto, "purge_contact_vector", new=AsyncMock(return_value=1)):
        resultat = await rgpd_auto.auto_purge_expired_contacts()

    assert resultat["anonymisations"] == 1, resultat
    db_session.expire_all()
    releve = await db_session.execute(select(Contact).where(Contact.id == id_anonymiser))
    assert releve.scalar_one().first_name == "[ANONYMISÉ]"
