"""B-841 (cycle 9) : la purge RGPD automatique ignorait les contacts sans prénom.

Le filtre `Contact.first_name != "[ANONYMISÉ]"` écarte, en SQL, toute ligne
dont `first_name` est NULL (une comparaison avec NULL n'est jamais vraie).
Un contact créé avec un nom seul, ou importé sans prénom, échappait donc
pour toujours à l'anonymisation, quelle que soit son ancienneté.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, patch

import pytest
from app.models.entities import Contact, Preference
from app.services import rgpd_auto
from sqlmodel import select


@pytest.mark.asyncio
async def test_un_contact_sans_prenom_est_anonymise_apres_la_retention(db_session) -> None:
    db_session.add(Preference(key="rgpd_purge_enabled", value="true"))
    db_session.add(Preference(key="rgpd_purge_months", value="12"))
    ancien = datetime.now(UTC) - timedelta(days=13 * 30)
    sans_prenom = Contact(
        first_name=None,
        last_name="Durand",
        email="durand@example.test",
        last_interaction=ancien,
    )
    avec_prenom = Contact(
        first_name="Léa",
        last_name="Martin",
        email="lea@example.test",
        last_interaction=ancien,
    )
    db_session.add(sans_prenom)
    db_session.add(avec_prenom)
    await db_session.commit()
    id_sans_prenom, id_avec_prenom = sans_prenom.id, avec_prenom.id

    with patch.object(rgpd_auto, "purge_contact_vector", new=AsyncMock(return_value=1)):
        resultat = await rgpd_auto.auto_purge_expired_contacts()

    assert resultat["anonymisations"] == 2, resultat

    db_session.expire_all()
    releve = await db_session.execute(
        select(Contact).where(Contact.id.in_([id_sans_prenom, id_avec_prenom]))
    )
    par_id = {c.id: c for c in releve.scalars().all()}
    assert par_id[id_avec_prenom].first_name == "[ANONYMISÉ]"
    assert par_id[id_sans_prenom].first_name == "[ANONYMISÉ]"
    assert par_id[id_sans_prenom].email is None
    assert par_id[id_sans_prenom].last_name is None
