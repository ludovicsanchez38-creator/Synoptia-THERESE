"""B-1667 : la purge RGPD automatique ignorait le consentement renouvelé.
« Renouveler le consentement » prolonge rgpd_date_expiration de 3 ans et
l'écran le promet, mais la purge ne lisait que les dates d'interaction : un
contact prolongé était quand même anonymisé, e-mails supprimés.
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, patch

import pytest

from tests.rgpd_preavis import preavis_ancien_pour_tous


async def _purger_un_contact(db_session, expiration):
    from app.models.entities import Contact, Preference
    from app.services import rgpd_auto

    db_session.add(Preference(key="rgpd_purge_enabled", value="true"))
    db_session.add(Preference(key="rgpd_purge_months", value="12"))
    db_session.add(Contact(id="c-consent", first_name="Hélène", last_name="Ménard",
                           last_interaction=datetime.now(UTC) - timedelta(days=4 * 365),
                           rgpd_date_expiration=expiration))
    await db_session.commit()
    await preavis_ancien_pour_tous(db_session)
    with patch.object(rgpd_auto, "purge_contact_vector", new=AsyncMock(return_value=1)):
        await rgpd_auto.auto_purge_expired_contacts()
    db_session.expire_all()
    return (await db_session.get(Contact, "c-consent")).first_name


@pytest.mark.asyncio
async def test_un_consentement_prolonge_protege_de_la_purge(db_session):
    assert await _purger_un_contact(db_session, datetime.now(UTC) + timedelta(days=3 * 365)) == "Hélène"


@pytest.mark.asyncio
async def test_temoin_une_expiration_passee_laisse_purger(db_session):
    # B-1670 : le préavis (posé il y a 31 jours) doit suivre la fin du
    # consentement ; un préavis antérieur appartient à un épisode passé.
    assert await _purger_un_contact(db_session, datetime.now(UTC) - timedelta(days=40)) == "[ANONYMISÉ]"
