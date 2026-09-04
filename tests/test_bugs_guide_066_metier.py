"""Régressions métier relevées dans le guide 0.66."""

from datetime import UTC, datetime, time, timedelta

import pytest
from app.models.entities import Activity, Contact, Invoice
from app.services.action_agents import (
    _gather_local_context,
    get_agent_definitions,
    reload_agent_definitions,
)
from app.services.civil_time import date_civile_paris
from app.services.invoice_status import statut_effectif_facture


def _facture(
    contact: Contact,
    *,
    identifiant: str,
    numero: str,
    echeance: datetime,
    statut: str = "sent",
    type_document: str = "facture",
) -> Invoice:
    return Invoice(
        id=identifiant,
        invoice_number=numero,
        contact_id=contact.id,
        client_name=contact.display_name,
        document_type=type_document,
        issue_date=echeance - timedelta(days=30),
        due_date=echeance,
        status=statut,
        total_ttc=1200.0,
        currency="EUR",
    )


class TestB315FacturesEchues:
    def test_une_facture_envoyee_devient_en_retard_le_lendemain(self):
        aujourd_hui = date_civile_paris()

        assert statut_effectif_facture(
            "sent",
            "facture",
            datetime.combine(aujourd_hui - timedelta(days=1), time.min),
            aujourd_hui=aujourd_hui,
        ) == "overdue"
        assert statut_effectif_facture(
            "sent",
            "facture",
            datetime.combine(aujourd_hui, time.min),
            aujourd_hui=aujourd_hui,
        ) == "sent"
        assert statut_effectif_facture(
            "sent",
            "devis",
            datetime.combine(aujourd_hui - timedelta(days=1), time.min),
            aujourd_hui=aujourd_hui,
        ) == "sent"

    @pytest.mark.asyncio
    async def test_liste_et_brief_incluent_une_facture_echue_depuis_neuf_jours(
        self, client, db_session
    ):
        aujourd_hui = date_civile_paris()
        contact = Contact(id="ct-b315", first_name="Camille", last_name="Martin")
        facture = _facture(
            contact,
            identifiant="inv-b315",
            numero="FACT-2026-315",
            echeance=datetime.combine(aujourd_hui - timedelta(days=9), time.min),
        )
        db_session.add_all([contact, facture])
        await db_session.commit()

        liste = await client.get("/api/invoices/?status=overdue")
        brief = await client.get("/api/dashboard/today")

        assert liste.status_code == 200
        assert [(piece["id"], piece["status"]) for piece in liste.json()] == [
            (facture.id, "overdue")
        ]
        assert facture.id in {
            piece["id"] for piece in brief.json()["overdue_invoices"]
        }

    @pytest.mark.asyncio
    async def test_facture_due_aujourdhui_reste_envoyee(self, client, db_session):
        aujourd_hui = date_civile_paris()
        contact = Contact(id="ct-b315-today", first_name="Nora")
        facture = _facture(
            contact,
            identifiant="inv-b315-today",
            numero="FACT-2026-316",
            echeance=datetime.combine(aujourd_hui, time.min),
        )
        db_session.add_all([contact, facture])
        await db_session.commit()

        en_retard = await client.get("/api/invoices/?status=overdue")
        envoyees = await client.get("/api/invoices/?status=sent")

        assert facture.id not in {piece["id"] for piece in en_retard.json()}
        assert facture.id in {piece["id"] for piece in envoyees.json()}


class TestB322RelanceClients:
    @pytest.mark.asyncio
    async def test_contexte_associe_pipeline_activite_et_piece_au_contact(self, db_session):
        maintenant = datetime.now(UTC).replace(tzinfo=None)
        contact = Contact(
            id="ct-b322",
            first_name="Sophie",
            last_name="Garcia",
            company="Garcia SARL",
            stage="proposition",
            last_interaction=maintenant - timedelta(days=8),
            next_follow_up=maintenant - timedelta(days=1),
        )
        activite = Activity(
            id="act-b322",
            contact_id=contact.id,
            type="email",
            title="Devis transmis",
            created_at=maintenant - timedelta(days=8),
        )
        facture = _facture(
            contact,
            identifiant="inv-b322",
            numero="DEV-2026-322",
            echeance=maintenant + timedelta(days=5),
            type_document="devis",
        )
        db_session.add_all([contact, activite, facture])
        await db_session.commit()

        reload_agent_definitions()
        assert "invoices" in get_agent_definitions()["relance-clients"].tools

        contexte = await _gather_local_context(["crm", "invoices"])

        assert "Sophie Garcia (Garcia SARL)" in contexte
        assert "étape : proposition" in contexte
        assert "Devis transmis" in contexte
        assert "devis DEV-2026-322" in contexte
        assert "1200.0 EUR" in contexte
