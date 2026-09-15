"""B-883 (cycle 9, relecteur U3) : la synchronisation depuis Google Sheets
réécrivait `last_interaction` à chaque passage, y compris depuis une colonne
vide : une date posée localement (échange par e-mail, appel) disparaissait au
premier import sans colonne LastInteraction, et la purge RGPD retombait sur
`updated_at`."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from app.models.entities import Contact
from app.services.crm_sync import CRMSyncService, SyncStats
from sqlmodel import select


@pytest.mark.asyncio
async def test_une_colonne_vide_ne_gomme_pas_la_derniere_interaction(db_session) -> None:
    service = CRMSyncService(db_session, MagicMock())
    ligne = {
        "ID": "crm-42",
        "Nom": "Léa Martin",
        "Email": "lea@example.test",
        "LastInteraction": "2026-08-01T10:00:00",
    }
    await service._sync_contacts([ligne], SyncStats())
    await db_session.commit()

    sans_date = dict(ligne)
    sans_date["LastInteraction"] = ""
    await service._sync_contacts([sans_date], SyncStats())
    await db_session.commit()

    db_session.expire_all()
    contacts = (
        (await db_session.execute(select(Contact).where(Contact.email == "lea@example.test")))
        .scalars()
        .all()
    )
    assert len(contacts) == 1, [c.id for c in contacts]
    assert contacts[0].last_interaction is not None
    assert contacts[0].last_interaction.strftime("%Y-%m-%d") == "2026-08-01"
