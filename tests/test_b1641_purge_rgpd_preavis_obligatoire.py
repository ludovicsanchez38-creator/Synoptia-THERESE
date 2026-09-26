"""B-1641 : la purge RGPD automatique anonymisait sans préavis.

Un contact importé (tableur, synchro Google Sheets) avec une « Dernière
interaction » de plus de 36 mois était anonymisé au démarrage suivant, e-mails
supprimés, sans la notification de 30 jours que promet le service. Reproduit :
{'notifications': 0, 'anonymisations': 1} au premier passage.

Règle : aucune anonymisation sans un préavis donné au moins 30 jours avant.
"""

from datetime import UTC, datetime, timedelta

import pytest
from sqlmodel import select


async def _contact_ancien(identifiant: str) -> None:
    from app.models.database import get_session_context
    from app.models.entities import Contact

    async with get_session_context() as session:
        session.add(Contact(id=identifiant, first_name="Hélène", last_name="Ménard",
                            last_interaction=datetime.now(UTC) - timedelta(days=4 * 365)))
        await session.commit()


async def _preavis(identifiant: str, il_y_a_jours: int) -> None:
    from app.models.database import get_session_context
    from app.models.entities import Notification

    async with get_session_context() as session:
        session.add(Notification(
            title="Purge RGPD programmée", message="préavis", type="warning", source="rgpd_purge",
            action_url=f"/crm/contacts/{identifiant}",
            created_at=datetime.now(UTC) - timedelta(days=il_y_a_jours),
        ))
        await session.commit()


async def _prenom(identifiant: str) -> str | None:
    from app.models.database import get_session_context
    from app.models.entities import Contact

    async with get_session_context() as session:
        return (await session.get(Contact, identifiant)).first_name


@pytest.mark.asyncio
async def test_sans_preavis_le_contact_est_prevenu_pas_anonymise(client):
    from app.models.database import get_session_context
    from app.models.entities import Notification
    from app.services.rgpd_auto import auto_purge_expired_contacts

    await _contact_ancien("c-sans-preavis")
    resultat = await auto_purge_expired_contacts()

    assert resultat["anonymisations"] == 0, resultat
    assert await _prenom("c-sans-preavis") == "Hélène"
    async with get_session_context() as session:
        preavis = (await session.execute(select(Notification).where(
            Notification.source == "rgpd_purge", Notification.action_url == "/crm/contacts/c-sans-preavis",
        ))).scalars().all()
    assert len(preavis) == 1


@pytest.mark.asyncio
async def test_un_preavis_de_moins_de_30_jours_fait_attendre(client):
    from app.services.rgpd_auto import auto_purge_expired_contacts

    await _contact_ancien("c-preavis-recent")
    await _preavis("c-preavis-recent", 10)
    await auto_purge_expired_contacts()

    assert await _prenom("c-preavis-recent") == "Hélène"


@pytest.mark.asyncio
async def test_un_preavis_de_30_jours_ou_plus_autorise_l_anonymisation(client):
    from app.services.rgpd_auto import auto_purge_expired_contacts

    await _contact_ancien("c-preavis-ancien")
    await _preavis("c-preavis-ancien", 31)
    resultat = await auto_purge_expired_contacts()

    assert resultat["anonymisations"] == 1, resultat
    assert await _prenom("c-preavis-ancien") == "[ANONYMISÉ]"
