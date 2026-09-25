"""B-1256 : à l'import de fichier, une cellule de budget non vide mais illisible
(« inf », « NaN », « beaucoup ») écrivait None par-dessus le budget existant,
sans erreur au rapport. Le tableur, lui, ne remplace rien. Revue du diff,
passe 4 (cas E). Le budget négatif relève de B-1244 (règle à trancher)."""

import pytest
from app.models.entities import Project
from app.services.crm_import import CRMImportService
from sqlmodel import select


async def _importer(db_session, cellule: str):
    db_session.add(Project(id="p-e", name="Chantier", budget=1200.0, status="active"))
    await db_session.commit()
    res = await CRMImportService(db_session).import_projects(
        f"id,name,budget\np-e,Chantier,{cellule}\n".encode(), filename="p.csv"
    )
    await db_session.commit()
    db_session.expire_all()
    projet = (await db_session.execute(select(Project).where(Project.id == "p-e"))).scalar_one()
    return res, projet


@pytest.mark.asyncio
@pytest.mark.parametrize("cellule", ["inf", "NaN", "beaucoup"])
async def test_un_budget_illisible_garde_l_ancien_et_le_dit(db_session, cellule):
    res, projet = await _importer(db_session, cellule)
    assert projet.budget == 1200.0, projet.budget
    assert any(e.column == "budget" for e in res.errors), [e.message for e in res.errors]


@pytest.mark.asyncio
async def test_un_budget_lisible_remplace_toujours(db_session):
    res, projet = await _importer(db_session, "1500")
    assert projet.budget == 1500.0, projet.budget
    assert not res.errors, [e.message for e in res.errors]
