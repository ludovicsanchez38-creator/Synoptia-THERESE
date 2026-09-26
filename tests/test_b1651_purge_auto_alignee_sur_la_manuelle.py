"""B-1651 (décision de Ludo, 26/09 : aligner la purge automatique sur la
manuelle) : la purge RGPD automatique n'effaçait que la fiche et ses e-mails.
Nom, courriel et adresse restaient dans les tâches, brouillons de facture,
prestations, activités et projets de la personne, que la route manuelle
efface. Les deux passent désormais par le même traitement.
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, patch

import pytest
from sqlmodel import select

from tests.rgpd_preavis import preavis_ancien_pour_tous


@pytest.mark.asyncio
async def test_la_purge_automatique_efface_comme_la_manuelle(db_session):
    from app.models.entities import (
        Activity,
        Contact,
        Invoice,
        Preference,
        Prestation,
        Project,
        Task,
    )
    from app.services import rgpd_auto

    db_session.add(Preference(key="rgpd_purge_enabled", value="true"))
    db_session.add(Preference(key="rgpd_purge_months", value="12"))
    contact = Contact(id="c-aligne", first_name="Hélène", last_name="Ménard", email="helene@exemple.test",
                      last_interaction=datetime.now(UTC) - timedelta(days=13 * 30))
    db_session.add(contact)
    await db_session.commit()
    db_session.add(Task(id="t-aligne", title="Rappeler Hélène Ménard", contact_id="c-aligne"))
    db_session.add(Prestation(id="p-aligne", contact_id="c-aligne", intitule="Accompagnement Ménard", phase="discovery"))
    db_session.add(Project(id="d-aligne", name="Dossier Ménard", contact_id="c-aligne"))
    db_session.add(Activity(contact_id="c-aligne", type="note", title="Appel avec Hélène Ménard"))
    db_session.add(Invoice(id="f-aligne", invoice_number="FAC-TEST-1", contact_id="c-aligne", status="draft",
                           client_name="Hélène Ménard", client_email="helene@exemple.test",
                           issue_date=datetime.now(UTC), due_date=datetime.now(UTC)))
    await db_session.commit()
    await preavis_ancien_pour_tous(db_session)

    with patch.object(rgpd_auto, "purge_contact_vector", new=AsyncMock(return_value=1)):
        resultat = await rgpd_auto.auto_purge_expired_contacts()
    assert resultat["anonymisations"] == 1, resultat

    db_session.expire_all()
    assert await db_session.get(Task, "t-aligne") is None
    assert await db_session.get(Prestation, "p-aligne") is None
    assert await db_session.get(Project, "d-aligne") is None
    brouillon = await db_session.get(Invoice, "f-aligne")
    assert brouillon.client_name == "[ANONYMISÉ]" and brouillon.client_email is None
    activites = (await db_session.execute(select(Activity).where(Activity.contact_id == "c-aligne"))).scalars().all()
    assert all("Ménard" not in (a.title or "") for a in activites), [a.title for a in activites]
