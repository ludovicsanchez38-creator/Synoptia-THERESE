"""B-1445 (recette P-146, lot 3) : P-119 imprimait la bonne mention quand on
appelait le générateur directement, mais la route du PDF recopiait le profil
par une liste blanche qui oubliait `regime_tva` : la franchise déclarée à
l'écran sortait « Aucune TVA facturée ». Le test passe désormais par les
routes, du profil au PDF, comme l'utilisatrice."""

import pytest
from httpx import AsyncClient
from pypdf import PdfReader

FRANCHISE = "TVA non applicable, art. 293 B du code général des impôts"
FORMATION = "Exonération de TVA, art. 261, 4, 4° a du code général des impôts"


async def _pdf_d_une_facture_a_zero(client: AsyncClient, regime: str) -> str:
    profil = await client.post("/api/config/profile", json={
        "name": "Claire Exemple", "company": "Claire Exemple Coaching", "address": "Lyon",
        "siret": "99988877900009", "regime_tva": regime,
    })
    assert profil.status_code == 200, profil.text
    contact = await client.post("/api/memory/contacts", json={"first_name": "Hélène", "last_name": "Ménard"})
    facture = await client.post("/api/invoices/", json={
        "contact_id": contact.json()["id"], "document_type": "facture",
        "lines": [{"description": "Séance de coaching", "quantity": 1, "unit_price_ht": 100.0, "tva_rate": 0.0}],
    })
    assert facture.status_code in (200, 201), facture.text
    reponse = await client.get(f"/api/invoices/{facture.json()['id']}/pdf")
    assert reponse.status_code == 200, reponse.text
    chemin = reponse.json()["pdf_path"]
    return " ".join("".join(page.extract_text() for page in PdfReader(chemin).pages).split())


@pytest.mark.asyncio
async def test_la_franchise_declaree_a_l_ecran_s_imprime(client: AsyncClient):
    assert FRANCHISE in await _pdf_d_une_facture_a_zero(client, "franchise")


@pytest.mark.asyncio
async def test_l_exoneration_formation_declaree_a_l_ecran_s_imprime(client: AsyncClient):
    assert FORMATION in await _pdf_d_une_facture_a_zero(client, "exoneration_formation")
