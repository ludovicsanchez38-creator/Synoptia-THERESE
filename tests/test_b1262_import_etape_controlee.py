"""B-1262 : l'import de fichier CRM écrivait l'étape telle quelle. Une étape
hors du pipeline rendait la fiche invisible des colonnes ; le tableur, lui, ne
retient qu'une étape connue (B-1187). Lecteur U, passe 4."""

import pytest
from app.models.entities import Contact
from app.services.crm_import import CRMImportService
from sqlmodel import select


async def _importer(db_session, lignes: str):
    res = await CRMImportService(db_session).import_contacts(
        ("id,first_name,last_name,stage\n" + lignes).encode(), filename="c.csv"
    )
    await db_session.commit()
    db_session.expire_all()
    return res


async def _etape(db_session, cid: str) -> str:
    return (await db_session.execute(select(Contact).where(Contact.id == cid))).scalar_one().stage


@pytest.mark.asyncio
async def test_une_etape_inconnue_ne_remplace_pas_l_existante(db_session):
    db_session.add(Contact(id="c-1", first_name="Marie", last_name="Exemple", stage="proposition"))
    await db_session.commit()
    res = await _importer(db_session, "c-1,Marie,Exemple,gelé\n")
    assert await _etape(db_session, "c-1") == "proposition"
    assert any(e.column == "stage" for e in res.errors), [e.message for e in res.errors]


@pytest.mark.asyncio
async def test_une_fiche_creee_avec_une_etape_inconnue_prend_le_defaut(db_session):
    res = await _importer(db_session, "c-2,Jean,Exemple,gelé\n")
    assert await _etape(db_session, "c-2") == "contact"
    assert any(e.column == "stage" for e in res.errors), [e.message for e in res.errors]


@pytest.mark.asyncio
async def test_une_etape_connue_passe_quelle_que_soit_la_casse(db_session):
    res = await _importer(db_session, "c-3,Léa,Exemple,Proposition\n")
    assert await _etape(db_session, "c-3") == "proposition"
    assert not res.errors, [e.message for e in res.errors]
