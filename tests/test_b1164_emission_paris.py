"""B-1164 : jour d'émission parisien, avec la règle P160 à la première émission."""

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from app.models import database as db
from app.models.entities import Invoice
from app.routers import invoices
from pypdf import PdfReader


def figer(monkeypatch, instant):
    class Horloge(datetime):
        @classmethod
        def now(cls, tz=None):
            return instant.astimezone(tz) if tz else instant.replace(tzinfo=None)

    monkeypatch.setattr(invoices, "datetime", Horloge)


async def creer(client, type_document="facture"):
    profil = await client.post("/api/config/profile", json={
        "name": "Atelier fictif", "company": "Paris", "address": "Paris",
        "siret": "99988877900009", "legal_form": "EI",
    })
    assert profil.status_code == 200, profil.text
    contact = await client.post("/api/memory/contacts", json={"first_name": "Paris", "last_name": "Émission", "address": "3 rue du Client, Lyon"})
    response = await client.post("/api/invoices/", json={
        "contact_id": contact.json()["id"], "document_type": type_document,
        "issue_date": "2026-10-01", "due_date": "2026-10-31",
        "lines": [{"description": "Prestation nocturne", "quantity": 1, "unit_price_ht": 10, "tva_rate": 20}],
    })
    assert response.status_code == 200, response.text
    return response.json()


@pytest.mark.asyncio
@pytest.mark.parametrize("instant,jour", [
    ("2026-12-31T23:30:00+00:00", "2027-01-01"),
    ("2026-07-15T22:30:00+00:00", "2026-07-16"),
])
@pytest.mark.parametrize("operation", ["sent", "paid", "mark-paid", "convert", "convert-to-invoice", "avoir"])
async def test_emission_civile_par_les_routes_et_pdf(client, monkeypatch, instant, jour, operation):
    piece = await creer(client, "devis" if operation.startswith("convert") else "facture")
    figer(monkeypatch, datetime.fromisoformat(instant))
    if operation.startswith("convert"):
        conversion = await client.post(f"/api/invoices/{piece['id']}/{operation}", json={
            "target_type": "facture", "payment_terms": "30 jours",
        })
        assert conversion.status_code == 200, conversion.text
        piece = conversion.json()
        assert piece["issue_date"][:10] == jour
    if operation == "avoir":
        origine = await client.put(f"/api/invoices/{piece['id']}", json={"status": "sent"})
        assert origine.status_code == 200, origine.text
        conversion = await client.post(f"/api/invoices/{piece['id']}/convert", json={"target_type": "avoir"})
        assert conversion.status_code == 200, conversion.text
        piece = conversion.json()
    chemin = f"/api/invoices/{piece['id']}"
    if operation == "mark-paid":
        response = await client.patch(chemin + "/mark-paid", json={})
    else:
        response = await client.put(chemin, json={"status": "paid" if operation == "paid" else "sent"})
    assert response.status_code == 200, response.text
    relue = (await client.get(chemin)).json()
    assert relue["invoice_number"].startswith(f"FACT-{jour[:4]}-")
    assert relue["issue_date"][:10] == jour
    assert relue["due_date"][:10] == (datetime.fromisoformat(jour) + timedelta(days=30)).date().isoformat()
    pdf = await client.get(chemin + "/pdf")
    assert pdf.status_code == 200, pdf.text
    texte = " ".join(page.extract_text() for page in PdfReader(Path(pdf.json()["pdf_path"])).pages)
    assert datetime.fromisoformat(jour).strftime("%d/%m/%Y") in texte


@pytest.mark.asyncio
@pytest.mark.parametrize("statut,numero,attendu", [
    ("draft", "FACT-2026-007", "FACT-2027-001"),
    ("draft", "FACT-2027-007", "FACT-2027-007"),
    ("sent", "FACT-2026-007", "FACT-2026-007"),
    ("paid", "FACT-2026-007", "FACT-2026-007"),
])
async def test_numero_herite_suit_p160_a_minuit_paris(client, monkeypatch, statut, numero, attendu):
    piece = await creer(client)
    async with db.AsyncSessionLocal() as session:
        stockee = await session.get(Invoice, piece["id"])
        stockee.invoice_number = numero
        stockee.status = statut
        await session.commit()
    figer(monkeypatch, datetime(2026, 12, 31, 23, 30, tzinfo=UTC))
    response = await client.put(f"/api/invoices/{piece['id']}", json={"status": "sent"})
    assert response.status_code == 200, response.text
    assert response.json()["invoice_number"] == attendu


@pytest.mark.asyncio
@pytest.mark.parametrize("instant,jour,type_document", [
    ("2026-12-31T22:59:59+00:00", "2026-12-31", "facture"),
    ("2026-12-31T23:00:00+00:00", "2027-01-01", "devis"),
    ("2027-01-31T23:15:00+00:00", "2027-02-01", "facture"),
    ("2028-02-28T23:45:00+00:00", "2028-02-29", "devis"),
    ("2026-03-29T00:30:00+00:00", "2026-03-29", "facture"),
    ("2026-03-29T22:01:00+00:00", "2026-03-30", "devis"),
    ("2026-06-30T21:59:59+00:00", "2026-06-30", "facture"),
    ("2026-06-30T22:00:00+00:00", "2026-07-01", "devis"),
    ("2026-10-25T00:30:00+00:00", "2026-10-25", "facture"),
    ("2026-10-25T23:30:00+00:00", "2026-10-26", "devis"),
])
async def test_dix_entrees_apres_correctif(client, monkeypatch, instant, jour, type_document):
    figer(monkeypatch, datetime.fromisoformat(instant))
    piece = await creer(client, type_document)
    chemin = f"/api/invoices/{piece['id']}"
    if type_document == "facture":
        response = await client.patch(chemin + "/mark-paid", json={})
        assert response.status_code == 200, response.text
        piece = response.json()
        assert piece["issue_date"][:10] == jour
    prefixe = "DEV" if type_document == "devis" else "FACT"
    assert piece["invoice_number"] == f"{prefixe}-{jour[:4]}-001"
    if type_document == "devis":
        # La date explicitement saisie reste celle du devis, même la nuit.
        assert piece["issue_date"][:10] == "2026-10-01"
