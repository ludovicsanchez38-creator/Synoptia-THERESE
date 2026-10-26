"""B-1149 : Excel Windows-1252 doit garder ses caractères à l'import CRM."""

import pytest
from app.models.entities import Contact
from app.services.crm_import import CRMImportService, _parse_csv
from sqlmodel import select

EXCEL = "Prénom;Nom;Entreprise;Notes\nAnaïs;Cœur;L’Atelier;Budget 240 € « validé »\n"
LATIN1 = "Prénom;Nom;Entreprise;Notes\nAndré;Noël;Façade & Associés;Pièce à 75 £ « réglée »\n"


@pytest.mark.parametrize("encodage,texte", [
    ("cp1252", EXCEL),
    ("utf-8", EXCEL),
    ("utf-8-sig", EXCEL),
    ("latin-1", LATIN1),
    ("latin-1", "Notes\nAvant\x81après\n"),
])
def test_le_decodage_preserve_les_cellules(encodage, texte):
    entete, ligne = texte.splitlines()
    assert _parse_csv(texte.encode(encodage)) == [dict(zip(entete.split(";"), ligne.split(";"), strict=True))]


@pytest.mark.asyncio
@pytest.mark.parametrize("encodage,texte", [
    ("cp1252", EXCEL),
    ("utf-8", EXCEL),
    ("utf-8-sig", EXCEL),
    ("latin-1", LATIN1),
])
async def test_l_apercu_et_la_fiche_stockee_gardent_le_texte(db_session, encodage, texte):
    await _verifier_import(db_session, encodage, texte)


async def _verifier_import(db_session, encodage, texte):
    contenu = texte.encode(encodage)
    attendu = dict(zip(
        ("first_name", "last_name", "company", "notes"), texte.splitlines()[1].split(";"), strict=True,
    ))
    service = CRMImportService(db_session)
    apercu = await service.preview_contacts(contenu, filename="excel.csv")
    assert apercu.can_import
    assert apercu.sample_rows == [attendu]

    resultat = await service.import_contacts(contenu, filename="excel.csv")
    assert resultat.created == 1, resultat.message
    assert not resultat.errors
    contact = (await db_session.execute(select(Contact))).scalar_one()
    assert {champ: getattr(contact, champ) for champ in attendu} == attendu


@pytest.mark.asyncio
@pytest.mark.parametrize("encodage,ligne", [
    ("cp1252", "Zoé;Œillet;L’Îlot;Conseil 91 € « prêt »"),
    ("cp1252", "Maëlle;Bœuf;D’Art;Offre “été” 37 €"),
    ("cp1252", "Héloïse;Lecœur;L’Escalier;Tarif 0,5 €"),
    ("utf-8", "Élise;André;Atelier 🧵;Pièce cœur 128 €"),
    ("utf-8", "Søren;Müller;Studio « Nord »;Trait d’union"),
    ("utf-8-sig", "Aïcha;Noël;L’Œuvre;Échéance 42 €"),
    ("utf-8-sig", "Renée;Faure;Maison 🍀;Cœur « artisan »"),
    ("latin-1", "Jérôme;François;Café du Port;Dépôt à 64 £"),
    ("latin-1", "Béatrice;Legrand;Façades réunies;Séance d'été"),
    ("latin-1", "Inès;García;Hôtel des Prés;Prévu « août »"),
])
async def test_dix_entrees_inventees_apres_correction(db_session, encodage, ligne):
    await _verifier_import(db_session, encodage, f"Prénom;Nom;Entreprise;Notes\n{ligne}\n")
