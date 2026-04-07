"""
THERESE v2 - Tests Module Devis

Tests pour les fonctionnalites specifiques aux devis.
"""

from datetime import UTC, datetime

import pytest
from httpx import AsyncClient


async def _create_contact(client: AsyncClient) -> str:
    """Cree un contact de test et retourne son ID."""
    response = await client.post("/api/memory/contacts", json={
        "first_name": "Jean",
        "last_name": "Dupont",
        "company": "SARL Test",
        "email": "jean@test.fr",
    })
    assert response.status_code == 200, f"Echec creation contact: {response.text}"
    return response.json()["id"]


async def _create_devis(client: AsyncClient, contact_id: str, **kwargs) -> dict:
    """Cree un devis de test et retourne la reponse complete."""
    devis_data = {
        "contact_id": contact_id,
        "document_type": "devis",
        "lines": [
            {
                "description": "Prestation formation IA",
                "quantity": 1.0,
                "unit_price_ht": 2490.0,
                "tva_rate": 20.0,
            }
        ],
        "notes": "Devis de test",
    }
    devis_data.update(kwargs)
    response = await client.post("/api/invoices/", json=devis_data)
    assert response.status_code == 200, f"Echec creation devis: {response.text}"
    return response.json()


class TestDevisCreation:
    """Tests pour la creation de devis."""

    @pytest.mark.asyncio
    async def test_create_devis(self, client: AsyncClient):
        """POST /api/invoices/ avec document_type=devis cree un devis."""
        contact_id = await _create_contact(client)
        devis = await _create_devis(client, contact_id)

        assert devis["document_type"] == "devis"
        assert devis["status"] == "draft"

        current_year = datetime.now(UTC).year
        assert devis["invoice_number"].startswith(f"DEV-{current_year}-")

    @pytest.mark.asyncio
    async def test_devis_default_validite(self, client: AsyncClient):
        """Un devis sans validite_jours explicite recoit 30 jours par defaut."""
        contact_id = await _create_contact(client)
        devis = await _create_devis(client, contact_id)

        assert devis["validite_jours"] == 30

    @pytest.mark.asyncio
    async def test_devis_custom_validite(self, client: AsyncClient):
        """Un devis avec validite_jours explicite utilise la valeur fournie."""
        contact_id = await _create_contact(client)
        devis = await _create_devis(client, contact_id, validite_jours=60)

        assert devis["validite_jours"] == 60

    @pytest.mark.asyncio
    async def test_facture_no_validite(self, client: AsyncClient):
        """Une facture n'a pas de validite_jours."""
        contact_id = await _create_contact(client)
        response = await client.post("/api/invoices/", json={
            "contact_id": contact_id,
            "document_type": "facture",
            "lines": [{"description": "Test", "quantity": 1, "unit_price_ht": 100, "tva_rate": 20}],
        })
        assert response.status_code == 200
        invoice = response.json()
        assert invoice["validite_jours"] is None

    @pytest.mark.asyncio
    async def test_devis_number_format(self, client: AsyncClient):
        """Les numeros de devis suivent le format DEV-YYYY-NNN."""
        contact_id = await _create_contact(client)
        devis1 = await _create_devis(client, contact_id)
        devis2 = await _create_devis(client, contact_id)

        current_year = datetime.now(UTC).year
        assert devis1["invoice_number"] == f"DEV-{current_year}-001"
        assert devis2["invoice_number"] == f"DEV-{current_year}-002"


class TestDevisStatus:
    """Tests pour les statuts de devis."""

    @pytest.mark.asyncio
    async def test_accept_devis(self, client: AsyncClient):
        """PATCH /api/invoices/{id}/devis-status avec status=accepted accepte le devis."""
        contact_id = await _create_contact(client)
        devis = await _create_devis(client, contact_id)

        response = await client.patch(
            f"/api/invoices/{devis['id']}/devis-status",
            json={"status": "accepted"},
        )
        assert response.status_code == 200
        result = response.json()
        assert result["status"] == "accepted"

    @pytest.mark.asyncio
    async def test_refuse_devis(self, client: AsyncClient):
        """PATCH /api/invoices/{id}/devis-status avec status=refused refuse le devis."""
        contact_id = await _create_contact(client)
        devis = await _create_devis(client, contact_id)

        response = await client.patch(
            f"/api/invoices/{devis['id']}/devis-status",
            json={"status": "refused"},
        )
        assert response.status_code == 200
        result = response.json()
        assert result["status"] == "refused"

    @pytest.mark.asyncio
    async def test_expire_devis(self, client: AsyncClient):
        """PATCH /api/invoices/{id}/devis-status avec status=expired expire le devis."""
        contact_id = await _create_contact(client)
        devis = await _create_devis(client, contact_id)

        response = await client.patch(
            f"/api/invoices/{devis['id']}/devis-status",
            json={"status": "expired"},
        )
        assert response.status_code == 200
        result = response.json()
        assert result["status"] == "expired"

    @pytest.mark.asyncio
    async def test_invalid_devis_status(self, client: AsyncClient):
        """PATCH /api/invoices/{id}/devis-status avec un statut invalide retourne 400."""
        contact_id = await _create_contact(client)
        devis = await _create_devis(client, contact_id)

        response = await client.patch(
            f"/api/invoices/{devis['id']}/devis-status",
            json={"status": "paid"},
        )
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_devis_status_on_facture_fails(self, client: AsyncClient):
        """PATCH /api/invoices/{id}/devis-status sur une facture retourne 400."""
        contact_id = await _create_contact(client)

        response = await client.post("/api/invoices/", json={
            "contact_id": contact_id,
            "document_type": "facture",
            "lines": [{"description": "Test", "quantity": 1, "unit_price_ht": 100, "tva_rate": 20}],
        })
        invoice = response.json()

        response = await client.patch(
            f"/api/invoices/{invoice['id']}/devis-status",
            json={"status": "accepted"},
        )
        assert response.status_code == 400


class TestDevisConversion:
    """Tests pour la conversion devis -> facture."""

    @pytest.mark.asyncio
    async def test_convert_devis_to_facture(self, client: AsyncClient):
        """POST /api/invoices/{id}/convert-to-invoice convertit un devis en facture."""
        contact_id = await _create_contact(client)
        devis = await _create_devis(client, contact_id)

        response = await client.post(
            f"/api/invoices/{devis['id']}/convert-to-invoice",
            json={"payment_terms": "30 jours", "payment_method": "Virement bancaire"},
        )
        assert response.status_code == 200
        facture = response.json()

        assert facture["document_type"] == "facture"
        assert facture["converted_from_id"] == devis["id"]

        current_year = datetime.now(UTC).year
        assert facture["invoice_number"].startswith(f"FACT-{current_year}-")

        # Le devis source doit etre marque comme converti
        devis_response = await client.get(f"/api/invoices/{devis['id']}")
        assert devis_response.status_code == 200
        assert devis_response.json()["status"] == "converted"

    @pytest.mark.asyncio
    async def test_convert_cancelled_devis_fails(self, client: AsyncClient):
        """Impossible de convertir un devis annule."""
        contact_id = await _create_contact(client)
        devis = await _create_devis(client, contact_id)

        # Annuler le devis
        await client.patch(
            f"/api/invoices/{devis['id']}/devis-status",
            json={"status": "cancelled"},
        )

        # Tenter de convertir
        response = await client.post(
            f"/api/invoices/{devis['id']}/convert-to-invoice",
            json={},
        )
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_convert_already_converted_fails(self, client: AsyncClient):
        """Impossible de convertir un devis deja converti."""
        contact_id = await _create_contact(client)
        devis = await _create_devis(client, contact_id)

        # Convertir une premiere fois
        await client.post(
            f"/api/invoices/{devis['id']}/convert-to-invoice",
            json={},
        )

        # Tenter une deuxieme conversion
        response = await client.post(
            f"/api/invoices/{devis['id']}/convert-to-invoice",
            json={},
        )
        assert response.status_code == 400


class TestDevisFilter:
    """Tests pour le filtrage des devis."""

    @pytest.mark.asyncio
    async def test_filter_by_document_type(self, client: AsyncClient):
        """GET /api/invoices/?document_type=devis filtre les devis."""
        contact_id = await _create_contact(client)

        # Creer un devis et une facture
        await _create_devis(client, contact_id)
        await client.post("/api/invoices/", json={
            "contact_id": contact_id,
            "document_type": "facture",
            "lines": [{"description": "Test", "quantity": 1, "unit_price_ht": 100, "tva_rate": 20}],
        })

        # Filtrer les devis
        response = await client.get("/api/invoices/?document_type=devis")
        assert response.status_code == 200
        devis_list = response.json()
        assert all(d["document_type"] == "devis" for d in devis_list)
        assert len(devis_list) >= 1


class TestDevisValiditeUpdate:
    """Tests pour la mise a jour de la validite."""

    @pytest.mark.asyncio
    async def test_update_validite(self, client: AsyncClient):
        """PUT /api/invoices/{id} met a jour la validite_jours."""
        contact_id = await _create_contact(client)
        devis = await _create_devis(client, contact_id)

        response = await client.put(
            f"/api/invoices/{devis['id']}",
            json={"validite_jours": 90},
        )
        assert response.status_code == 200
        updated = response.json()
        assert updated["validite_jours"] == 90
