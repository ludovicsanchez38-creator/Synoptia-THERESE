"""Dix entrées ajoutées après le retour au vert de P160 (contre-relecture)."""

from datetime import UTC, datetime

import pytest
from app.models import database as db
from app.models.entities import Invoice
from tests.test_b1164_emission_paris import creer, figer


@pytest.mark.asyncio
@pytest.mark.parametrize("numero,maximum,type_document,operation,attendu", [
    ("FACT-2027-014", 15, "facture", "sent", "FACT-2027-016"),
    ("FACT-2027-025", 24, "avoir", "mark-paid", "FACT-2027-025"),
    ("FACT-2027-25", 25, "facture", "mark-paid", "FACT-2027-026"),
    ("FACT-2027-00025", 25, "avoir", "sent", "FACT-2027-026"),
    ("AV-2027-019", 33, "avoir", "sent", "FACT-2027-034"),
    ("IMPORT-2027-031", 35, "facture", "sent", "FACT-2027-036"),
    ("FACT-2026-980", 10, "avoir", "mark-paid", "FACT-2027-011"),
    ("FACT-2028-001", 13, "facture", "sent", "FACT-2027-014"),
    ("FACT-2027-000", 11, "avoir", "sent", "FACT-2027-012"),
    ("FACT-2027-999", 1000, "facture", "mark-paid", "FACT-2027-1001"),
])
async def test_dix_heritages_a_minuit_paris(client, monkeypatch, numero, maximum, type_document, operation, attendu):
    piece = await creer(client)
    async with db.AsyncSessionLocal() as session:
        historique = Invoice(
            invoice_number=f"FACT-2027-{maximum:03d}", contact_id=piece["contact_id"],
            document_type="facture", status="sent", issue_date=datetime(2027, 1, 1),
            due_date=datetime(2027, 1, 31), sent_at=datetime(2026, 12, 31, 23, tzinfo=UTC),
        )
        session.add(historique)
        brouillon = await session.get(Invoice, piece["id"])
        brouillon.invoice_number = numero
        brouillon.document_type = type_document
        if type_document == "avoir":
            brouillon.converted_from_id = historique.id
        await session.commit()
        historique_id = historique.id
    avant = (await client.get(f"/api/invoices/{historique_id}")).json()
    figer(monkeypatch, datetime(2026, 12, 31, 23, 30, tzinfo=UTC))
    chemin = f"/api/invoices/{piece['id']}"
    notes = await client.put(chemin, json={"notes": "Avant première émission"})
    assert notes.status_code == 200, notes.text
    assert notes.json()["invoice_number"] == numero
    if operation == "mark-paid":
        response = await client.patch(chemin + "/mark-paid", json={})
    else:
        response = await client.put(chemin, json={"status": "sent"})
    assert response.status_code == 200, response.text
    relue = (await client.get(chemin)).json()
    assert relue["invoice_number"] == attendu
    assert relue["issue_date"][:10] == "2027-01-01"
    assert (await client.get(f"/api/invoices/{historique_id}")).json() == avant
