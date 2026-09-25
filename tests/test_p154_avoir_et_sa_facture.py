"""P-154 (recette P-146, lot 3 ; acceptée le 25/09) : un avoir imprimait les
conditions et pénalités d'une facture, sans rien qui le relie à la facture
qu'il corrige. L'avoir garde sa facture d'origine (converti depuis elle, ou
choisie à la création) et son PDF la cite, sans pénalités de retard."""

import pytest
from httpx import AsyncClient
from pypdf import PdfReader

LIGNES = [{"description": "Table en chêne", "quantity": 1, "unit_price_ht": 900.0, "tva_rate": 20.0}]


async def _piece(client: AsyncClient, type_: str, **extra) -> dict:
    contact = await client.post("/api/memory/contacts", json={"first_name": "Hélène", "last_name": "Ménard"})
    reponse = await client.post("/api/invoices/", json={
        "contact_id": contact.json()["id"], "document_type": type_, "lines": LIGNES, **extra,
    })
    return {**(reponse.json() if reponse.status_code < 300 else {"detail": reponse.text}), "http": reponse.status_code}


def _texte_du_pdf(chemin: str) -> str:
    return " ".join("".join(page.extract_text() for page in PdfReader(chemin).pages).split())


@pytest.mark.asyncio
async def test_un_avoir_converti_garde_sa_facture_et_la_cite(client: AsyncClient):
    profil = await client.post("/api/config/profile", json={
        "name": "Hélène Ménard", "company": "Atelier Ménard", "address": "Manosque", "siret": "99988877900009",
    })
    assert profil.status_code == 200, profil.text
    facture = await _piece(client, "facture")
    avoir = await client.post(f"/api/invoices/{facture['id']}/convert", json={"target_type": "avoir"})
    assert avoir.status_code == 200, avoir.text
    assert avoir.json()["converted_from_id"] == facture["id"]

    pdf = await client.get(f"/api/invoices/{avoir.json()['id']}/pdf")
    assert pdf.status_code == 200, pdf.text
    texte = _texte_du_pdf(pdf.json()["pdf_path"])
    assert f"Avoir sur la facture n° {facture['invoice_number']}" in texte
    assert "Indemnité forfaitaire" not in texte
    assert "retard" not in texte


@pytest.mark.asyncio
async def test_un_avoir_cree_choisit_sa_facture_d_origine(client: AsyncClient):
    facture = await _piece(client, "facture")
    avoir = await _piece(client, "avoir", converted_from_id=facture["id"])
    assert avoir["http"] in (200, 201), avoir
    assert avoir["converted_from_id"] == facture["id"]


@pytest.mark.asyncio
async def test_la_piece_d_origine_d_un_avoir_est_une_facture(client: AsyncClient):
    devis = await _piece(client, "devis")
    avoir = await _piece(client, "avoir", converted_from_id=devis["id"])
    assert avoir["http"] == 400, avoir
    inconnue = await _piece(client, "avoir", converted_from_id="facture-fantome")
    assert inconnue["http"] == 400, inconnue
