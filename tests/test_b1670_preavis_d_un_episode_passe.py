"""B-1670 (lecteur de carte c13r-2) : la purge RGPD comptait le plus ancien
préavis de toute la vie d'une fiche.

B-1641 exige un préavis donné 30 jours avant l'anonymisation, mais
`_premier_preavis` prenait le plus ancien préavis jamais émis. Une fiche
prévenue il y a longtemps, puis relancée (nouvelle interaction) ou protégée par
un consentement renouvelé, était anonymisée le jour où elle redevenait
échue, sans nouveau préavis. Seul compte désormais un préavis donné pendant
l'épisode en cours.
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, patch

import pytest


async def _purger(db_session, *, derniere_interaction_jours: int, preavis_jours: int,
                  expiration: datetime | None = None) -> str | None:
    from app.models.entities import Contact, Notification, Preference
    from app.services import rgpd_auto

    maintenant = datetime.now(UTC)
    db_session.add(Preference(key="rgpd_purge_enabled", value="true"))
    db_session.add(Preference(key="rgpd_purge_months", value="12"))
    db_session.add(Contact(id="c-episode", first_name="Hélène", last_name="Ménard",
                           last_interaction=maintenant - timedelta(days=derniere_interaction_jours),
                           rgpd_date_expiration=expiration))
    db_session.add(Notification(
        title="Purge RGPD programmée", message="préavis", type="warning", source="rgpd_purge",
        action_url="/crm/contacts/c-episode", created_at=maintenant - timedelta(days=preavis_jours),
    ))
    await db_session.commit()
    with patch.object(rgpd_auto, "purge_contact_vector", new=AsyncMock(return_value=1)):
        await rgpd_auto.auto_purge_expired_contacts()
    db_session.expire_all()
    return (await db_session.get(Contact, "c-episode")).first_name


@pytest.mark.asyncio
async def test_un_preavis_anterieur_a_la_derniere_interaction_ne_compte_pas(db_session):
    # Prévenue il y a 500 jours, relancée il y a 425 jours (14 mois) : échue
    # de nouveau depuis deux mois, elle doit recevoir un nouveau préavis.
    assert await _purger(db_session, derniere_interaction_jours=425, preavis_jours=500) == "Hélène"


@pytest.mark.asyncio
async def test_un_preavis_anterieur_au_consentement_renouvele_ne_compte_pas(db_session):
    # Prévenue il y a 400 jours, consentement renouvelé depuis, arrivé à
    # expiration avant-hier : un nouveau préavis de 30 jours est dû.
    expiration = datetime.now(UTC) - timedelta(days=2)
    assert await _purger(db_session, derniere_interaction_jours=4 * 365, preavis_jours=400,
                         expiration=expiration) == "Hélène"


@pytest.mark.asyncio
async def test_temoin_un_preavis_de_l_episode_en_cours_laisse_purger(db_session):
    assert await _purger(db_session, derniere_interaction_jours=425, preavis_jours=40) == "[ANONYMISÉ]"
