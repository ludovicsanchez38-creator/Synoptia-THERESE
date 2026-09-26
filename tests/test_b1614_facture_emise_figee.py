"""B-1614 (suite de B-1506) : une facture émise se modifiait encore par PUT
(lignes, totaux, client, dates, notes). Sa numérotation et son contenu
appartiennent à la séquence chronologique continue (BOFiP,
BOI-TVA-DECLA-30-20-20-10, vérifié pour B-1506) : on la corrige par un avoir.
Seul son statut change encore (payée, en retard, annulée), jamais vers le
brouillon.
"""

import pytest
from httpx import AsyncClient


async def _facture_envoyee(client: AsyncClient) -> str:
    contact = await client.post("/api/memory/contacts", json={"first_name": "Hélène", "last_name": "Ménard"})
    piece = await client.post("/api/invoices/", json={
        "contact_id": contact.json()["id"], "document_type": "facture",
        "lines": [{"description": "Table en chêne", "quantity": 1, "unit_price_ht": 900.0, "tva_rate": 20.0}],
    })
    identifiant = piece.json()["id"]
    assert (await client.put(f"/api/invoices/{identifiant}", json={"status": "sent"})).status_code == 200
    return identifiant


@pytest.mark.asyncio
async def test_les_lignes_d_une_facture_emise_ne_changent_plus(client: AsyncClient):
    identifiant = await _facture_envoyee(client)
    reponse = await client.put(f"/api/invoices/{identifiant}", json={
        "lines": [{"description": "Table en chêne", "quantity": 2, "unit_price_ht": 900.0, "tva_rate": 20.0}],
    })
    assert reponse.status_code == 409, reponse.text
    assert "avoir" in reponse.text
    assert (await client.get(f"/api/invoices/{identifiant}")).json()["total_ttc"] == 1080.0


@pytest.mark.asyncio
async def test_les_notes_et_la_date_d_une_facture_emise_ne_changent_plus(client: AsyncClient):
    identifiant = await _facture_envoyee(client)
    assert (await client.put(f"/api/invoices/{identifiant}", json={"notes": "réécrite"})).status_code == 409
    assert (await client.put(f"/api/invoices/{identifiant}", json={"issue_date": "2026-01-01"})).status_code == 409


@pytest.mark.asyncio
async def test_le_statut_d_une_facture_emise_change_encore(client: AsyncClient):
    identifiant = await _facture_envoyee(client)
    reponse = await client.put(f"/api/invoices/{identifiant}", json={"status": "paid"})
    assert reponse.status_code == 200, reponse.text
    assert reponse.json()["status"] == "paid"
