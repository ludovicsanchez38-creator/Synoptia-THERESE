"""B-1418 (vérification du moteur pendant P-130, cycle 13) : un tableur aux
en-têtes français naturels (« Étape », « Téléphone », « PRÉNOM ») perdait
ces colonnes en silence ; seules les formes exactes des alias (« etape »,
« Etape ») étaient reconnues. Les en-têtes se comparent désormais sans
accents ni casse."""

import pytest
from app.services.crm_import import CRMImportService
from sqlmodel import select

CSV = (
    "PRÉNOM,Nom,Téléphone,Étape\n"
    "Nadia,Roux,06 11 22 33 44,discovery\n"
).encode("utf-8")


@pytest.mark.asyncio
async def test_l_apercu_reconnait_les_en_tetes_accentues(db_session):
    apercu = await CRMImportService(db_session).preview_contacts(CSV, filename="prospects.csv")
    assert apercu.column_mapping == {
        "PRÉNOM": "first_name", "Nom": "last_name", "Téléphone": "phone", "Étape": "stage",
    }


@pytest.mark.asyncio
async def test_l_import_garde_l_etape_et_le_telephone(db_session):
    from app.models.entities import Contact

    resultat = await CRMImportService(db_session).import_contacts(CSV, filename="prospects.csv")
    assert resultat.created == 1, resultat.message
    nadia = (await db_session.execute(select(Contact).where(Contact.last_name == "Roux"))).scalar_one()
    assert (nadia.first_name, nadia.phone, nadia.stage) == ("Nadia", "06 11 22 33 44", "discovery")
