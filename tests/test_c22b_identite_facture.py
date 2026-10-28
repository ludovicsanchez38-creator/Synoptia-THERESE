"""Identité et dates des factures directes, sans changer pénalités ni escompte."""

from unittest.mock import AsyncMock

import pytest
from app.routers import invoices
from app.services.user_profile import UserProfile
from pypdf import PdfReader


@pytest.mark.asyncio
async def test_facture_directe_adresses_mentions_et_date(client, monkeypatch, tmp_path):
    profil = UserProfile.from_dict(
        {
            "name": "Camille Exemple",
            "company": "Atelier Exemple",
            "siret": "12345678900010",
            "address": "10 rue du Siège, 75001 Paris",
            "legal_form": "SAS",
            "share_capital": "1000",
            "billing_address": "20 rue Comptable, 75002 Paris",
        }
    )
    monkeypatch.setattr(invoices, "get_cached_profile", lambda: profil)
    monkeypatch.setattr(invoices, "_get_invoice_output_dir", AsyncMock(return_value=str(tmp_path)))
    contact = (
        await client.post(
            "/api/memory/contacts", json={"first_name": "Alice", "last_name": "Client"}
        )
    ).json()
    cree = await client.post(
        "/api/invoices/",
        json={
            "contact_id": contact["id"],
            "issue_date": "2026-10-28",
            "lines": [
                {"description": "Prestation", "quantity": 1, "unit_price_ht": 100, "tva_rate": 20}
            ],
        },
    )
    assert cree.status_code == 200, cree.text
    assert cree.json()["service_date"] is None  # aucune date de prestation inventée
    identifiant = cree.json()["id"]
    refus = await client.get(f"/api/invoices/{identifiant}/pdf")
    assert refus.status_code == 400
    assert "adresse du client" in refus.text
    modifie = await client.put(
        f"/api/invoices/{identifiant}",
        json={
            "client_address": "3 rue du Client, 69001 Lyon",
            "client_billing_address": "4 rue de Facturation, 69002 Lyon",
            "service_date": "2026-10-20",
            "purchase_order": "BC <42>",
        },
    )
    assert modifie.status_code == 200, modifie.text
    relu = (await client.get(f"/api/invoices/{identifiant}")).json()
    assert relu["service_date"].startswith("2026-10-20")
    assert relu["client_billing_address"] == "4 rue de Facturation, 69002 Lyon"
    pdf = await client.get(f"/api/invoices/{identifiant}/pdf")
    assert pdf.status_code == 200, pdf.text
    texte = "\n".join(page.extract_text() for page in PdfReader(pdf.json()["pdf_path"]).pages)
    for attendu in [
        "SAS",
        "Capital social",
        "1 000",
        "20 rue Comptable",
        "3 rue du Client",
        "4 rue de Facturation",
        "20/10/2026",
        "BC <42>",
        "Escompte pour paiement anticipé",
        "refinancement",
    ]:
        assert attendu in texte
    emis = await client.put(f"/api/invoices/{identifiant}", json={"status": "sent"})
    assert emis.status_code == 200, emis.text
    for champ in ("client_address", "client_billing_address", "service_date", "purchase_order"):
        interdit = await client.put(f"/api/invoices/{identifiant}", json={champ: None})
        assert interdit.status_code == 409, interdit.text
    avoir = await client.post(f"/api/invoices/{identifiant}/convert", json={"target_type": "avoir"})
    assert avoir.status_code == 200, avoir.text
    assert avoir.json()["client_billing_address"] == relu["client_billing_address"]
    assert avoir.json()["service_date"] == relu["service_date"]
    assert avoir.json()["purchase_order"] == "BC <42>"


def test_identite_ei_et_capital_de_societe(tmp_path):
    from app.services.invoice_pdf import InvoicePDFGenerator

    from tests.test_invoice_pdf_francais import donnees_facture

    ei = UserProfile.from_dict(
        {
            "name": "Camille Exemple",
            "company": "Nom commercial",
            "siret": "12345678900010",
            "address": "Paris",
            "legal_form": "EI",
        }
    )
    assert ei.missing_invoice_identity_fields() == []
    sas = UserProfile.from_dict({**ei.to_dict(), "legal_form": "SAS"})
    assert "capital social" in sas.missing_invoice_identity_fields()
    sas.share_capital = "1e999999"
    assert "capital social" in sas.missing_invoice_identity_fields()
    chemin = InvoicePDFGenerator(output_dir=str(tmp_path)).generate_invoice_pdf(
        donnees_facture(),
        {"name": "Client", "address": "Lyon"},
        ei.to_dict(),
    )
    texte = "\n".join(page.extract_text() for page in PdfReader(chemin).pages)
    assert "Camille Exemple EI" in texte


@pytest.mark.asyncio
async def test_champs_identite_passent_par_le_profil(client):
    sauvegarde = await client.post(
        "/api/config/profile",
        json={
            "name": "Camille Exemple",
            "company": "Exemple",
            "legal_form": "SARL",
            "share_capital": "2500",
            "billing_address": "Adresse de facturation",
        },
    )
    assert sauvegarde.status_code == 200, sauvegarde.text
    relu = (await client.get("/api/config/profile")).json()
    assert relu["legal_form"] == "SARL"
    assert relu["share_capital"] == "2500"
    assert relu["billing_address"] == "Adresse de facturation"


@pytest.mark.asyncio
async def test_piece_deja_emise_sans_adresse_ne_propose_pas_de_modifier_le_brouillon(
    client, monkeypatch
):
    profil = UserProfile(
        name="Camille Exemple", address="Paris", siret="12345678900010", legal_form="EI"
    )
    monkeypatch.setattr(invoices, "get_cached_profile", lambda: profil)
    contact = (await client.post("/api/memory/contacts", json={"first_name": "Alice"})).json()
    piece = await client.post(
        "/api/invoices/",
        json={
            "contact_id": contact["id"],
            "lines": [
                {"description": "Prestation", "quantity": 1, "unit_price_ht": 100, "tva_rate": 20}
            ],
        },
    )
    identifiant = piece.json()["id"]
    emise = await client.put(f"/api/invoices/{identifiant}", json={"status": "sent"})
    assert emise.status_code == 200, emise.text
    reponse = await client.get(f"/api/invoices/{identifiant}/pdf")
    assert reponse.status_code == 400
    assert "déjà émise" in reponse.text
    assert "PDF d’origine" in reponse.text
    assert "dans le brouillon" not in reponse.text
