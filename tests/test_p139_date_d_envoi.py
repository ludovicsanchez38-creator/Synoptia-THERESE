"""P-139 (acceptée le 25/09) : garder la date d'envoi d'un devis ou d'une
facture. L'écran ne pouvait dire ni si ni quand une pièce était partie
(B-1388) : « Envoyée le » reprenait la date d'émission, et une facture payée
disait « Envoi non tracé » (B-1449). La date est posée au premier passage à
« envoyé », jamais réécrite ensuite."""

import pytest
from httpx import AsyncClient


async def _piece(client: AsyncClient, type_: str) -> str:
    contact = await client.post("/api/memory/contacts", json={"first_name": "Hélène", "last_name": "Ménard"})
    piece = await client.post("/api/invoices/", json={
        "contact_id": contact.json()["id"], "document_type": type_,
        "lines": [{"description": "Table en chêne", "quantity": 1, "unit_price_ht": 900.0, "tva_rate": 20.0}],
    })
    assert piece.status_code in (200, 201), piece.text
    assert piece.json().get("sent_at") is None
    return piece.json()["id"]


@pytest.mark.asyncio
async def test_une_facture_envoyee_garde_sa_date_d_envoi(client: AsyncClient):
    identifiant = await _piece(client, "facture")
    envoyee = await client.put(f"/api/invoices/{identifiant}", json={"status": "sent"})
    assert envoyee.status_code == 200, envoyee.text
    date_envoi = envoyee.json()["sent_at"]
    assert date_envoi

    # Payée ensuite : la date d'envoi reste, elle n'est jamais réécrite.
    payee = await client.patch(f"/api/invoices/{identifiant}/mark-paid", json={"payment_date": "2026-07-20"})
    assert payee.json()["sent_at"] == date_envoi
    revue = await client.put(f"/api/invoices/{identifiant}", json={"status": "sent"})
    assert revue.json()["sent_at"] == date_envoi


@pytest.mark.asyncio
async def test_un_devis_envoye_garde_sa_date_d_envoi(client: AsyncClient):
    identifiant = await _piece(client, "devis")
    reponse = await client.patch(f"/api/invoices/{identifiant}/devis-status", json={"status": "sent"})
    if reponse.status_code == 404 or reponse.status_code == 405:
        pytest.fail(f"route du statut de devis introuvable : {reponse.status_code}")
    assert reponse.status_code == 200, reponse.text
    assert reponse.json()["sent_at"]
