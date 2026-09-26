"""B-1685 (lecteur de carte c13r-1) : anonymiser une personne dont un dossier
a un dossier local synchronisé.

`anonymiser_la_personne` écrit d'abord l'identité effacée, puis supprime les
dossiers comme la route de suppression, qui détache la racine synchronisée
par `retirer_racine`, sur sa propre session. Aucune anonymisation de test ne
posait de dossier synchronisé : le chemin n'était jamais exercé.
"""

import pytest


@pytest.mark.asyncio
async def test_l_anonymisation_detache_le_dossier_synchronise(client, tmp_path):
    from app.models import database as db_module
    from app.models.entities_sync import ProjectSyncRoot
    from sqlmodel import select

    contact = (await client.post("/api/memory/contacts", json={"first_name": "Hélène", "last_name": "Ménard"})).json()
    projet = (await client.post("/api/memory/projects", json={"name": "Cuisine Ménard", "contact_id": contact["id"]})).json()
    async with db_module.AsyncSessionLocal() as session:
        session.add(ProjectSyncRoot(project_id=projet["id"], racine=str(tmp_path / "Cuisine"), volume_id=1))
        await session.commit()

    reponse = await client.post(f"/api/rgpd/anonymize/{contact['id']}", json={"reason": "Demande"})

    assert reponse.status_code == 200, reponse.text
    async with db_module.AsyncSessionLocal() as session:
        racine = (await session.execute(
            select(ProjectSyncRoot).where(ProjectSyncRoot.project_id == projet["id"])
        )).scalar_one_or_none()
    assert racine is None or racine.detachee, "la racine du dossier supprimé est restée rattachée"


@pytest.mark.asyncio
async def test_la_purge_automatique_detache_le_dossier_synchronise(client, tmp_path):
    from datetime import UTC, datetime, timedelta
    from unittest.mock import AsyncMock, patch

    from app.models import database as db_module
    from app.models.entities import Contact, Notification, Preference
    from app.models.entities_sync import ProjectSyncRoot
    from app.services import rgpd_auto
    from sqlmodel import select

    projet = (await client.post("/api/memory/projects", json={"name": "Cuisine Ménard"})).json()
    maintenant = datetime.now(UTC)
    async with db_module.AsyncSessionLocal() as session:
        session.add(Preference(key="rgpd_purge_enabled", value="true"))
        session.add(Contact(id="c-synchro", first_name="Hélène", last_name="Ménard",
                            last_interaction=maintenant - timedelta(days=4 * 365)))
        # Une seconde fiche à prévenir : la campagne écrit avant d'anonymiser.
        session.add(Contact(id="c-a-prevenir", first_name="Karim", last_name="Benali",
                            last_interaction=maintenant - timedelta(days=4 * 365)))
        session.add(Notification(title="Purge RGPD programmée", message="préavis", type="warning",
                                 source="rgpd_purge", action_url="/crm/contacts/c-synchro",
                                 created_at=maintenant - timedelta(days=40)))
        session.add(ProjectSyncRoot(project_id=projet["id"], racine=str(tmp_path / "Cuisine"), volume_id=1))
        await session.commit()
    await client.patch(f"/api/memory/projects/{projet['id']}", json={"contact_id": "c-synchro"})

    with patch.object(rgpd_auto, "purge_contact_vector", new=AsyncMock(return_value=1)):
        resultat = await rgpd_auto.auto_purge_expired_contacts()

    assert resultat["anonymisations"] == 1, resultat
    async with db_module.AsyncSessionLocal() as session:
        racine = (await session.execute(
            select(ProjectSyncRoot).where(ProjectSyncRoot.project_id == projet["id"])
        )).scalar_one_or_none()
    assert racine is None or racine.detachee
