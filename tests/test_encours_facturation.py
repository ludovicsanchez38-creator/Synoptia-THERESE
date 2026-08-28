"""B3 — « Combien me reste-t-il à encaisser ? »

Campagne dix personas, finding F4 de l'artisan : « C'est la seule question que
je pose tous les mois, avant la comptable. Si je dois recompter à la main, je
n'ai pas besoin de l'appli. »

Elle n'avait aucun chemin. `search_invoices` est un LOOKUP : `query`
obligatoire, ILIKE sur la référence ou le nom du client, limite 10, aucun
filtre de statut, aucune somme. Interrogé sur les impayés, le modèle a cherché
« Alain Moreau » — le seul nom qu'il avait — puis « encaissement août 2026 »,
et a conclu qu'il n'y avait rien.

Deux décisions de la relecture de design :

  * un OUTIL SÉPARÉ plutôt qu'un `search_invoices` surchargé — « un total sur
    10 lignes est un mensonge », et le lookup garderait sa limite ;
  * borné aux FACTURES (`document_type='facture'`) — sinon un devis envoyé
    entrerait dans l'encours, et l'artisan voulait 1 218 € (Garcia + SCI), pas
    son devis Moreau de 4 620 €.
"""
import json
from datetime import UTC, datetime, timedelta

import pytest


async def _poser_facture(client, montant, statut, jours_de_retard=0, type_doc="facture"):
    contact = await client.post(
        "/api/memory/contacts", json={"first_name": "Client", "last_name": f"N{montant}"}
    )
    facture = await client.post(
        "/api/invoices/",
        json={
            "contact_id": contact.json()["id"],
            "document_type": type_doc,
            "lines": [{"description": "Prestation", "quantity": 1,
                       "unit_price_ht": montant, "tva_rate": 0.0}],
        },
    )
    identifiant = facture.json()["id"]
    if statut != "draft":
        from app.models.database import get_session_context
        from app.models.entities import Invoice
        from sqlalchemy import select

        async with get_session_context() as session:
            trouvee = await session.execute(select(Invoice).where(Invoice.id == identifiant))
            en_base = trouvee.scalars().one()
            en_base.status = statut
            if jours_de_retard:
                en_base.due_date = datetime.now(UTC).replace(tzinfo=None) - timedelta(
                    days=jours_de_retard
                )
            await session.commit()
    return identifiant


class TestLOutilExisteEtEstAnnonce:
    def test_l_outil_est_declare_pour_le_chat(self):
        from app.services.workspace_tools import INVOICE_TOTALS_TOOL

        fonction = INVOICE_TOTALS_TOOL["function"]
        assert fonction["name"] == "invoice_totals"
        parametres = fonction["parameters"]
        assert not parametres.get("required"), (
            "aucun paramètre obligatoire : « combien me reste-t-il à encaisser » "
            "ne fournit ni référence ni nom de client"
        )


class TestLesMontantsSontJustes:
    @pytest.mark.asyncio
    async def test_l_encours_additionne_les_factures_non_payees(self, client):
        from app.models.database import get_session_context
        from app.services.workspace_tools import execute_workspace_tool

        await _poser_facture(client, 198.0, "overdue", jours_de_retard=44)
        await _poser_facture(client, 1020.0, "overdue", jours_de_retard=69)
        await _poser_facture(client, 500.0, "paid")

        async with get_session_context() as session:
            brut = await execute_workspace_tool("invoice_totals", {}, session)

        resultat = json.loads(brut)
        assert resultat["encours_ttc"] == pytest.approx(1218.0), (
            "l'artisan attendait 1 218 € : Garcia 198 + SCI 1 020, sans la payée"
        )
        assert resultat["nombre"] == 2

    @pytest.mark.asyncio
    async def test_un_devis_envoye_n_entre_pas_dans_l_encours(self, client):
        """Le point que la relecture a imposé.

        Un devis n'est pas une créance : il n'est pas dû. L'y compter aurait
        donné 5 838 € au lieu de 1 218 €.
        """
        from app.models.database import get_session_context
        from app.services.workspace_tools import execute_workspace_tool

        await _poser_facture(client, 198.0, "overdue", jours_de_retard=44)
        await _poser_facture(client, 4620.0, "sent", type_doc="devis")

        async with get_session_context() as session:
            resultat = json.loads(await execute_workspace_tool("invoice_totals", {}, session))

        assert resultat["encours_ttc"] == pytest.approx(198.0), (
            "un devis envoyé n'est pas un encaissement à venir"
        )

    @pytest.mark.asyncio
    async def test_les_retards_sont_distingues_de_l_encours(self, client):
        from app.models.database import get_session_context
        from app.services.workspace_tools import execute_workspace_tool

        await _poser_facture(client, 300.0, "sent")           # due, pas en retard
        await _poser_facture(client, 198.0, "overdue", jours_de_retard=44)

        async with get_session_context() as session:
            resultat = json.loads(await execute_workspace_tool("invoice_totals", {}, session))

        assert resultat["encours_ttc"] == pytest.approx(498.0)
        assert resultat["retard_ttc"] == pytest.approx(198.0), (
            "« depuis combien de temps » était la deuxième moitié de sa question"
        )

    @pytest.mark.asyncio
    async def test_sans_facture_l_outil_repond_zero_sans_mentir(self, client):
        from app.models.database import get_session_context
        from app.services.workspace_tools import execute_workspace_tool

        async with get_session_context() as session:
            resultat = json.loads(await execute_workspace_tool("invoice_totals", {}, session))

        assert resultat["encours_ttc"] == 0
        assert resultat["nombre"] == 0


class TestLOutilEstReellementAtteignable:
    """Un outil non exposé au modèle est du code mort — la leçon du jour."""

    def test_il_figure_dans_les_outils_du_chat(self):
        from app.services.workspace_tools import INVOICE_TOTALS_TOOL, WORKSPACE_TOOLS

        assert INVOICE_TOTALS_TOOL in WORKSPACE_TOOLS, (
            "sans cela, le modèle ne saurait pas qu'il peut totaliser, et "
            "retomberait sur search_invoices — c'est-à-dire sur rien"
        )

    def test_il_est_classe_en_lecture_seule(self):
        from app.services.contexte_execution import LECTURE_SEULE, classe_de

        assert classe_de("invoice_totals") == LECTURE_SEULE, (
            "un outil non classé est traité comme externe par prudence "
            "(`classe_de` défaut) : ici ce serait faux, il ne sort pas"
        )


class TestLesAvoirsEtLaDevise:
    """Deux montants faux hors du cas nominal, relevés par la relecture.

    « Un avoir `sent` de 200 € laisse l'encours à 1 000. `total_ttc` est
    toujours positif, donc les inclure sans signe serait pire. Il faut les
    soustraire. »
    """

    @pytest.mark.asyncio
    async def test_un_avoir_diminue_l_encours(self, client):
        from app.models.database import get_session_context
        from app.services.workspace_tools import execute_workspace_tool

        await _poser_facture(client, 1000.0, "sent")
        await _poser_facture(client, 200.0, "sent", type_doc="avoir")

        async with get_session_context() as session:
            resultat = json.loads(await execute_workspace_tool("invoice_totals", {}, session))

        assert resultat["encours_ttc"] == pytest.approx(800.0), (
            "un avoir est une créance NÉGATIVE : l'ignorer surestime l'encours, "
            "l'ajouter tel quel le double"
        )

    @pytest.mark.asyncio
    async def test_des_devises_melangees_ne_sont_pas_additionnees_en_silence(self, client):
        """« 1 000 EUR + 1 000 USD → 2 000, étiquetés au hasard. »"""
        from app.models.database import get_session_context
        from app.models.entities import Invoice
        from app.services.workspace_tools import execute_workspace_tool
        from sqlalchemy import select

        await _poser_facture(client, 1000.0, "sent")
        identifiant = await _poser_facture(client, 1000.0, "sent")

        async with get_session_context() as session:
            trouvee = await session.execute(select(Invoice).where(Invoice.id == identifiant))
            trouvee.scalars().one().currency = "USD"
            await session.commit()

            resultat = json.loads(await execute_workspace_tool("invoice_totals", {}, session))

        assert resultat.get("devises_multiples") is True, (
            "sommer des devises différentes sans le dire produit un chiffre "
            "qui n'existe pas"
        )
