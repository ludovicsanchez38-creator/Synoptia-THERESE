"""B-1382 (persona Nathalie, cycle 13) : le score d'un prospect importé
n'était pas calculé, puis sautait au premier déplacement.

Seul le formulaire (`memory.py`, `initial_creation`) et la création du CRM
calculaient le score ; les imports vCard (deux routes), l'import tableur et la
commande du chat créaient la fiche avec le défaut de 50. Élodie (e-mail,
téléphone, entreprise) affichait 50, puis 105 en changeant d'une colonne ; Paul
et Julien, mêmes champs et même étape, avaient 50 et 80. Toute fiche NEUVE
reçoit désormais le score de base calculé par la même règle.
"""

import csv
import io
import json

import pytest

EMAIL = "elodie.martin@example.test"


def _attendu(**champs) -> int:
    from app.models.entities import Contact
    from app.services.scoring import calculate_base_score

    return calculate_base_score(Contact(stage="contact", **champs))


async def _relire(client, email: str) -> dict:
    contacts = (await client.get("/api/memory/contacts?limit=200")).json()
    if isinstance(contacts, dict):
        contacts = contacts.get("contacts", contacts.get("items", []))
    return next(c for c in contacts if c.get("email") == email)


@pytest.mark.asyncio
@pytest.mark.parametrize("route", ["/api/crm/import/vcf", "/api/memory/contacts/import"])
async def test_une_fiche_importee_en_vcard_a_son_score(client, route):
    carte = (
        "BEGIN:VCARD\r\nVERSION:3.0\r\nN:Martin;Élodie;;;\r\nFN:Élodie Martin\r\n"
        f"ORG:Boulangerie Martin\r\nEMAIL:{EMAIL}\r\nTEL:06 00 00 00 02\r\nEND:VCARD\r\n"
    ).encode("utf-8")
    reponse = await client.post(route, files={"file": ("prospects.vcf", carte, "text/vcard")})
    assert reponse.status_code == 200, reponse.text

    fiche = await _relire(client, EMAIL)
    assert fiche["score"] == _attendu(email=EMAIL, phone="06 00 00 00 02", company="Boulangerie Martin")
    assert fiche["score"] != 50


@pytest.mark.asyncio
async def test_une_fiche_importee_du_tableur_sans_score_a_le_sien(client):
    tampon = io.StringIO()
    graveur = csv.writer(tampon, lineterminator="\r\n")
    graveur.writerow(["first_name", "last_name", "company", "email", "phone"])
    graveur.writerow(["Karim", "Benali", "Garage Benali", "karim@example.test", ""])
    reponse = await client.post(
        "/api/crm/import/contacts", files={"file": ("prospects.csv", tampon.getvalue().encode("utf-8"), "text/csv")},
    )
    assert reponse.status_code == 200, reponse.text

    fiche = await _relire(client, "karim@example.test")
    assert fiche["score"] == _attendu(email="karim@example.test", company="Garage Benali")


@pytest.mark.asyncio
async def test_un_score_fourni_par_le_tableur_est_garde(client):
    tampon = io.StringIO()
    graveur = csv.writer(tampon, lineterminator="\r\n")
    graveur.writerow(["first_name", "last_name", "email", "score"])
    graveur.writerow(["Julien", "Garnier", "julien@example.test", "80"])
    reponse = await client.post(
        "/api/crm/import/contacts", files={"file": ("prospects.csv", tampon.getvalue().encode("utf-8"), "text/csv")},
    )
    assert reponse.status_code == 200, reponse.text
    assert (await _relire(client, "julien@example.test"))["score"] == 80


@pytest.mark.asyncio
async def test_une_fiche_creee_par_le_chat_a_son_score(client):
    from app.models.database import get_session_context
    from app.services.memory_tools import execute_memory_tool

    async with get_session_context() as session:
        brut = await execute_memory_tool(
            "create_contact",
            {"first_name": "Paul", "last_name": "Exemple", "email": "paul@example.test", "company": "Orion"},
            session,
        )
    assert json.loads(brut)["success"] is True

    fiche = await _relire(client, "paul@example.test")
    assert fiche["score"] == _attendu(email="paul@example.test", company="Orion")
