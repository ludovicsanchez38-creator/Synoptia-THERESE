"""B-1307 : à l'import CRM de projets, un statut inconnu était ignoré sans rien
au rapport (garder le statut existant, ou « active » à la création, est voulu :
B-1083). Lecteur Y, passe 5."""

import pytest
from app.models.entities import Project
from app.services.crm_import import CRMImportService
from sqlmodel import select


@pytest.mark.asyncio
async def test_un_statut_inconnu_est_signale(db_session):
    db_session.add(Project(id="p-s", name="Chantier", status="completed"))
    await db_session.commit()
    res = await CRMImportService(db_session).import_projects(
        "id,name,status\np-s,Chantier,gelé\np-n,Nouveau,gelé\n".encode(), filename="p.csv"
    )
    await db_session.commit()
    db_session.expire_all()
    statuts = {p.id: p.status for p in (await db_session.execute(select(Project))).scalars().all()}
    assert statuts == {"p-s": "completed", "p-n": "active"}, statuts
    assert sum(1 for e in res.errors if e.column == "status") == 2, [e.message for e in res.errors]
