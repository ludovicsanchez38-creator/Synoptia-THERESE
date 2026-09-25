"""P-155 (recette P-146, lot 3) : la date du paiement se saisit. La route
l'acceptait déjà ; elle refuse désormais une date future, qui ferait passer
une facture pour payée avant de l'être (tableau de bord, relances)."""

from datetime import date, timedelta

import pytest
from httpx import AsyncClient


async def _facture(client: AsyncClient) -> str:
    contact = await client.post("/api/memory/contacts", json={"first_name": "Hélène", "last_name": "Ménard"})
    facture = await client.post("/api/invoices/", json={
        "contact_id": contact.json()["id"], "document_type": "facture",
        "lines": [{"description": "Table en chêne", "quantity": 1, "unit_price_ht": 900.0, "tva_rate": 20.0}],
    })
    assert facture.status_code in (200, 201), facture.text
    return facture.json()["id"]


@pytest.mark.asyncio
async def test_la_date_reelle_du_paiement_est_gardee(client: AsyncClient):
    identifiant = await _facture(client)
    reponse = await client.patch(f"/api/invoices/{identifiant}/mark-paid", json={"payment_date": "2026-07-20"})
    assert reponse.status_code == 200, reponse.text
    assert reponse.json()["payment_date"].startswith("2026-07-20")


@pytest.mark.asyncio
async def test_une_date_future_est_refusee(client: AsyncClient):
    identifiant = await _facture(client)
    demain = (date.today() + timedelta(days=2)).isoformat()
    reponse = await client.patch(f"/api/invoices/{identifiant}/mark-paid", json={"payment_date": demain})
    assert reponse.status_code == 400, reponse.text
    relue = await client.get(f"/api/invoices/{identifiant}")
    assert relue.json()["status"] != "paid"
