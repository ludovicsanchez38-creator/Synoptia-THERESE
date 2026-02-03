"""
THERESE v2 - Invoices Router Tests

Tests pour le CRUD de facturation (Phase 4).
"""

import pytest
from datetime import UTC, datetime
from httpx import AsyncClient


# ============================================================
# Helpers
# ============================================================


async def _create_contact(client: AsyncClient) -> str:
    """Cree un contact de test et retourne son ID."""
    response = await client.post("/api/memory/contacts", json={
        "first_name": "Marie",
        "last_name": "Martin",
        "company": "Entreprise Test",
        "email": "marie@test.fr",
        "phone": "+33612345678",
    })
    assert response.status_code == 200, f"Echec creation contact: {response.text}"
    return response.json()["id"]


async def _create_invoice(client: AsyncClient, contact_id: str, **kwargs) -> dict:
    """Cree une facture de test et retourne la reponse complete."""
    invoice_data = {
        "contact_id": contact_id,
        "lines": [
            {
                "description": "Prestation de conseil",
                "quantity": 2.0,
                "unit_price_ht": 500.0,
                "tva_rate": 20.0,
            }
        ],
        "notes": "Facture de test",
    }
    invoice_data.update(kwargs)

    response = await client.post("/api/invoices/", json=invoice_data)
    assert response.status_code == 200, f"Echec creation facture: {response.text}"
    return response.json()


# ============================================================
# Tests
# ============================================================


class TestInvoicesList:
    """Tests pour le listing des factures."""

    @pytest.mark.asyncio
    async def test_list_invoices_empty(self, client: AsyncClient):
        """GET /api/invoices/ retourne une liste vide quand aucune facture n'existe."""
        response = await client.get("/api/invoices/")

        assert response.status_code == 200
        invoices = response.json()

        assert isinstance(invoices, list)
        assert len(invoices) == 0

    @pytest.mark.asyncio
    async def test_list_invoices_filter_status(self, client: AsyncClient):
        """GET /api/invoices/?status=draft filtre par statut."""
        contact_id = await _create_contact(client)
        await _create_invoice(client, contact_id)

        # Toutes les nouvelles factures sont en draft
        response = await client.get("/api/invoices/?status=draft")

        assert response.status_code == 200
        invoices = response.json()
        assert len(invoices) >= 1
        assert all(inv["status"] == "draft" for inv in invoices)


class TestInvoicesCRUD:
    """Tests pour le CRUD complet des factures."""

    @pytest.mark.asyncio
    async def test_create_invoice(self, client: AsyncClient):
        """POST /api/invoices/ cree une facture avec contact et lignes."""
        contact_id = await _create_contact(client)

        response = await client.post("/api/invoices/", json={
            "contact_id": contact_id,
            "lines": [
                {
                    "description": "Formation IA",
                    "quantity": 1.0,
                    "unit_price_ht": 2490.0,
                    "tva_rate": 20.0,
                },
                {
                    "description": "Support technique",
                    "quantity": 3.0,
                    "unit_price_ht": 150.0,
                    "tva_rate": 20.0,
                },
            ],
            "notes": "Facture formation + support",
        })

        assert response.status_code == 200
        invoice = response.json()

        assert "id" in invoice
        assert invoice["contact_id"] == contact_id
        assert invoice["status"] == "draft"
        assert invoice["notes"] == "Facture formation + support"
        assert len(invoice["lines"]) == 2
        assert "invoice_number" in invoice
        assert "created_at" in invoice

    @pytest.mark.asyncio
    async def test_invoice_auto_number(self, client: AsyncClient):
        """Verifie que le numero de facture est au format FACT-YYYY-NNN."""
        contact_id = await _create_contact(client)
        invoice = await _create_invoice(client, contact_id)

        current_year = datetime.now(UTC).year
        assert invoice["invoice_number"].startswith(f"FACT-{current_year}-")
        # Le numero doit etre sur 3 chiffres
        number_part = invoice["invoice_number"].split("-")[-1]
        assert len(number_part) == 3
        assert number_part == "001"

        # Creer une deuxieme facture - doit incrementer
        invoice2 = await _create_invoice(client, contact_id)
        number_part2 = invoice2["invoice_number"].split("-")[-1]
        assert number_part2 == "002"

    @pytest.mark.asyncio
    async def test_invoice_line_calculation(self, client: AsyncClient):
        """Verifie le calcul des lignes: total_ht = qty * unit_price_ht, total_ttc inclut TVA."""
        contact_id = await _create_contact(client)

        invoice = await _create_invoice(client, contact_id, lines=[
            {
                "description": "Conseil strategie",
                "quantity": 5.0,
                "unit_price_ht": 200.0,
                "tva_rate": 20.0,
            }
        ])

        line = invoice["lines"][0]

        # total_ht = 5 * 200 = 1000
        assert line["total_ht"] == pytest.approx(1000.0)
        # total_ttc = 1000 * 1.20 = 1200
        assert line["total_ttc"] == pytest.approx(1200.0)

    @pytest.mark.asyncio
    async def test_invoice_totals(self, client: AsyncClient):
        """Verifie les totaux de la facture: subtotal_ht, total_tax, total_ttc."""
        contact_id = await _create_contact(client)

        invoice = await _create_invoice(client, contact_id, lines=[
            {
                "description": "Prestation A",
                "quantity": 2.0,
                "unit_price_ht": 500.0,
                "tva_rate": 20.0,
            },
            {
                "description": "Prestation B",
                "quantity": 1.0,
                "unit_price_ht": 1000.0,
                "tva_rate": 20.0,
            },
        ])

        # Ligne A: HT=1000, TTC=1200
        # Ligne B: HT=1000, TTC=1200
        # subtotal_ht = 2000, total_tax = 400, total_ttc = 2400
        assert invoice["subtotal_ht"] == pytest.approx(2000.0)
        assert invoice["total_tax"] == pytest.approx(400.0)
        assert invoice["total_ttc"] == pytest.approx(2400.0)

    @pytest.mark.asyncio
    async def test_get_invoice(self, client: AsyncClient):
        """GET /api/invoices/{id} recupere une facture specifique."""
        contact_id = await _create_contact(client)
        invoice = await _create_invoice(client, contact_id)

        response = await client.get(f"/api/invoices/{invoice['id']}")

        assert response.status_code == 200
        fetched = response.json()
        assert fetched["id"] == invoice["id"]
        assert fetched["invoice_number"] == invoice["invoice_number"]

    @pytest.mark.asyncio
    async def test_get_invoice_not_found(self, client: AsyncClient):
        """GET /api/invoices/{id} retourne 404 si la facture n'existe pas."""
        response = await client.get("/api/invoices/id-inexistant-12345")

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_invoice(self, client: AsyncClient):
        """PUT /api/invoices/{id} met a jour les notes d'une facture."""
        contact_id = await _create_contact(client)
        invoice = await _create_invoice(client, contact_id)

        response = await client.put(f"/api/invoices/{invoice['id']}", json={
            "notes": "Notes mises a jour",
        })

        assert response.status_code == 200
        updated = response.json()
        assert updated["notes"] == "Notes mises a jour"
        # Les autres champs restent inchanges
        assert updated["invoice_number"] == invoice["invoice_number"]

    @pytest.mark.asyncio
    async def test_mark_invoice_paid(self, client: AsyncClient):
        """PATCH /api/invoices/{id}/mark-paid marque une facture comme payee."""
        contact_id = await _create_contact(client)
        invoice = await _create_invoice(client, contact_id)

        response = await client.patch(
            f"/api/invoices/{invoice['id']}/mark-paid",
            json={"payment_date": "2026-02-01T12:00:00"},
        )

        assert response.status_code == 200
        paid = response.json()
        assert paid["status"] == "paid"
        assert paid["payment_date"] is not None

    @pytest.mark.asyncio
    async def test_mark_invoice_paid_default_date(self, client: AsyncClient):
        """PATCH /api/invoices/{id}/mark-paid utilise la date du jour si aucune date fournie."""
        contact_id = await _create_contact(client)
        invoice = await _create_invoice(client, contact_id)

        response = await client.patch(
            f"/api/invoices/{invoice['id']}/mark-paid",
            json={},
        )

        assert response.status_code == 200
        paid = response.json()
        assert paid["status"] == "paid"
        assert paid["payment_date"] is not None

    @pytest.mark.asyncio
    async def test_delete_invoice(self, client: AsyncClient):
        """DELETE /api/invoices/{id} supprime une facture."""
        contact_id = await _create_contact(client)
        invoice = await _create_invoice(client, contact_id)

        response = await client.delete(f"/api/invoices/{invoice['id']}")

        assert response.status_code == 200
        result = response.json()
        assert "deleted" in result["message"].lower() or "successfully" in result["message"].lower()

        # Verifier qu'elle n'existe plus
        get_response = await client.get(f"/api/invoices/{invoice['id']}")
        assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_create_invoice_invalid_contact(self, client: AsyncClient):
        """POST /api/invoices/ echoue si le contact_id n'existe pas."""
        response = await client.post("/api/invoices/", json={
            "contact_id": "contact-inexistant-12345",
            "lines": [
                {
                    "description": "Prestation test",
                    "quantity": 1.0,
                    "unit_price_ht": 100.0,
                    "tva_rate": 20.0,
                }
            ],
        })

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_invoice_tva_rate_variable(self, client: AsyncClient):
        """Verifie le calcul avec des taux de TVA differents (5.5% et 20%)."""
        contact_id = await _create_contact(client)

        invoice = await _create_invoice(client, contact_id, lines=[
            {
                "description": "Livre",
                "quantity": 10.0,
                "unit_price_ht": 20.0,
                "tva_rate": 5.5,
            },
            {
                "description": "Service conseil",
                "quantity": 1.0,
                "unit_price_ht": 1000.0,
                "tva_rate": 20.0,
            },
        ])

        # Ligne Livre: HT=200, TTC=200*1.055=211
        # Ligne Service: HT=1000, TTC=1000*1.20=1200
        assert invoice["subtotal_ht"] == pytest.approx(1200.0)
        assert invoice["total_ttc"] == pytest.approx(1411.0)
        assert invoice["total_tax"] == pytest.approx(211.0)
