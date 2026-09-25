"""B-1315 : l'import de fichier CRM et la synchro tableur lisaient les statuts
de projet dans deux tables différentes ; « Livrée », « Terminée » ou « In
progress », reconnus par la synchro, étaient écartés à l'import de fichier.
Lecteur α, passe 6."""

import pytest
from app.models.entities import Project
from app.services.crm_import import CRMImportService
from sqlmodel import select


@pytest.mark.asyncio
async def test_l_import_de_fichier_lit_les_statuts_de_la_synchro(db_session):
    lignes = "id,name,status\np-1,Un,Livrée\np-2,Deux,Terminée\np-3,Trois,In progress\np-4,Quatre,pause\np-5,Cinq,En cours\n"
    res = await CRMImportService(db_session).import_projects(lignes.encode(), filename="p.csv")
    await db_session.commit()
    statuts = {p.id: p.status for p in (await db_session.execute(select(Project))).scalars().all()}
    assert statuts == {"p-1": "completed", "p-2": "completed", "p-3": "active", "p-4": "on_hold", "p-5": "active"}, statuts
    assert not res.errors, [e.message for e in res.errors]
