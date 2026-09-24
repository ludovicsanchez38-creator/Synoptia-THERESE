"""B-1087, B-1121 (cycle 12, réparés au cycle 13) : une cellule vide ne fait
plus échouer tout un import de contacts.

Au réimport, une cellule vide d'étape ou de périmètre, ou une date de
création ou de modification vide ou illisible, écrivait None sur une colonne
NOT NULL ; le commit unique faisait alors échouer tout l'import, fiches
saines comprises. Règle (comme la synchro, B-1108) : une valeur vide ou
illisible ne remplace pas la valeur enregistrée. Le périmètre suit aussi la
règle de B-1165 (« Global » devient « global », une valeur inconnue ne
remplace rien).
"""

from datetime import datetime

import pytest
from app.models.entities import Contact
from app.services.crm_import import CRMImportService
from sqlmodel import select

ENTETE = "id,first_name,last_name,stage,scope,created_at,updated_at\n"


async def _existant(session) -> datetime:
    cree = datetime(2025, 3, 1, 9, 0)
    session.add(Contact(id="reimport-b1087", first_name="Léa", last_name="Martin", stage="client", scope="global", created_at=cree, updated_at=cree))
    session.add(Contact(id="reimport-sain", first_name="Paul", last_name="Durand"))
    await session.commit()
    return cree


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "ligne",
    [
        "reimport-b1087,Léa,Martin,,,,\n",
        "reimport-b1087,Léa,Martin,client,global,pas une date,jamais\n",
        "reimport-b1087,Léa,Martin,client,partout,,\n",
    ],
)
async def test_une_cellule_vide_ou_illisible_ne_fait_pas_echouer_l_import(db_session, ligne):
    cree = await _existant(db_session)
    contenu = (ENTETE + ligne + "reimport-sain,Paul,Durand-Bis,,,,\n").encode("utf-8")

    resultat = await CRMImportService(db_session).import_contacts(contenu, "contacts.csv")
    await db_session.commit()

    assert resultat.updated == 2, resultat
    db_session.expire_all()
    lea = await db_session.get(Contact, "reimport-b1087")
    assert (lea.stage, lea.scope) == ("client", "global")
    assert lea.created_at.replace(tzinfo=None) == cree
    assert lea.updated_at is not None
    paul = await db_session.get(Contact, "reimport-sain")
    assert paul.last_name == "Durand-Bis"


@pytest.mark.asyncio
async def test_un_perimetre_en_majuscules_est_normalise(db_session):
    await _existant(db_session)
    contenu = (ENTETE + "reimport-b1087,Léa,Martin,client,Global,,\n").encode("utf-8")
    await CRMImportService(db_session).import_contacts(contenu, "contacts.csv")
    await db_session.commit()
    db_session.expire_all()
    assert (await db_session.get(Contact, "reimport-b1087")).scope == "global"


@pytest.mark.asyncio
async def test_une_fiche_neuve_sans_etape_ni_perimetre_prend_les_defauts(db_session):
    contenu = (ENTETE + "neuve-b1087,Nina,Roux,,,,\n").encode("utf-8")
    resultat = await CRMImportService(db_session).import_contacts(contenu, "contacts.csv")
    await db_session.commit()
    assert resultat.created == 1, resultat
    nina = (await db_session.execute(select(Contact).where(Contact.first_name == "Nina"))).scalar_one()
    assert (nina.stage, nina.scope) == ("contact", "global")
