"""B-1320, B-1321 : jumeaux côté livrables de B-1315 et B-1313.

- B-1320 : l'import de fichier avait sa propre table de statuts de livrables ;
  « À faire », « En révision » ou « pending », acceptés par la synchro
  tableur, étaient refusés.
- B-1321 : un livrable créé avec une échéance illisible était enregistré sans
  échéance, sans rien au rapport.
Lecteur γ, passe 7."""

import pytest
from app.models.entities import Deliverable, Project
from app.services.crm_import import CRMImportService
from sqlmodel import select


@pytest.mark.asyncio
async def test_l_import_lit_les_statuts_de_livrables_de_la_synchro(db_session):
    db_session.add(Project(id="p-l", name="Chantier", status="active"))
    await db_session.commit()
    lignes = "id,project_id,title,status\nl-1,p-l,Un,À faire\nl-2,p-l,Deux,En révision\nl-3,p-l,Trois,pending\n"
    res = await CRMImportService(db_session).import_deliverables(lignes.encode(), filename="l.csv")
    await db_session.commit()
    statuts = {d.id: d.status for d in (await db_session.execute(select(Deliverable))).scalars().all()}
    assert statuts == {"l-1": "a_faire", "l-2": "en_revision", "l-3": "a_faire"}, statuts
    assert not res.errors, [e.message for e in res.errors]


@pytest.mark.asyncio
async def test_une_echeance_illisible_a_la_creation_se_dit(db_session):
    db_session.add(Project(id="p-m", name="Chantier", status="active"))
    await db_session.commit()
    res = await CRMImportService(db_session).import_deliverables(
        b"id,project_id,title,due_date\nl-9,p-m,Maquette,pas une date\n", filename="l.csv"
    )
    assert res.created == 1, res
    assert any(e.column == "due_date" for e in res.errors), [e.message for e in res.errors]
