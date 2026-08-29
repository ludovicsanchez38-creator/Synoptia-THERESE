"""
F1 — une facture réelle, un seul montant, à travers toutes les couches.

Première étape du chantier F, et la SEULE de la 0.55. Son but n'est pas de
corriger : c'est de décider. Le plan F posait trois étapes et disait de ne
faire la deuxième que si la première la justifie.

- Vert  -> la dette « argent en float » est théorique, on s'arrête là.
- Rouge -> le test NOMME la couche qui diverge, on corrige cette couche, et on
           n'introduit pas de type `Money` pour autant.

Le montant est choisi pour exposer les arrondis : 3 x 33,33 EUR à 20 % donne
99,99 HT et 119,988 TTC. Un nombre rond ne teste pas l'arrondi - leçon de la
septième passe de `invoice_totals`, où mon test utilisait 1 000 et -200.
"""

import json

import pytest

MONTANT_UNITAIRE = 33.33
QUANTITE = 3
TAUX = 20.0


async def _poser_facture(client, devise: str = "EUR") -> str:
    contact = await client.post(
        "/api/memory/contacts", json={"first_name": "Client", "last_name": "F1"}
    )
    piece = await client.post(
        "/api/invoices/",
        json={
            "contact_id": contact.json()["id"],
            "document_type": "facture",
            "currency": devise,
            "lines": [
                {
                    "description": "Prestation",
                    "quantity": QUANTITE,
                    "unit_price_ht": MONTANT_UNITAIRE,
                    "tva_rate": TAUX,
                }
            ],
        },
    )
    assert piece.status_code == 200, piece.text
    identifiant = piece.json()["id"]

    from app.models.database import get_session_context
    from app.models.entities import Invoice
    from sqlalchemy import select

    async with get_session_context() as session:
        trouvee = await session.execute(select(Invoice).where(Invoice.id == identifiant))
        trouvee.scalars().one().status = "sent"
        await session.commit()
    return identifiant


class TestUnSeulMontantATraversLesCouches:
    @pytest.mark.asyncio
    async def test_la_base_et_le_schema_disent_la_meme_chose(self, client):
        identifiant = await _poser_facture(client)

        from app.models.database import get_session_context
        from app.models.entities import Invoice
        from sqlalchemy import select

        async with get_session_context() as session:
            resultat = await session.execute(
                select(Invoice).where(Invoice.id == identifiant)
            )
            en_base = resultat.scalars().one().total_ttc

        par_api = (await client.get(f"/api/invoices/{identifiant}")).json()["total_ttc"]

        assert par_api == en_base, f"schéma {par_api} vs base {en_base}"

    @pytest.mark.asyncio
    async def test_la_somme_des_lignes_egale_le_total_du_document(self, client):
        identifiant = await _poser_facture(client)
        piece = (await client.get(f"/api/invoices/{identifiant}")).json()

        # Ne PAS arrondir la somme ici : c'est ce que faisait mon premier jet,
        # et les trois sabotages passaient inaperçus. Arrondir des deux côtés
        # fait converger deux nombres qui divergent en base. On exige que
        # CHAQUE montant soit déjà rond au centime, là où il est stocké.
        for ligne in piece["lines"]:
            assert ligne["total_ttc"] == round(ligne["total_ttc"], 2), (
                f"une ligne stockée à {ligne['total_ttc']!r} traîne une "
                "troisième décimale : l'argent n'en a pas"
            )
            assert ligne["total_ht"] == round(ligne["total_ht"], 2)
        assert piece["total_ttc"] == round(piece["total_ttc"], 2), (
            f"document stocké à {piece['total_ttc']!r}"
        )
        assert piece["total_tax"] == round(piece["total_tax"], 2)

        somme = sum(ligne["total_ttc"] for ligne in piece["lines"])
        assert abs(somme - piece["total_ttc"]) < 0.005, (
            f"lignes {somme} vs document {piece['total_ttc']} : un client qui "
            "additionne les lignes du PDF ne retrouve pas le total"
        )
        assert piece["total_tax"] == round(piece["total_ttc"] - piece["subtotal_ht"], 2), (
            "la taxe affichée ne se déduit pas du HT et du TTC affichés"
        )

    @pytest.mark.asyncio
    async def test_l_outil_de_tresorerie_dit_le_meme_montant(self, client):
        identifiant = await _poser_facture(client)
        piece = (await client.get(f"/api/invoices/{identifiant}")).json()

        from app.models.database import get_session_context
        from app.services.workspace_tools import execute_workspace_tool

        async with get_session_context() as session:
            totaux = json.loads(await execute_workspace_tool("invoice_totals", {}, session))

        assert totaux["encours_ttc"] == piece["total_ttc"], (
            f"encours {totaux['encours_ttc']} vs document {piece['total_ttc']}"
        )
        ligne = next(d for d in totaux["documents"] if d["reference"] == piece["invoice_number"])
        assert ligne["montant_ttc"] == piece["total_ttc"]

    @pytest.mark.asyncio
    async def test_le_pdf_imprime_le_meme_montant(self, client):
        identifiant = await _poser_facture(client)
        piece = (await client.get(f"/api/invoices/{identifiant}")).json()

        attendu = f"{piece['total_ttc']:.2f}"
        from app.services import invoice_pdf

        source = invoice_pdf.__file__
        from pathlib import Path

        assert "total_ttc" in Path(source).read_text(encoding="utf-8"), (
            "le PDF ne lit plus le même champ"
        )
        # Le PDF formate `invoice_data['total_ttc']` en .2f : c'est la même
        # valeur, arrondie à l'affichage. On vérifie que l'arrondi d'affichage
        # ne CHANGE pas le montant (119.988 -> 119.99 serait une divergence).
        assert float(attendu) == piece["total_ttc"], (
            f"le PDF imprimerait {attendu} pour un document à {piece['total_ttc']}"
        )

    @pytest.mark.asyncio
    async def test_la_devise_voyage_avec_le_montant(self, client):
        """Un montant sans sa devise se lit en euros par défaut."""
        identifiant = await _poser_facture(client, devise="CHF")
        piece = (await client.get(f"/api/invoices/{identifiant}")).json()

        assert piece["currency"] == "CHF"

        from app.models.database import get_session_context
        from app.services.workspace_tools import execute_workspace_tool

        async with get_session_context() as session:
            totaux = json.loads(await execute_workspace_tool("invoice_totals", {}, session))

        ligne = next(d for d in totaux["documents"] if d["reference"] == piece["invoice_number"])
        assert ligne["devise"] == "CHF"


class TestLesCasQueMonPremierMontantNExposaitPas:
    """
    Trois sabotages passaient inaperçus après le premier jet de F1.

    3 x 33,33 fait 99,99 PILE : l'arrondi du HT ne pouvait pas diverger. Et une
    ligne unique ne peut pas exposer une taxe calculée par somme plutôt que par
    différence. Un test qui choisit un seul montant ne teste qu'un seul chemin -
    c'est la même leçon que les nombres ronds de la septième passe.
    """

    @pytest.mark.asyncio
    async def test_une_quantite_fractionnaire_arrondit_le_ht(self, client):
        """0,5 x 33,33 = 16,665 : trois décimales, que la base ne doit pas garder."""
        contact = await client.post(
            "/api/memory/contacts", json={"first_name": "Client", "last_name": "Demi"}
        )
        piece = await client.post(
            "/api/invoices/",
            json={
                "contact_id": contact.json()["id"],
                "document_type": "facture",
                "lines": [{"description": "Demi-journée", "quantity": 0.5,
                           "unit_price_ht": 33.33, "tva_rate": 20.0}],
            },
        )
        corps = piece.json()
        ligne = corps["lines"][0]

        assert ligne["total_ht"] == round(ligne["total_ht"], 2), (
            f"HT stocké à {ligne['total_ht']!r} : trois décimales en base"
        )
        assert corps["subtotal_ht"] == round(corps["subtotal_ht"], 2)

    @pytest.mark.asyncio
    async def test_plusieurs_taux_de_tva_ne_font_pas_deriver_la_taxe(self, client):
        """La taxe se déduit du HT et du TTC affichés, pas d'une somme parallèle."""
        contact = await client.post(
            "/api/memory/contacts", json={"first_name": "Client", "last_name": "Taux"}
        )
        piece = await client.post(
            "/api/invoices/",
            json={
                "contact_id": contact.json()["id"],
                "document_type": "facture",
                "lines": [
                    {"description": "Travaux", "quantity": 3, "unit_price_ht": 33.33,
                     "tva_rate": 10.0},
                    {"description": "Conseil", "quantity": 7, "unit_price_ht": 14.29,
                     "tva_rate": 20.0},
                    {"description": "Presse", "quantity": 1, "unit_price_ht": 9.99,
                     "tva_rate": 2.1},
                ],
            },
        )
        corps = piece.json()

        for ligne in corps["lines"]:
            assert ligne["total_ht"] == round(ligne["total_ht"], 2), ligne
            assert ligne["total_ttc"] == round(ligne["total_ttc"], 2), ligne

        assert corps["total_tax"] == round(corps["total_ttc"] - corps["subtotal_ht"], 2), (
            f"taxe {corps['total_tax']} ≠ {corps['total_ttc']} - {corps['subtotal_ht']} : "
            "une taxe calculée par somme parallèle dérive des deux totaux affichés"
        )
        assert corps["total_tax"] == round(corps["total_tax"], 2)

    @pytest.mark.asyncio
    async def test_la_somme_de_lignes_rondes_ne_traine_pas(self, client):
        """
        Dernier sabotage non détecté : sommer des lignes DÉJÀ arrondies peut
        encore traîner en flottant. 0,10 + 0,20 vaut 0.30000000000000004, et
        le JSON transmet ce nombre tel quel - à l'écran, au PDF, au modèle.
        """
        contact = await client.post(
            "/api/memory/contacts", json={"first_name": "Client", "last_name": "Traine"}
        )
        piece = await client.post(
            "/api/invoices/",
            json={
                "contact_id": contact.json()["id"],
                "document_type": "facture",
                "lines": [
                    {"description": "A", "quantity": 1, "unit_price_ht": 0.10, "tva_rate": 0.0},
                    {"description": "B", "quantity": 1, "unit_price_ht": 0.20, "tva_rate": 0.0},
                ],
            },
        )
        corps = piece.json()

        assert corps["subtotal_ht"] == 0.30, f"HT traîné : {corps['subtotal_ht']!r}"
        assert corps["total_ttc"] == 0.30, f"TTC traîné : {corps['total_ttc']!r}"
