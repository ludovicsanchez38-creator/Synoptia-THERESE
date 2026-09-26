"""B-894 (cycle 9, relecteur V3) : les compteurs de la purge automatique étaient
incrémentés au fil de la boucle et rendus tels quels quand le commit final
levait : l'appelant croyait à N anonymisations alors que rien n'était écrit."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, patch

import pytest
from app.models.entities import Activity, Contact, Preference
from app.services import rgpd_auto
from sqlalchemy.ext.asyncio import AsyncSession

from tests.rgpd_preavis import preavis_ancien_pour_tous


@pytest.mark.asyncio
async def test_un_commit_qui_echoue_rend_des_compteurs_a_zero(db_session) -> None:
    db_session.add(Preference(key="rgpd_purge_enabled", value="true"))
    db_session.add(Preference(key="rgpd_purge_months", value="12"))
    db_session.add(
        Contact(
            first_name="Paul",
            last_name="Blanc",
            last_interaction=datetime.now(UTC) - timedelta(days=13 * 30),
        )
    )
    await db_session.commit()

    commit_reel = AsyncSession.commit

    async def commit_defaillant(self: AsyncSession) -> None:
        # Seul le commit qui porte l'anonymisation échoue ; les lectures de
        # préférences (qui committent aussi en sortie de contexte) passent.
        if any(isinstance(objet, Activity) for objet in self.new):
            raise RuntimeError("disque plein")
        await commit_reel(self)

    # B-1641 : l'anonymisation automatique exige un préavis de 30 jours.
    await preavis_ancien_pour_tous(db_session)
    with (
        patch.object(rgpd_auto, "purge_contact_vector", new=AsyncMock(return_value=1)),
        patch.object(AsyncSession, "commit", new=commit_defaillant),
    ):
        resultat = await rgpd_auto.auto_purge_expired_contacts()

    assert resultat == {"notifications": 0, "anonymisations": 0}, resultat
