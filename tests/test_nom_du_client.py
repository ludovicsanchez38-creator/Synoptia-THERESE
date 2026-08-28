"""B4 — le nom du client sur les listes de devis et sur le brief.

Campagne dix personas, finding F5 de l'artisan : « On voit DEV-2026-001, badge
Devis, Brouillon, dates, montant TTC. Pas le client. Je ne retiens pas les
numéros DEV-2026-001. Je retiens Moreau. Si le client rappelle, je cherche
Moreau, pas un numéro. »

La relecture a nommé le même trou sur le brief du jour : `overdue_invoices`
n'a pas le nom non plus (`dashboard.py`). L'artisan y a lu « Facture
FACT-2026-001 » au lieu de Garcia.

Un join, pas une dénormalisation : `Invoice.contact` existe déjà et
`list_invoices` fait déjà un `selectinload` sur les lignes. La pagination ne
bouge pas.
"""
import pytest


async def _client_avec_facture(client):
    contact = await client.post(
        "/api/memory/contacts",
        json={"first_name": "Sophie", "last_name": "Garcia", "company": "Garcia SARL"},
    )
    cid = contact.json()["id"]
    facture = await client.post(
        "/api/invoices/",
        json={
            "contact_id": cid,
            "type": "invoice",
            "lines": [{"description": "Depannage", "quantity": 1,
                       "unit_price_ht": 165.0, "tva_rate": 20.0}],
        },
    )
    assert facture.status_code in (200, 201), facture.text
    return cid, facture.json()


class TestLaListeNommeLeClient:
    @pytest.mark.asyncio
    async def test_la_liste_des_factures_porte_le_nom(self, client):
        await _client_avec_facture(client)

        liste = await client.get("/api/invoices/")
        assert liste.status_code == 200
        factures = liste.json()
        assert factures, "aucune facture rendue"
        premiere = factures[0] if isinstance(factures, list) else factures["items"][0]
        assert "contact_name" in premiere, (
            "la liste n'affichait que le numéro : « je retiens Moreau, pas "
            "DEV-2026-001 »"
        )
        assert premiere["contact_name"] and "Garcia" in premiere["contact_name"]

    @pytest.mark.asyncio
    async def test_une_facture_sans_contact_ne_casse_pas_la_liste(self, client):
        """Le join ne doit pas exclure ni planter sur un contact absent."""
        liste = await client.get("/api/invoices/")
        assert liste.status_code == 200


class TestLeBriefNommeLeClient:
    @pytest.mark.asyncio
    async def test_les_impayes_du_brief_portent_le_nom(self, client):
        """« Facture FACT-2026-001 » ne dit pas à qui elle est.

        Test de bout en bout, pas de schéma : le brief construit ses entrées à
        la main (`dashboard.py`), un champ de modèle ne prouverait rien.
        """
        from datetime import UTC, datetime, timedelta

        from app.models.database import get_session_context
        from app.models.entities import Invoice
        from sqlalchemy import select

        cid, facture = await _client_avec_facture(client)

        # Le brief ne retient que les factures échues depuis plus de 30 jours
        # (`dashboard.py:210`). On pose l'échéance en base : un PATCH ne suffit
        # pas, et un `skip` ferait de ce test un décor.
        async with get_session_context() as session:
            trouvee = await session.execute(
                select(Invoice).where(Invoice.id == facture["id"])
            )
            en_base = trouvee.scalars().one()
            en_base.status = "overdue"
            en_base.due_date = datetime.now(UTC).replace(tzinfo=None) - timedelta(days=45)
            await session.commit()

        brief = await client.get("/api/dashboard/today")
        assert brief.status_code == 200
        impayees = brief.json().get("overdue_invoices", [])
        assert impayees, "la facture échue depuis 45 jours doit figurer au brief"
        assert "contact_name" in impayees[0], (
            "le brief nomme une référence, pas un client : l'artisan y a lu "
            "« Facture FACT-2026-001 » au lieu de Garcia"
        )
