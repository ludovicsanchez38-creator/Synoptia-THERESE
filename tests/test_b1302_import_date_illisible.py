"""B-1302 : à l'import CRM en mise à jour, une date illisible écrivait None
par-dessus la date enregistrée, sans rien au rapport, y compris
`rgpd_date_expiration` (la date de purge RGPD d'une fiche). Une cellule vide
garde son sens de miroir. Lecteur X, passe 5."""

from datetime import datetime

import pytest
from app.models.entities import Contact
from app.services.crm_import import CRMImportService
from sqlmodel import select

EXPIRATION = datetime(2030, 1, 1)


async def _importer(db_session, cellule: str):
    db_session.add(Contact(id="c-d", first_name="Marie", last_name="Exemple", rgpd_date_expiration=EXPIRATION))
    await db_session.commit()
    res = await CRMImportService(db_session).import_contacts(
        f"id,first_name,last_name,rgpd_date_expiration\nc-d,Marie,Exemple,{cellule}\n".encode(), filename="c.csv"
    )
    await db_session.commit()
    db_session.expire_all()
    fiche = (await db_session.execute(select(Contact).where(Contact.id == "c-d"))).scalar_one()
    return res, fiche


@pytest.mark.asyncio
async def test_une_date_illisible_garde_l_ancienne_et_le_dit(db_session):
    res, fiche = await _importer(db_session, "pas une date")
    assert fiche.rgpd_date_expiration is not None and fiche.rgpd_date_expiration.year == 2030, fiche.rgpd_date_expiration
    assert any(e.column == "rgpd_date_expiration" for e in res.errors), [e.message for e in res.errors]


@pytest.mark.asyncio
async def test_une_cellule_vide_efface_toujours(db_session):
    res, fiche = await _importer(db_session, "")
    assert fiche.rgpd_date_expiration is None, fiche.rgpd_date_expiration
    assert not res.errors, [e.message for e in res.errors]


@pytest.mark.asyncio
async def test_l_echeance_illisible_d_un_livrable_garde_l_ancienne(db_session):
    from app.models.entities import Deliverable, Project

    db_session.add(Project(id="p-d", name="Chantier", status="active"))
    db_session.add(Deliverable(id="l-d", project_id="p-d", title="Maquette", due_date=EXPIRATION))
    await db_session.commit()
    res = await CRMImportService(db_session).import_deliverables(
        b"id,project_id,title,due_date\nl-d,p-d,Maquette,pas une date\n", filename="l.csv"
    )
    await db_session.commit()
    db_session.expire_all()
    livrable = (await db_session.execute(select(Deliverable).where(Deliverable.id == "l-d"))).scalar_one()
    assert livrable.due_date is not None and livrable.due_date.year == 2030, livrable.due_date
    assert any(e.column == "due_date" for e in res.errors), [e.message for e in res.errors]
