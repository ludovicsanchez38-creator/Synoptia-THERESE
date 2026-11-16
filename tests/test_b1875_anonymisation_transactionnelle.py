"""B-1875 : une anonymisation annulée conserve aussi la synchronisation SQL."""

from datetime import UTC, datetime, timedelta
from unittest.mock import patch

import pytest
from app.models import database
from app.models.entities import Activity, Contact, Notification, Preference, Project
from app.models.entities_sync import EtatPlan, ProjectSyncEntry, ProjectSyncRoot, SyncPlan
from app.services import rgpd_auto, rgpd_identite
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
@pytest.mark.parametrize("chemin", ["manuel", "automatique"])
@pytest.mark.parametrize("echec", ["identite", "commit"])
async def test_un_echec_annule_aussi_le_detachement(client, tmp_path, chemin, echec):
    maintenant = datetime.now(UTC)
    async with database.AsyncSessionLocal() as session:
        session.add(Contact(
            id="c-b1875", first_name="Hélène", email="helene@example.test",
            last_interaction=maintenant - timedelta(days=4 * 365),
        ))
        session.add(Project(id="p-b1875", name="Dossier jetable", contact_id="c-b1875"))
        session.add(ProjectSyncRoot(
            id="r-b1875", project_id="p-b1875", racine=str(tmp_path), volume_id=1,
        ))
        session.add(SyncPlan(id="plan-b1875", project_id="p-b1875", generation_racine=1))
        session.add(ProjectSyncEntry(
            id="entree-b1875", project_id="p-b1875", chemin=str(tmp_path / "note.txt"),
            file_id="f-b1875", taille=5, mtime_ns=1, sha256="empreinte", generation_racine=1,
        ))
        session.add(Preference(key="rgpd_purge_enabled", value="true"))
        session.add(Notification(
            title="Purge RGPD programmée", message="Préavis", type="warning",
            source="rgpd_purge", action_url="/crm/contacts/c-b1875",
            created_at=maintenant - timedelta(days=40),
        ))
        await session.commit()

    commit_reel = AsyncSession.commit

    async def commit_defaillant(session: AsyncSession) -> None:
        if any(isinstance(objet, Activity) for objet in session.new):
            raise RuntimeError("Échec simulé de l'anonymisation")
        await commit_reel(session)

    panne = (
        patch.object(rgpd_identite, "effacer_l_identite", side_effect=RuntimeError("Échec simulé de l'anonymisation"))
        if echec == "identite"
        else patch.object(AsyncSession, "commit", new=commit_defaillant)
    )
    with panne:
        if chemin == "manuel":
            reponse = await client.post("/api/rgpd/anonymize/c-b1875", json={"reason": "Demande"})
            assert reponse.status_code == 500
        else:
            resultat = await rgpd_auto.auto_purge_expired_contacts()
            assert resultat == {"notifications": 0, "anonymisations": 0}

    # Une nouvelle session relit ce qui a réellement été conservé sur disque.
    async with database.AsyncSessionLocal() as session:
        contact = await session.get(Contact, "c-b1875")
        assert contact.first_name == "Hélène"
        assert contact.email == "helene@example.test"
        assert await session.get(Project, "p-b1875") is not None
        racine = await session.get(ProjectSyncRoot, "r-b1875")
        assert racine.detachee is False, "l'anonymisation annulée a détaché la racine"
        assert racine.generation == 1
        assert (await session.get(SyncPlan, "plan-b1875")).etat == EtatPlan.PROPOSE
        assert await session.get(ProjectSyncEntry, "entree-b1875") is not None
