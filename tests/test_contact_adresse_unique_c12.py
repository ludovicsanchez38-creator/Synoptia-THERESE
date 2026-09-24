"""B-1074 (relecture du design P-096, constat n° 9, code actuel) : une fiche
contact peut porter DEUX adresses (« a@b.fr,pirate@x.fr » passe la validation
de création : un « @ », un point, aucune espace), la mise à jour ne vérifiait
aucune forme, et les imports ne testent que « @ ». Les chemins d'e-mail
joignent les destinataires par « , » : une réponse préparée depuis la fiche
viserait deux personnes. Une fiche porte une seule adresse.
"""

from __future__ import annotations

import pytest
from app.models.schemas import ContactCreate, ContactUpdate
from app.services.crm_import import _validate_contact
from app.services.import_service import parse_vcf
from pydantic import ValidationError

INVALIDES = ["a@b.fr,pirate@x.fr", "a@b.fr;pirate@x.fr", "Jean <a@b.fr>", "a@b.fr\nBcc: x@y.fr", "a@@b.fr", "a@b"]


@pytest.mark.parametrize("adresse", INVALIDES)
def test_la_creation_refuse_plus_d_une_adresse_ou_une_forme_douteuse(adresse: str):
    with pytest.raises(ValidationError):
        ContactCreate(first_name="Jeanne", email=adresse)


@pytest.mark.parametrize("adresse", INVALIDES)
def test_la_mise_a_jour_applique_la_meme_regle(adresse: str):
    with pytest.raises(ValidationError):
        ContactUpdate(email=adresse)


@pytest.mark.parametrize("adresse", ["jeanne.martin@exemple.fr", "j+tag@sous.domaine.fr"])
def test_une_adresse_ordinaire_passe(adresse: str):
    assert ContactCreate(first_name="Jeanne", email=adresse).email == adresse
    assert ContactUpdate(email=adresse).email == adresse


def test_la_mise_a_jour_peut_vider_l_adresse():
    assert ContactUpdate(email="").email == ""
    assert ContactUpdate(email=None).email is None


def test_l_import_tableur_n_ecarte_pas_la_fiche_pour_une_adresse_double():
    """B-1148 (audit de release 0.75) : l'adresse double n'est plus une erreur
    bloquante ; la fiche est importée sans l'adresse, comme par les autres portes."""
    assert _validate_contact({"first_name": "Jeanne", "email": "a@b.fr,pirate@x.fr"}) == []


@pytest.mark.asyncio
async def test_l_import_tableur_garde_la_fiche_sans_l_adresse_double(db_session):
    from app.models.entities import Contact
    from app.services.crm_import import CRMImportService
    from sqlmodel import select

    csv = "first_name,last_name,email\nJeanne,Martin,\"jean@a.fr, compta@a.fr\"\nPaul,Durand,paul@exemple.fr\n".encode()
    service = CRMImportService(db_session)
    apercu = await service.preview_contacts(csv, "contacts.csv")
    assert apercu.can_import, apercu.validation_errors
    resultat = await service.import_contacts(csv, "contacts.csv")
    await db_session.commit()
    assert resultat.created == 2, resultat
    assert resultat.skipped == 0
    assert any("une seule adresse" in e.message for e in resultat.errors), resultat.errors
    fiches = {c.first_name: c for c in (await db_session.execute(select(Contact))).scalars().all()}
    assert fiches["Jeanne"].email is None
    assert fiches["Paul"].email == "paul@exemple.fr"


@pytest.mark.asyncio
async def test_le_reimport_d_une_adresse_double_n_efface_pas_l_adresse_valide(db_session):
    from app.models.entities import Contact
    from app.services.crm_import import CRMImportService

    db_session.add(Contact(id="c-b1148", first_name="Jeanne", email="jeanne@exemple.fr", scope="global"))
    await db_session.commit()
    csv = "id,first_name,email\nc-b1148,Jeanne,\"jean@a.fr, compta@a.fr\"\n".encode()
    await CRMImportService(db_session).import_contacts(csv, "contacts.csv")
    await db_session.commit()
    fiche = await db_session.get(Contact, "c-b1148")
    await db_session.refresh(fiche)
    assert fiche.email == "jeanne@exemple.fr"


def test_l_import_vcard_ne_garde_pas_une_adresse_double():
    vcf = b"BEGIN:VCARD\r\nVERSION:3.0\r\nFN:Jeanne Martin\r\nN:Martin;Jeanne;;;\r\nEMAIL:a@b.fr,pirate@x.fr\r\nEND:VCARD\r\n"
    contacts = parse_vcf(vcf)
    # vobject ne rend que la première valeur : la fiche garde une adresse unique.
    assert contacts and contacts[0].get("email") in (None, "", "a@b.fr"), contacts


# ---------------------------------------------------------------------------
# B-1081 : trois portes d'écriture n'appliquaient pas encore la règle
# (lecteurs G1 et H2, dernière passe de la carte c12).
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("adresse", INVALIDES)
def test_la_creation_crm_refuse_plus_d_une_adresse(adresse: str):
    from app.models.schemas import CreateCRMContactRequest

    with pytest.raises(ValidationError):
        CreateCRMContactRequest(first_name="Jeanne", email=adresse)


def test_la_creation_crm_garde_une_adresse_ordinaire():
    from app.models.schemas import CreateCRMContactRequest

    assert CreateCRMContactRequest(first_name="Jeanne", email="jeanne@exemple.fr").email == "jeanne@exemple.fr"


@pytest.mark.asyncio
async def test_l_outil_du_chat_refuse_une_adresse_double(db_session):
    import json

    from app.models.entities import Contact
    from app.services.memory_tools import execute_create_contact
    from sqlmodel import select

    r = json.loads(await execute_create_contact({"first_name": "Jeanne", "email": "a@b.fr,pirate@x.fr"}, db_session))
    assert "error" in r, r
    assert (await db_session.execute(select(Contact))).scalars().all() == []


@pytest.mark.asyncio
async def test_la_synchro_tableur_ne_garde_pas_une_adresse_double(db_session):
    from app.services.crm_utils import upsert_contact

    contact, cree = await upsert_contact(db_session, {"ID": "crm-b1081", "Nom": "Jeanne Martin", "Email": "a@b.fr,pirate@x.fr"})
    assert cree
    assert contact.email is None


@pytest.mark.asyncio
async def test_la_synchro_tableur_n_efface_pas_une_adresse_valide(db_session):
    """B-1107 (lecteur I1) : régression de B-1081, une cellule mal formée
    effaçait l'adresse valide d'une fiche existante."""
    from app.services.crm_utils import upsert_contact

    await upsert_contact(db_session, {"ID": "crm-b1107", "Nom": "Jeanne Martin", "Email": "jeanne@exemple.fr"})
    await db_session.commit()
    contact, cree = await upsert_contact(db_session, {"ID": "crm-b1107", "Nom": "Jeanne Martin", "Email": "a@b.fr,pirate@x.fr"})
    assert not cree
    assert contact.email == "jeanne@exemple.fr"


@pytest.mark.asyncio
async def test_la_restauration_json_ne_garde_pas_une_adresse_double(client):
    """B-1119 (lecteur J1) : /api/data/import/contacts (restauration d'un
    export JSON) écrivait l'adresse telle quelle."""
    reponse = await client.post(
        "/api/data/import/contacts",
        json={"contacts": [
            {"id": "restau-b1119-a", "first_name": "Jeanne", "email": "a@b.fr,pirate@x.fr"},
            {"id": "restau-b1119-b", "first_name": "Paul", "email": "paul@exemple.fr"},
        ]},
    )
    assert reponse.status_code == 200, reponse.text[:200]
    assert reponse.json()["imported"] == 2
    fiches = {c["id"]: c for c in (await client.get("/api/memory/contacts")).json()}
    assert fiches["restau-b1119-a"]["email"] is None
    assert fiches["restau-b1119-b"]["email"] == "paul@exemple.fr"
