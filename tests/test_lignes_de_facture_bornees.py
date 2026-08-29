"""
Une ligne de facture ne porte pas de montant négatif.

Dette nommée à la 0.54.0, requalifiée par la revue de plan : `InvoiceLineRequest`
n'impose AUCUNE borne, et le garde-fou n'existe que côté écran
(`InvoiceForm.tsx` refuse `quantity < 1` et `unit_price_ht < 0`). L'API et le
serveur MCP, eux, acceptent tout. Un modèle qui « corrige » une ligne, ou un
script, invente alors un avoir fantôme : le total devient négatif sans qu'aucun
avoir existe.

Vérifié AVANT d'écrire la borne, comme la revue l'exigeait : un avoir est un
`document_type` à part entière (préfixe AV-), avec un `total_ttc` stocké
POSITIF. Le borner ne casse donc pas les avoirs.

Deux nuances contre l'instruction reçue, tirées du code :
- « strictement positif » pour le PRIX casserait une ligne offerte à 0 €, que
  l'écran autorise. On refuse le négatif, pas la gratuité.
- La quantité, elle, est bornée à 1 par l'écran (`min={1}`) ; on accepte toute
  quantité strictement positive côté API pour ne pas interdire une demi-journée.
"""

import pytest


class TestLApiRefuseUneLigneNegative:
    @pytest.mark.asyncio
    async def test_un_prix_negatif_est_refuse(self, client):
        contact = await client.post(
            "/api/memory/contacts", json={"first_name": "Client", "last_name": "Borne"}
        )
        reponse = await client.post(
            "/api/invoices/",
            json={
                "contact_id": contact.json()["id"],
                "document_type": "facture",
                "lines": [
                    {"description": "Ligne empoisonnée", "quantity": 1,
                     "unit_price_ht": -100.0, "tva_rate": 20.0}
                ],
            },
        )
        assert reponse.status_code == 422, (
            "une ligne à -100 EUR crée un avoir fantôme : l'encours devient "
            f"négatif sans qu'aucun avoir existe (reçu {reponse.status_code})"
        )

    @pytest.mark.asyncio
    async def test_une_quantite_negative_est_refusee(self, client):
        contact = await client.post(
            "/api/memory/contacts", json={"first_name": "Client", "last_name": "Borne2"}
        )
        reponse = await client.post(
            "/api/invoices/",
            json={
                "contact_id": contact.json()["id"],
                "document_type": "facture",
                "lines": [
                    {"description": "Quantité négative", "quantity": -2,
                     "unit_price_ht": 100.0, "tva_rate": 20.0}
                ],
            },
        )
        assert reponse.status_code == 422

    @pytest.mark.asyncio
    async def test_une_ligne_offerte_reste_possible(self, client):
        """L'écran autorise 0 € : la borne ne doit pas interdire la gratuité."""
        contact = await client.post(
            "/api/memory/contacts", json={"first_name": "Client", "last_name": "Offert"}
        )
        reponse = await client.post(
            "/api/invoices/",
            json={
                "contact_id": contact.json()["id"],
                "document_type": "facture",
                "lines": [
                    {"description": "Prestation", "quantity": 1,
                     "unit_price_ht": 500.0, "tva_rate": 20.0},
                    {"description": "Livraison offerte", "quantity": 1,
                     "unit_price_ht": 0.0, "tva_rate": 20.0},
                ],
            },
        )
        assert reponse.status_code == 200, reponse.text

    @pytest.mark.asyncio
    async def test_une_demi_journee_reste_possible(self, client):
        """La quantité fractionnaire est légitime : 0,5 jour de formation."""
        contact = await client.post(
            "/api/memory/contacts", json={"first_name": "Client", "last_name": "Demi"}
        )
        reponse = await client.post(
            "/api/invoices/",
            json={
                "contact_id": contact.json()["id"],
                "document_type": "facture",
                "lines": [
                    {"description": "Formation", "quantity": 0.5,
                     "unit_price_ht": 800.0, "tva_rate": 20.0}
                ],
            },
        )
        assert reponse.status_code == 200, reponse.text

    @pytest.mark.asyncio
    async def test_un_avoir_reste_creable(self, client):
        """Un avoir est un document_type, pas une ligne négative."""
        contact = await client.post(
            "/api/memory/contacts", json={"first_name": "Client", "last_name": "Avoir"}
        )
        reponse = await client.post(
            "/api/invoices/",
            json={
                "contact_id": contact.json()["id"],
                "document_type": "avoir",
                "lines": [
                    {"description": "Geste commercial", "quantity": 1,
                     "unit_price_ht": 200.0, "tva_rate": 20.0}
                ],
            },
        )
        assert reponse.status_code == 200, reponse.text


class TestLeCheminMcpEstFermeEtBorne:
    """
    La revue de plan m'annonçait un trou côté MCP : `create_invoice` y expose
    `unit_price`, sans borne. Vérifié par exécution plutôt que par lecture du
    schéma : le chemin est en fait FERMÉ en amont - `create_invoice` est dans
    `MUTATING_TOOLS`, donc retiré des outils annoncés au modèle ET des routes.

    Le schéma est borné quand même, en défense en profondeur : le jour où ce
    filtre saute, la borne ne doit pas être à réinventer. Ce test fige les
    DEUX protections, parce qu'une seule des deux est celle qui protège
    aujourd'hui, et l'autre celle qui protégera demain.
    """

    def test_l_outil_nest_pas_annonce_au_modele(self):
        from app.services.mcp_therese_server import TOOLS

        noms = {outil["name"] for outil in TOOLS}
        assert "create_invoice" not in noms, (
            "un outil mutant annoncé au modèle sans protocole de confirmation"
        )

    def test_l_outil_na_pas_de_route(self):
        from app.services.mcp_therese_server import TOOL_ROUTES

        assert "create_invoice" not in TOOL_ROUTES

    def test_le_schema_reste_borne_pour_le_jour_ou_il_rouvrira(self):
        from pathlib import Path

        import app.services.mcp_therese_server as serveur

        texte = Path(serveur.__file__).read_text(encoding="utf-8")
        i = texte.find('"unit_price"')
        assert i != -1, "le schéma MCP a changé de nom de champ"
        bloc = texte[i : i + 120]
        assert "minimum" in bloc, (
            "sans borne, un modèle qui « corrige » une ligne inventerait un "
            "avoir fantôme le jour où l'outil est rouvert"
        )
