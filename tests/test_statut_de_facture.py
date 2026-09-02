"""
Un statut de DEVIS ne se pose pas sur une FACTURE.

Requalifiée par la revue de plan, et elle avait raison de me reprendre : je
rangeais ce défaut avec les scories de formulaire. Il SABOTE l'encours.

`UpdateInvoiceRequest.status` est une chaîne libre. Un `PUT` qui pose
« accepted » sur une facture de 1 200 EUR la fait sortir de `invoice_totals`,
qui ne regarde que `sent` et `overdue`. Le testeur croit enregistrer un
accord ; il efface une créance. C'est le mensonge de la première passe de
`invoice_totals`, déclenché par un menu, sans passer par le chat.

La route dédiée `PATCH /{id}/devis-status` est, elle, déjà protégée
(`if document_type != "devis"` -> 400). C'est la porte GÉNÉRIQUE qui manquait.
"""

import json

import pytest


async def _facture(client, montant: float) -> str:
    contact = await client.post(
        "/api/memory/contacts", json={"first_name": "Client", "last_name": "Statut"}
    )
    piece = await client.post(
        "/api/invoices/",
        json={
            "contact_id": contact.json()["id"],
            "document_type": "facture",
            "lines": [{"description": "Prestation", "quantity": 1,
                       "unit_price_ht": montant, "tva_rate": 0.0}],
        },
    )
    identifiant = piece.json()["id"]
    from app.models.database import get_session_context
    from app.models.entities import Invoice
    from sqlalchemy import select

    async with get_session_context() as session:
        trouvee = await session.execute(select(Invoice).where(Invoice.id == identifiant))
        trouvee.scalars().one().status = "sent"
        await session.commit()
    return identifiant


class TestUnStatutDeDevisNeSePosePasSurUneFacture:
    @pytest.mark.asyncio
    async def test_accepted_est_refuse_sur_une_facture(self, client):
        identifiant = await _facture(client, 1200.0)

        reponse = await client.put(
            f"/api/invoices/{identifiant}", json={"status": "accepted"}
        )

        assert reponse.status_code == 400, (
            "« Accepté » est un statut de devis : le poser sur une facture la "
            f"sort de l'encours sans que personne ne l'ait voulu (reçu {reponse.status_code})"
        )

    @pytest.mark.asyncio
    async def test_la_creance_reste_dans_l_encours(self, client):
        """La démonstration de ce que le défaut coûte, en euros."""
        from app.models.database import get_session_context
        from app.services.workspace_tools import execute_workspace_tool

        identifiant = await _facture(client, 1200.0)
        await client.put(f"/api/invoices/{identifiant}", json={"status": "accepted"})

        async with get_session_context() as session:
            resultat = json.loads(await execute_workspace_tool("invoice_totals", {}, session))

        assert resultat["encours_ttc"] == 1200.0, (
            "une créance de 1 200 EUR a disparu de l'encours par un clic de menu : "
            f"rendu {resultat['encours_ttc']!r}"
        )

    @pytest.mark.asyncio
    async def test_un_statut_de_facture_passe_toujours(self, client):
        """La garde vise les statuts de devis, pas la route."""
        identifiant = await _facture(client, 500.0)

        reponse = await client.put(
            f"/api/invoices/{identifiant}", json={"status": "overdue"}
        )

        assert reponse.status_code == 200, reponse.text

    @pytest.mark.asyncio
    async def test_un_devis_garde_ses_statuts(self, client):
        contact = await client.post(
            "/api/memory/contacts", json={"first_name": "Client", "last_name": "Devis"}
        )
        devis = await client.post(
            "/api/invoices/",
            json={
                "contact_id": contact.json()["id"],
                "document_type": "devis",
                "lines": [{"description": "Prestation", "quantity": 1,
                           "unit_price_ht": 900.0, "tva_rate": 0.0}],
            },
        )
        reponse = await client.put(
            f"/api/invoices/{devis.json()['id']}", json={"status": "accepted"}
        )
        assert reponse.status_code == 200, reponse.text

    @pytest.mark.asyncio
    async def test_un_statut_inventé_est_refusé(self, client):
        """`status` était une chaîne LIBRE : n'importe quoi passait."""
        identifiant = await _facture(client, 300.0)

        reponse = await client.put(
            f"/api/invoices/{identifiant}", json={"status": "en attente"}
        )
        assert reponse.status_code == 400, (
            "un statut inventé se retrouve en base et sort la pièce de tous les "
            "filtres - c'est ce que THÉRÈSE a elle-même halluciné en 0.53"
        )


class TestUnDevisNeSeMarquePasPaye:
    """B-162 (02/09/2026) : la porte generique `PUT` etait fermee en 0.55, la
    porte laterale `PATCH /{id}/mark-paid` ne l'a jamais ete.

    `paid` n'appartient pas a STATUTS_DE_DEVIS - un devis s'accepte ou se
    refuse, il ne se paie pas. La route posait pourtant `status='paid'` et une
    date de paiement sur n'importe quelle piece, sans regarder son type. Le
    devis sortait alors des filtres de devis par statut tout en restant compte
    dans la liste des devis : deux ecrans qui se contredisent sur la meme
    piece.
    """

    async def _devis(self, client) -> str:
        contact = await client.post(
            "/api/memory/contacts", json={"first_name": "Client", "last_name": "Paye"}
        )
        devis = await client.post(
            "/api/invoices/",
            json={
                "contact_id": contact.json()["id"],
                "document_type": "devis",
                "lines": [{"description": "Prestation", "quantity": 1,
                           "unit_price_ht": 1200.0, "tva_rate": 0.0}],
            },
        )
        assert devis.status_code == 200, devis.text
        return devis.json()["id"]

    @pytest.mark.asyncio
    async def test_marquer_paye_est_refuse_sur_un_devis(self, client):
        identifiant = await self._devis(client)

        reponse = await client.patch(f"/api/invoices/{identifiant}/mark-paid", json={})

        assert reponse.status_code == 400, (
            f"« paid » n'est pas un statut de devis, la porte PUT le refuse "
            f"deja : {reponse.status_code} {reponse.text[:200]}"
        )

    @pytest.mark.asyncio
    async def test_le_devis_refuse_garde_son_statut_et_reste_sans_date(self, client):
        identifiant = await self._devis(client)

        await client.patch(f"/api/invoices/{identifiant}/mark-paid", json={})

        relecture = await client.get(f"/api/invoices/{identifiant}")
        piece = relecture.json()
        assert piece["status"] == "draft", piece["status"]
        assert piece["payment_date"] is None, piece["payment_date"]

    @pytest.mark.asyncio
    async def test_une_facture_se_marque_toujours_payee(self, client):
        identifiant = await _facture(client, 1200.0)

        reponse = await client.patch(f"/api/invoices/{identifiant}/mark-paid", json={})

        assert reponse.status_code == 200, reponse.text
        assert reponse.json()["status"] == "paid"
