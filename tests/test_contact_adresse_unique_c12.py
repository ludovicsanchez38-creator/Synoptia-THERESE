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


def test_l_import_tableur_refuse_deux_adresses():
    assert "Email invalide" in _validate_contact({"first_name": "Jeanne", "email": "a@b.fr,pirate@x.fr"})


def test_l_import_vcard_ne_garde_pas_une_adresse_double():
    vcf = b"BEGIN:VCARD\r\nVERSION:3.0\r\nFN:Jeanne Martin\r\nN:Martin;Jeanne;;;\r\nEMAIL:a@b.fr,pirate@x.fr\r\nEND:VCARD\r\n"
    contacts = parse_vcf(vcf)
    # vobject ne rend que la première valeur : la fiche garde une adresse unique.
    assert contacts and contacts[0].get("email") in (None, "", "a@b.fr"), contacts
