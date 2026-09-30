"""B-1671 : une facture émise ne passe plus à « Annulée » par un PUT.

Le § 210 du BOI-TVA-DECLA-30-20-20-20 rectifie une vente annulée par une
facture nouvelle ou par une note d'avoir, qui cite la facture initiale.
Basculer le statut sort la créance de l'encours sans aucun de ces documents.
Un devis, que ces textes ne visent pas, reste annulable.
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient


async def _contact(client: AsyncClient) -> str:
    reponse = await client.post(
        "/api/memory/contacts",
        json={"first_name": "Claire", "last_name": "Roux"},
    )
    assert reponse.status_code == 200, reponse.text
    return reponse.json()["id"]


async def _piece(client: AsyncClient, contact_id: str, document_type: str) -> dict:
    reponse = await client.post("/api/invoices/", json={
        "contact_id": contact_id,
        "document_type": document_type,
        "lines": [{"description": "Conseil", "quantity": 1, "unit_price_ht": 1200.0, "tva_rate": 20.0}],
    })
    assert reponse.status_code == 200, reponse.text
    return reponse.json()


@pytest.mark.asyncio
async def test_une_facture_emise_refuse_le_statut_annulee(client: AsyncClient):
    contact = await _contact(client)
    facture = await _piece(client, contact, "facture")
    emise = await client.put(f"/api/invoices/{facture['id']}", json={"status": "sent"})
    assert emise.status_code == 200, emise.text

    refus = await client.put(f"/api/invoices/{facture['id']}", json={"status": "cancelled"})
    assert refus.status_code == 409, refus.text
    assert "avoir" in refus.text

    relue = await client.get(f"/api/invoices/{facture['id']}")
    assert relue.json()["status"] == "sent"


@pytest.mark.asyncio
async def test_un_brouillon_de_facture_peut_passer_a_annulee(client: AsyncClient):
    contact = await _contact(client)
    facture = await _piece(client, contact, "facture")
    reponse = await client.put(f"/api/invoices/{facture['id']}", json={"status": "cancelled"})
    assert reponse.status_code == 200, reponse.text
    assert reponse.json()["status"] == "cancelled"


@pytest.mark.asyncio
async def test_un_avoir_emis_refuse_le_statut_annulee(client: AsyncClient):
    """L'article 289, I, 5 assimile l'avoir à une facture. Le passer à
    « Annulée » retirerait sa déduction de l'encours sans document nouveau."""
    contact = await _contact(client)
    facture = await _piece(client, contact, "facture")
    origine = await client.put(f"/api/invoices/{facture['id']}", json={"status": "sent"})
    assert origine.status_code == 200, origine.text
    avoir = await _piece(client, contact, "avoir")
    reference = await client.put(f"/api/invoices/{avoir['id']}", json={"converted_from_id": facture["id"]})
    assert reference.status_code == 200, reference.text
    emis = await client.put(f"/api/invoices/{avoir['id']}", json={"status": "sent"})
    assert emis.status_code == 200, emis.text
    assert emis.json()["invoice_number"].startswith("AV-")

    refus = await client.put(f"/api/invoices/{avoir['id']}", json={"status": "cancelled"})
    assert refus.status_code == 409, refus.text
    assert "expert-comptable" in refus.text

    relue = await client.get(f"/api/invoices/{avoir['id']}")
    assert relue.json()["status"] == "sent"


@pytest.mark.asyncio
async def test_un_brouillon_d_avoir_peut_passer_a_annulee(client: AsyncClient):
    contact = await _contact(client)
    avoir = await _piece(client, contact, "avoir")
    reponse = await client.put(f"/api/invoices/{avoir['id']}", json={"status": "cancelled"})
    assert reponse.status_code == 200, reponse.text
    assert reponse.json()["status"] == "cancelled"
    assert reponse.json()["invoice_number"].startswith("PROV-")


@pytest.mark.asyncio
async def test_un_devis_reste_annulable(client: AsyncClient):
    contact = await _contact(client)
    devis = await _piece(client, contact, "devis")
    envoye = await client.put(f"/api/invoices/{devis['id']}", json={"status": "sent"})
    assert envoye.status_code == 200, envoye.text

    annule = await client.put(f"/api/invoices/{devis['id']}", json={"status": "cancelled"})
    assert annule.status_code == 200, annule.text
    assert annule.json()["status"] == "cancelled"
