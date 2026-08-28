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

    @pytest.mark.asyncio
    async def test_devises_melangees_aucun_total_additionne_nest_rendu(self, client):
        """
        Revue de release (Soso, 28/08) : un drapeau à côté d'un chiffre ne
        retient pas le chiffre.

        Le test précédent n'exigeait que `devises_multiples is True`. Il
        passait pendant que `encours_ttc` valait la somme brute de 1 000 EUR
        et 1 000 USD, arrondie à deux décimales. Le modèle lit un nombre et
        répond « ton encours est de 2 000 € » : THÉRÈSE affirme un montant
        qui n'existe dans aucune devise, là où la 0.53.0 avouait ne pas
        savoir. Un drapeau ne s'oppose pas à un nombre, il le décore.

        Ce que la fonction doit rendre : le détail par devise, et AUCUN total
        additionné.
        """
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

        assert resultat["encours_ttc"] is None, (
            "un total additionné à travers les devises est un chiffre faux : "
            f"rendu {resultat['encours_ttc']!r}"
        )
        # Corrigé à la cinquième passe. Ce test exigeait `null` pour le retard
        # au motif que deux devises se mélangent. Mais aucune de ces deux
        # factures n'a d'échéance : rien n'est échu, et « zéro » est alors une
        # réponse EXACTE, pas une ignorance. Le gate du retard lit désormais
        # les devises des seules factures échues.
        assert resultat["retard_ttc"] == 0, "rien n'est échu : le retard vaut zéro"
        assert resultat["encours_par_devise"] == {"EUR": 1000.0, "USD": 1000.0}, (
            "à défaut d'un total, rendre ce qui est vrai : un montant par devise"
        )

    @pytest.mark.asyncio
    async def test_chaque_facture_du_detail_porte_sa_devise(self, client):
        """Un montant sans devise se lit en euros par défaut."""
        from app.models.database import get_session_context
        from app.services.workspace_tools import execute_workspace_tool

        await _poser_facture(client, 1000.0, "sent")

        async with get_session_context() as session:
            resultat = json.loads(await execute_workspace_tool("invoice_totals", {}, session))

        assert resultat["documents"], "la facture posée doit apparaître"
        assert resultat["documents"][0]["devise"] == "EUR", (
            "`montant_ttc` sans devise laisse le modèle choisir l'étiquette"
        )

    @pytest.mark.asyncio
    async def test_aucune_facture_ne_peut_exister_sans_devise(self, client):
        """
        Angle mort supposé du correctif, mesuré : il n'existe pas.

        `devises` ignore les valeurs nulles (`if d.currency`). Une facture
        sans devise à côté d'une facture en USD donnerait donc une seule
        devise, et le total global serait calculé sur les deux — le garde-fou
        s'éteindrait au moment précis où l'ambiguïté est la plus grande.

        Ce qui l'empêche n'est pas le code de `_invoice_totals` : c'est la
        contrainte NOT NULL du schéma. Ce test la fige, parce que le jour où
        elle tomberait, le filtre `if d.currency` deviendrait un trou sans
        que rien d'autre ne le signale.
        """
        from app.models.database import get_session_context
        from app.models.entities import Invoice
        from sqlalchemy import select

        identifiant = await _poser_facture(client, 100.0, "sent")

        # L'erreur remonte telle que la pose le pilote (sqlcipher3), pas
        # enveloppée par SQLAlchemy : viser `IntegrityError` de sqlalchemy.exc
        # laisserait le test échouer alors que la contrainte a bien tenu.
        with pytest.raises(Exception, match="invoices.currency"):
            async with get_session_context() as session:
                trouvee = await session.execute(
                    select(Invoice).where(Invoice.id == identifiant)
                )
                trouvee.scalars().one().currency = None
                await session.commit()


class TestLeDetecteurEtLeDetailParlentDeLaMemeDevise:
    """
    Revérification de release (Soso, 28/08) : mon correctif avait deux moitiés
    qui ne parlaient pas de la même chose.

    `_devise()` traite une devise absente comme EUR pour le détail, mais le
    décompte l'ignorait (`if d.currency`). Une facture sans devise à côté
    d'une facture en USD donnait donc UNE seule devise : `encours_ttc: 2000`,
    étiqueté `devise: "USD"`, `devises_multiples: false` — pendant que le
    détail affichait 1 000 EUR et 1 000 USD. Le garde-fou s'éteignait au
    moment précis où l'ambiguïté était la plus grande.

    J'avais écarté ce cas en concluant « le schéma l'interdit ». C'était vrai
    d'une base NEUVE seulement : la migration desktop ajoute
    `currency TEXT DEFAULT 'EUR'` SANS NOT NULL (`database.py`), et les bases
    des testeurs sont toutes migrées. Une preuve tirée du mauvais périmètre
    ressemble à une preuve.
    """

    def test_une_devise_absente_compte_comme_celle_du_detail(self):
        from app.services.workspace_tools import _devise, _devises_presentes

        class _Doc:
            def __init__(self, devise):
                self.currency = devise

        sans, en_dollars = _Doc(None), _Doc("USD")

        assert _devise(sans) == "EUR", "le détail lit une devise absente comme EUR"
        assert _devises_presentes([sans, en_dollars]) == {"EUR", "USD"}, (
            "le décompte doit lire la même chose que le détail, sinon un "
            "mélange passe pour une devise unique"
        )

    def test_une_devise_vide_ne_disparait_pas_non_plus(self):
        from app.services.workspace_tools import _devises_presentes

        class _Doc:
            def __init__(self, devise):
                self.currency = devise

        assert _devises_presentes([_Doc(""), _Doc("CHF")]) == {"EUR", "CHF"}


class TestUnAvoirNestPasUnEncoursNegatif:
    """
    Revérification de release (Soso, 28/08).

    Une facture de 1 000 EUR et un avoir de 200 USD donnaient
    `encours_par_devise = {"EUR": 1000, "USD": -200}`. Arithmétiquement c'est
    un solde net ; mais le champ s'appelle « encours », c'est-à-dire ce qui
    RESTE À ENCAISSER. Or -200 USD n'est pas à encaisser : c'est un avoir,
    une somme due au client. Le nom promettait une chose, le nombre en disait
    une autre.
    """

    @pytest.mark.asyncio
    async def test_les_avoirs_sont_exposes_a_part(self, client):
        from app.models.database import get_session_context
        from app.models.entities import Invoice
        from app.services.workspace_tools import execute_workspace_tool
        from sqlalchemy import select

        await _poser_facture(client, 1000.0, "sent")
        avoir = await _poser_facture(client, 200.0, "sent", type_doc="avoir")

        async with get_session_context() as session:
            trouve = await session.execute(select(Invoice).where(Invoice.id == avoir))
            trouve.scalars().one().currency = "USD"
            await session.commit()

            resultat = json.loads(await execute_workspace_tool("invoice_totals", {}, session))

        assert resultat["avoirs_par_devise"] == {"USD": 200.0}, (
            "un avoir doit être lisible pour lui-même, pas seulement comme "
            "un encours négatif"
        )
        # Réécrit à la cinquième passe. Ce test acceptait qu'un net négatif
        # reste dans `encours_par_devise` À CONDITION qu'une note l'explique.
        # C'était précisément le défaut : une note ne retient pas un chiffre,
        # elle le rend crédible. Le négatif ne vit plus sous ce nom.
        assert "USD" not in resultat["encours_par_devise"]
        assert resultat["du_au_client_par_devise"] == {"USD": 200.0}


class TestLeCasQueSosoAExecute:
    """
    Le cas exact de la revérification : 1 000 sans devise + 1 000 USD.

    Soso l'a fait tourner et THÉRÈSE recevait `encours_ttc: 2000`, étiqueté
    `devise: "USD"`, `devises_multiples: false`, pendant que le détail
    affichait 1 000 EUR et 1 000 USD. Un montant inventé, avec une étiquette
    au hasard, présenté comme certain.

    Ce test passe par `_totaux_des_documents`, la fonction extraite : c'est
    le SEUL moyen d'exercer ce cas, puisqu'une base de test neuve refuse une
    devise nulle (NOT NULL) alors que les bases migrées des testeurs
    l'acceptent. Un test qui n'appelait que l'aide `_devises_presentes`
    laissait le sabotage passer : la remise de l'ancien filtre dans
    `_totaux_des_documents` n'était détectée par rien.
    """

    class _Doc:
        def __init__(self, devise, montant, type_doc="facture", statut="sent"):
            self.currency = devise
            self.total_ttc = montant
            self.document_type = type_doc
            self.status = statut
            self.due_date = None
            self.invoice_number = f"X-{montant}"
            self.contact = None

    def test_une_facture_sans_devise_ne_masque_pas_le_melange(self):
        from datetime import UTC, datetime

        from app.services.workspace_tools import _totaux_des_documents

        resultat = _totaux_des_documents(
            [self._Doc(None, 1000.0), self._Doc("USD", 1000.0)],
            datetime.now(UTC).replace(tzinfo=None),
        )

        assert resultat["devises_multiples"] is True, (
            "une devise absente n'est pas une devise commune"
        )
        assert resultat["encours_ttc"] is None, (
            f"total inventé sur des devises hétérogènes : {resultat['encours_ttc']!r}"
        )
        assert resultat["devise"] is None, (
            f"étiquette choisie au hasard : {resultat['devise']!r}"
        )
        assert resultat["encours_par_devise"] == {"EUR": 1000.0, "USD": 1000.0}

    def test_un_avoir_seul_dans_sa_devise_est_annonce_comme_un_avoir(self):
        from datetime import UTC, datetime

        from app.services.workspace_tools import _totaux_des_documents

        resultat = _totaux_des_documents(
            [self._Doc("EUR", 1000.0), self._Doc("USD", 200.0, type_doc="avoir")],
            datetime.now(UTC).replace(tzinfo=None),
        )

        assert resultat["avoirs_par_devise"] == {"USD": 200.0}
        # Réécrit à la cinquième passe. Ce test se contentait d'une NOTE
        # expliquant le -200 USD resté dans `encours_par_devise`. La note ne
        # retenait pas le chiffre : le modèle lisait le dictionnaire, que le
        # prompt lui ordonne justement de lire quand le scalaire est null.
        assert "USD" not in resultat["encours_par_devise"]
        assert resultat["du_au_client_par_devise"] == {"USD": 200.0}
        assert resultat["encours_par_devise"] == {"EUR": 1000.0}


class TestDeuxChiffresPourLaMemeChoseNeDoiventPasDifferer:
    """
    Troisième passe de revue (Soso, 28/08).

    `retard_par_devise` et `avoirs_par_devise` arrondissaient APRÈS chaque
    addition, alors que `retard_ttc` et `encours_par_devise` accumulent puis
    arrondissent une fois. Deux documents à 1,055 EUR donnaient donc
    `retard_ttc: 2.11` et `retard_par_devise: {"EUR": 2.10}` — un centime
    d'écart entre deux champs du MÊME résultat, sur une question d'argent.

    Le modèle lit les deux et en cite un ; lequel dépend de la phrase.
    """

    class _Doc:
        def __init__(self, devise, montant, type_doc="facture", statut="overdue"):
            from datetime import UTC, datetime, timedelta

            self.currency = devise
            self.total_ttc = montant
            self.document_type = type_doc
            self.status = statut
            # Echeance REELLEMENT depassee : depuis la quatrieme passe, le
            # retard se constate sur la date et non sur le statut. Ce test
            # s'appuyait sur l'ancienne regle, qui etait le defaut.
            self.due_date = datetime.now(UTC).replace(tzinfo=None) - timedelta(days=3)
            self.invoice_number = f"X-{montant}"
            self.contact = None

    def test_le_retard_par_devise_egale_le_retard_global(self):
        from datetime import UTC, datetime

        from app.services.workspace_tools import _totaux_des_documents

        resultat = _totaux_des_documents(
            [self._Doc("EUR", 1.055), self._Doc("EUR", 1.055)],
            datetime.now(UTC).replace(tzinfo=None),
        )

        assert resultat["retard_par_devise"]["EUR"] == resultat["retard_ttc"], (
            f"{resultat['retard_par_devise']['EUR']} vs {resultat['retard_ttc']}"
        )

    def test_les_avoirs_par_devise_suivent_le_meme_arrondi(self):
        from datetime import UTC, datetime

        from app.services.workspace_tools import _totaux_des_documents

        resultat = _totaux_des_documents(
            [
                self._Doc("EUR", 1.055, type_doc="avoir"),
                self._Doc("EUR", 1.055, type_doc="avoir"),
            ],
            datetime.now(UTC).replace(tzinfo=None),
        )

        # Réécrit à la cinquième passe : un net négatif a quitté
        # `encours_par_devise` pour `du_au_client_par_devise`. Ce que ce test
        # vérifie reste le même - les deux champs disent le même montant, au
        # centime près, sans divergence d'arrondi.
        assert resultat["avoirs_par_devise"]["EUR"] == resultat["du_au_client_par_devise"]["EUR"], (
            f"{resultat['avoirs_par_devise']} vs {resultat['du_au_client_par_devise']}"
        )


class TestUnRetardNeSeCompteJamaisEnJoursNegatifs:
    """
    Troisième passe de revue (Soso, 28/08).

    Le calcul compte une facture comme en retard si `status == "overdue"` OU
    si l'échéance est passée, mais mesure l'ancienneté sur la seule date.
    Une facture marquée `overdue` avec une échéance FUTURE - que l'API
    accepte - rendait `plus_ancien_retard_jours: -5`. Un retard de moins cinq
    jours n'existe pas ; c'est le statut et la date qui se contredisent, et
    le résultat présente cette contradiction comme un fait.
    """

    class _Doc:
        def __init__(self, echeance, statut="overdue"):
            self.currency = "EUR"
            self.total_ttc = 1000.0
            self.document_type = "facture"
            self.status = statut
            self.due_date = echeance
            self.invoice_number = "FUTUR-001"
            self.contact = None

    def test_une_echeance_future_ne_produit_pas_un_retard_negatif(self):
        from datetime import UTC, datetime, timedelta

        from app.services.workspace_tools import _totaux_des_documents

        maintenant = datetime.now(UTC).replace(tzinfo=None)
        resultat = _totaux_des_documents(
            [self._Doc(maintenant + timedelta(days=5))], maintenant
        )

        jours = resultat["plus_ancien_retard_jours"]
        assert jours is None or jours >= 0, f"retard de {jours} jours"


class TestUneFactureNegativeNestPasUnAvoir:
    """
    Troisième passe de revue (Soso, 28/08).

    `InvoiceLineRequest` n'impose aucune borne : le backend accepte une
    facture à -100 EUR, le garde-fou n'existant que côté écran. L'encours
    devenait négatif, et ma note le qualifiait d'« avoir » alors que
    `nombre_avoirs` valait 0. Une explication fausse est pire qu'un chiffre
    nu : elle rend le chiffre crédible.

    Fermer la validation est une décision produit (une ligne négative sert
    aussi de remise), donc elle reste ouverte et nommée. Ce que la revue
    corrige ici, c'est le mensonge : THÉRÈSE signale l'anomalie au lieu de
    l'expliquer de travers.
    """

    class _Doc:
        def __init__(self, montant, type_doc="facture"):
            self.currency = "EUR"
            self.total_ttc = montant
            self.document_type = type_doc
            self.status = "sent"
            self.due_date = None
            self.invoice_number = "NEG-001"
            self.contact = None

    def test_un_encours_negatif_sans_avoir_est_signale_comme_anomalie(self):
        from datetime import UTC, datetime

        from app.services.workspace_tools import _totaux_des_documents

        resultat = _totaux_des_documents(
            [self._Doc(-100.0)], datetime.now(UTC).replace(tzinfo=None)
        )

        assert resultat["nombre_avoirs"] == 0
        # Réécrit à la cinquième passe. Ce test exigeait une NOTE d'anomalie à
        # côté du montant négatif. Grok a montré que c'était le même geste que
        # `devises_multiples` : le drapeau change de forme, le chiffre reste
        # lisible sous un nom qui ment. Plus de note, plus de négatif sous
        # « encours » - le montant vit sous un nom exact.
        assert "EUR" not in resultat["encours_par_devise"]
        assert resultat["du_au_client_par_devise"] == {"EUR": 100.0}
        assert "anomalie" not in resultat["note"].lower()


class TestUnNombreQuiNestPlusUnEncoursNestPasRendu:
    """
    Quatrième passe (Grok, 28/08) : le clone de la passe 1, sur l'autre axe.

    La passe 1 a appris qu'un drapeau ne retient pas un nombre : le modèle lit
    2000 malgré `devises_multiples: true`. J'ai donc annulé le total quand les
    DEVISES se mélangent. Mais je n'ai pas annulé le total quand le nombre
    cesse d'être un encours.

    Avoirs seuls, ou avoirs plus gros que les factures, une seule devise :
    `encours_ttc: -200`. Le champ s'appelle « reste à encaisser ». -200 n'est
    pas à encaisser. Le drapeau a changé de forme (une note, un dictionnaire
    d'avoirs) ; le nombre, lui, est resté. Même règle, autre axe.

    Règle gelée : `encours_ttc` et `retard_ttc` ne valent un nombre que si
    UNE devise ET ce nombre est positif ou nul. Sinon `null`.
    """

    class _Doc:
        def __init__(self, montant, type_doc="facture", echeance=None):
            self.currency = "EUR"
            self.total_ttc = montant
            self.document_type = type_doc
            self.status = "sent"
            self.due_date = echeance
            self.invoice_number = f"D-{montant}"
            self.contact = None

    def test_un_avoir_seul_ne_rend_pas_un_encours_negatif(self):
        from datetime import UTC, datetime

        from app.services.workspace_tools import _totaux_des_documents

        resultat = _totaux_des_documents(
            [self._Doc(200.0, type_doc="avoir")],
            datetime.now(UTC).replace(tzinfo=None),
        )

        assert resultat["encours_ttc"] is None, (
            f"-200 n'est pas un reste à encaisser : {resultat['encours_ttc']!r}"
        )

    def test_des_avoirs_plus_gros_que_les_factures_non_plus(self):
        from datetime import UTC, datetime

        from app.services.workspace_tools import _totaux_des_documents

        resultat = _totaux_des_documents(
            [self._Doc(100.0), self._Doc(300.0, type_doc="avoir")],
            datetime.now(UTC).replace(tzinfo=None),
        )

        assert resultat["encours_ttc"] is None

    def test_un_encours_positif_reste_un_nombre(self):
        """La règle ne doit pas tout éteindre : sans ceci, elle serait inutile."""
        from datetime import UTC, datetime

        from app.services.workspace_tools import _totaux_des_documents

        resultat = _totaux_des_documents(
            [self._Doc(1000.0), self._Doc(200.0, type_doc="avoir")],
            datetime.now(UTC).replace(tzinfo=None),
        )

        assert resultat["encours_ttc"] == 800.0

    def test_un_retard_negatif_nest_pas_rendu_non_plus(self):
        """
        Garde-fou trouvé NON COUVERT par le sabotage : retirer `retard >= 0`
        ne cassait aucun test. Une facture à montant négatif - que le backend
        accepte, faute de borne sur `InvoiceLineRequest` - et dont l'échéance
        est dépassée rend un « montant en retard » négatif. Un retard négatif
        n'est pas un retard.
        """
        from datetime import UTC, datetime, timedelta

        from app.services.workspace_tools import _totaux_des_documents

        maintenant = datetime.now(UTC).replace(tzinfo=None)
        doc = self._Doc(-500.0)
        doc.due_date = maintenant - timedelta(days=10)

        resultat = _totaux_des_documents([doc], maintenant)

        assert resultat["retard_ttc"] is None, (
            f"retard de {resultat['retard_ttc']!r} EUR"
        )


class TestUnMontantEnRetardSuitLEcheancePasLeStatut:
    """
    Quatrième passe (Grok, 28/08) : j'ai patché l'âge, pas le tas.

    La passe 3 a supprimé le « retard de -5 jours ». Mais l'appartenance à
    `en_retard` est restée « statut overdue OU échéance dépassée ». Une
    facture marquée overdue dont l'échéance tombe dans cinq jours entre donc
    toujours dans `retard_ttc`, avec `jours_de_retard: 0` et
    `plus_ancien_retard_jours: null`. Le résultat dit « 1 000 € en retard
    depuis 0 jour ». L'âge est devenu honnête, le montant est resté faux.
    """

    class _Doc:
        def __init__(self, echeance, statut="overdue"):
            self.currency = "EUR"
            self.total_ttc = 1000.0
            self.document_type = "facture"
            self.status = statut
            self.due_date = echeance
            self.invoice_number = "FUT-001"
            self.contact = None

    def test_une_echeance_future_nentre_pas_dans_le_montant_en_retard(self):
        from datetime import UTC, datetime, timedelta

        from app.services.workspace_tools import _totaux_des_documents

        maintenant = datetime.now(UTC).replace(tzinfo=None)
        resultat = _totaux_des_documents(
            [self._Doc(maintenant + timedelta(days=5))], maintenant
        )

        assert resultat["retard_ttc"] in (0, 0.0, None), (
            f"« en retard depuis 0 jour » pour {resultat['retard_ttc']} EUR"
        )
        assert resultat["nombre_en_retard"] == 0

    def test_une_echeance_depassee_compte_toujours(self):
        from datetime import UTC, datetime, timedelta

        from app.services.workspace_tools import _totaux_des_documents

        maintenant = datetime.now(UTC).replace(tzinfo=None)
        resultat = _totaux_des_documents(
            [self._Doc(maintenant - timedelta(days=5), statut="sent")], maintenant
        )

        assert resultat["retard_ttc"] == 1000.0
        assert resultat["plus_ancien_retard_jours"] == 5


class TestLaListeDeDocumentsSeSommeSansContredireLeTotal:
    """
    Quatrième passe (Grok, 28/08).

    `factures[]` ne contient que les factures ; `encours_ttc` en soustrait les
    avoirs. Un modèle qui additionne la liste - geste fréquent, surtout sur
    « quelles factures ne sont pas payées » - obtient 1 000 quand l'encours
    vaut 800. Deux chiffres dans le même résultat, tous deux défendables,
    dont un faux selon la question posée.

    La consigne « ne fabrique pas de total » ne portait que sur le mélange de
    devises. Le détail doit donc porter les avoirs, signés.
    """

    class _Doc:
        def __init__(self, montant, type_doc="facture", numero="X"):
            self.currency = "EUR"
            self.total_ttc = montant
            self.document_type = type_doc
            self.status = "sent"
            self.due_date = None
            self.invoice_number = numero
            self.contact = None

    def test_la_somme_du_detail_egale_l_encours(self):
        from datetime import UTC, datetime

        from app.services.workspace_tools import _totaux_des_documents

        resultat = _totaux_des_documents(
            [
                self._Doc(1000.0, numero="FACT-1"),
                self._Doc(200.0, type_doc="avoir", numero="AV-1"),
            ],
            datetime.now(UTC).replace(tzinfo=None),
        )

        somme = round(sum(d["montant_ttc"] for d in resultat["documents"]), 2)
        assert somme == resultat["encours_ttc"], (
            f"la liste somme à {somme}, l'encours vaut {resultat['encours_ttc']}"
        )

    def test_chaque_ligne_dit_son_type(self):
        from datetime import UTC, datetime

        from app.services.workspace_tools import _totaux_des_documents

        resultat = _totaux_des_documents(
            [self._Doc(200.0, type_doc="avoir", numero="AV-1")],
            datetime.now(UTC).replace(tzinfo=None),
        )

        assert resultat["documents"][0]["type"] == "avoir"
        assert resultat["documents"][0]["montant_ttc"] == -200.0, (
            "un avoir listé positivement se resomme comme une créance"
        )



class TestUneFactureSansEcheanceResteDansLEncours:
    """
    Conséquence assumée du gel, figée pour qu'elle reste un choix.

    Depuis que le retard se constate sur l'échéance seule, une facture marquée
    « overdue » SANS échéance n'entre plus dans `retard_ttc`. L'API pose
    toujours une échéance (+30 jours par défaut), mais une base migrée peut
    porter des factures sans.

    Ce n'est pas une perte d'argent : la facture reste dans `encours_ttc`,
    c'est le sous-ensemble « en retard » qui rétrécit. Sans date, on ne peut
    pas affirmer qu'une facture est en retard - on n'a que le statut posé à
    la main, et c'est précisément ce que la quatrième passe a écarté.
    """

    class _Doc:
        def __init__(self):
            self.currency = "EUR"
            self.total_ttc = 1000.0
            self.document_type = "facture"
            self.status = "overdue"
            self.due_date = None
            self.invoice_number = "SANS-ECHEANCE"
            self.contact = None

    def test_elle_compte_dans_l_encours_mais_pas_dans_le_retard(self):
        from datetime import UTC, datetime

        from app.services.workspace_tools import _totaux_des_documents

        resultat = _totaux_des_documents(
            [self._Doc()], datetime.now(UTC).replace(tzinfo=None)
        )

        assert resultat["encours_ttc"] == 1000.0, "l'argent dû ne disparaît pas"
        assert resultat["retard_ttc"] == 0, "sans date, le retard ne s'affirme pas"
        assert resultat["nombre"] == 1
        assert resultat["nombre_en_retard"] == 0


class TestAucunChampNommeEncoursNePorteUnNegatif:
    """
    Cinquième passe (Grok, 28/08) : la passe 1 rejouée pour la troisième fois.

    J'ai gelé le SCALAIRE `encours_ttc`. Le nombre est resté dans le résultat,
    sous un autre nom - `encours_par_devise: {"EUR": -200}` - et le prompt
    ORDONNE au modèle de lire le dictionnaire quand le scalaire vaut null.
    Le drapeau a changé de forme (null, plus une note), le chiffre a changé de
    champ. C'est le même geste que `devises_multiples`, la troisième fois.

    Règle, appliquée à TOUS les champs et plus au seul scalaire : rien de ce
    qui s'appelle « encours » ou « retard » ne porte un montant négatif. Ce
    qui est dû au client vit dans un champ qui le dit.
    """

    class _Doc:
        def __init__(self, montant, type_doc="facture", devise="EUR", echeance=None):
            self.currency = devise
            self.total_ttc = montant
            self.document_type = type_doc
            self.status = "sent"
            self.due_date = echeance
            self.invoice_number = f"D-{montant}"
            self.contact = None

    @staticmethod
    def _totaux(documents):
        from datetime import UTC, datetime

        from app.services.workspace_tools import _totaux_des_documents

        return _totaux_des_documents(documents, datetime.now(UTC).replace(tzinfo=None))

    def test_un_avoir_seul_ne_laisse_aucun_negatif_dans_encours_par_devise(self):
        resultat = self._totaux([self._Doc(200.0, type_doc="avoir")])

        assert all(m >= 0 for m in resultat["encours_par_devise"].values()), (
            f"négatif sous un nom qui veut dire « à encaisser » : "
            f"{resultat['encours_par_devise']}"
        )
        assert resultat["du_au_client_par_devise"] == {"EUR": 200.0}, (
            "ce qui est dû au client doit vivre dans un champ qui le dit"
        )

    def test_un_retard_negatif_ne_survit_pas_dans_le_dictionnaire(self):
        from datetime import UTC, datetime, timedelta

        maintenant = datetime.now(UTC).replace(tzinfo=None)
        resultat = self._totaux(
            [self._Doc(-500.0, echeance=maintenant - timedelta(days=10))]
        )

        assert all(m >= 0 for m in resultat["retard_par_devise"].values()), (
            f"retard négatif : {resultat['retard_par_devise']}"
        )

    def test_les_devises_saines_survivent_au_nettoyage(self):
        """Sans ceci, la règle éteindrait l'outil au lieu de le rendre honnête."""
        resultat = self._totaux(
            [
                self._Doc(1000.0),
                self._Doc(500.0, devise="USD"),
                self._Doc(200.0, type_doc="avoir"),
            ]
        )

        assert resultat["encours_par_devise"] == {"EUR": 800.0, "USD": 500.0}
        assert resultat["du_au_client_par_devise"] == {}

    def test_plus_aucune_note_ne_decore_un_chiffre(self):
        """
        Les notes « avoir net » et « anomalie » commentaient un négatif qui
        n'existe plus. Une note qui explique un chiffre le rend crédible ;
        c'est ce qui avait fait passer -100 pour un avoir alors qu'aucun avoir
        n'existait. Reste la mention du périmètre, qui ne commente rien.
        """
        resultat = self._totaux([self._Doc(200.0, type_doc="avoir")])

        note = resultat["note"].lower()
        assert "anomalie" not in note
        assert "negatif" not in note and "négatif" not in note
        assert "devis" in note, "le périmètre de la requête reste utile à dire"


class TestLaSommeDuDetailEstExacteAuCentime:
    """
    Cinquième passe (Grok, 28/08) : trou ouvert par le gel lui-même.

    La consigne neuve affirme « la somme du détail vaut l'encours ». Mais
    chaque ligne est arrondie seule pendant que le total est arrondi une
    fois : deux documents à 1,004 donnent un total de 2,01 et un détail qui
    somme à 2,00. C'est le centime de la passe 3, sur la paire que je venais
    de déclarer identique - et mon test de la somme n'utilisait que 1 000 et
    -200, qui ne s'arrondissent pas.

    Un test qui choisit des nombres ronds ne teste pas l'arrondi.
    """

    class _Doc:
        def __init__(self, montant, type_doc="facture"):
            self.currency = "EUR"
            self.total_ttc = montant
            self.document_type = type_doc
            self.status = "sent"
            self.due_date = None
            self.invoice_number = f"D-{montant}"
            self.contact = None

    @staticmethod
    def _totaux(documents):
        from datetime import UTC, datetime

        from app.services.workspace_tools import _totaux_des_documents

        return _totaux_des_documents(documents, datetime.now(UTC).replace(tzinfo=None))

    def test_aucun_montant_ne_sort_avec_une_trainee_flottante(self):
        """
        Trou trouvé par sabotage : retirer l'arrondi de l'accumulateur ne
        cassait aucun test, parce que mes cas choisissaient des montants dont
        la somme tombe juste. 0,10 + 0,20 vaut 0.30000000000000004 en
        flottant, et le JSON transmet ce nombre tel quel au modèle, qui
        l'annonce.

        Un test qui choisit des nombres commodes ne teste pas l'arithmétique.
        """
        resultat = self._totaux([self._Doc(0.10), self._Doc(0.20)])

        for champ in ("encours_par_devise", "retard_par_devise", "avoirs_par_devise"):
            for devise, montant in resultat[champ].items():
                assert round(montant, 2) == montant, (
                    f"{champ}[{devise}] = {montant!r} traîne des décimales"
                )
        for ligne in resultat["documents"]:
            assert round(ligne["montant_ttc"], 2) == ligne["montant_ttc"]
        assert resultat["encours_ttc"] == 0.30

    def test_deux_montants_a_1_004(self):
        resultat = self._totaux([self._Doc(1.004), self._Doc(1.004)])
        somme = round(sum(d["montant_ttc"] for d in resultat["documents"]), 2)
        assert somme == resultat["encours_ttc"], (
            f"détail {somme}, encours {resultat['encours_ttc']}"
        )

    def test_deux_montants_a_1_055(self):
        resultat = self._totaux([self._Doc(1.055), self._Doc(1.055)])
        somme = round(sum(d["montant_ttc"] for d in resultat["documents"]), 2)
        assert somme == resultat["encours_ttc"], (
            f"détail {somme}, encours {resultat['encours_ttc']}"
        )

    def test_le_detail_somme_aussi_par_devise(self):
        resultat = self._totaux([self._Doc(1.004), self._Doc(1.004)])
        somme = round(sum(d["montant_ttc"] for d in resultat["documents"]), 2)
        assert somme == resultat["encours_par_devise"]["EUR"]



class TestLeGelNeDoitPasEteindreUnChiffreExact:
    """
    Cinquième passe (Soso, 28/08) : la sur-correction que je lui avais demandé
    de chercher. Il l'a trouvée.

    Le gate du retard lisait les devises de TOUS les documents, pas celles des
    seules factures échues. Cent euros échus à côté de deux cents dollars à
    échéance FUTURE rendaient `retard_ttc: null`, alors que le retard vaut
    exactement 100 EUR : une seule devise est en retard. Et avec plusieurs
    devises mais aucune facture échue, le retard exact est zéro - le code
    rendait null.

    Se taire quand on sait est le symétrique d'affirmer quand on ignore. Les
    quatre passes précédentes ont corrigé le second travers ; celle-ci corrige
    le premier, qu'elles avaient créé.
    """

    class _Doc:
        def __init__(self, montant, devise="EUR", echeance=None, type_doc="facture"):
            self.currency = devise
            self.total_ttc = montant
            self.document_type = type_doc
            self.status = "sent"
            self.due_date = echeance
            self.invoice_number = f"D-{devise}-{montant}"
            self.contact = None

    @staticmethod
    def _totaux(documents):
        from datetime import UTC, datetime

        from app.services.workspace_tools import _totaux_des_documents

        return _totaux_des_documents(documents, datetime.now(UTC).replace(tzinfo=None))

    def test_un_retard_dans_une_seule_devise_est_rendu(self):
        from datetime import UTC, datetime, timedelta

        maintenant = datetime.now(UTC).replace(tzinfo=None)
        resultat = self._totaux(
            [
                self._Doc(100.0, echeance=maintenant - timedelta(days=3)),
                self._Doc(200.0, devise="USD", echeance=maintenant + timedelta(days=30)),
            ]
        )

        assert resultat["retard_ttc"] == 100.0, (
            f"le retard vaut exactement 100 EUR, rendu {resultat['retard_ttc']!r}"
        )
        assert resultat["encours_ttc"] is None, "l'encours, lui, mélange bien deux devises"

    def test_aucune_facture_echue_donne_zero_pas_null(self):
        from datetime import UTC, datetime, timedelta

        maintenant = datetime.now(UTC).replace(tzinfo=None)
        resultat = self._totaux(
            [
                self._Doc(100.0, echeance=maintenant + timedelta(days=10)),
                self._Doc(200.0, devise="USD", echeance=maintenant + timedelta(days=10)),
            ]
        )

        assert resultat["retard_ttc"] == 0, (
            f"« rien n'est en retard » est une réponse exacte : {resultat['retard_ttc']!r}"
        )

    def test_un_retard_reellement_multidevise_reste_null(self):
        """La correction ne doit pas rouvrir ce que la passe 1 a fermé."""
        from datetime import UTC, datetime, timedelta

        maintenant = datetime.now(UTC).replace(tzinfo=None)
        resultat = self._totaux(
            [
                self._Doc(100.0, echeance=maintenant - timedelta(days=3)),
                self._Doc(200.0, devise="USD", echeance=maintenant - timedelta(days=3)),
            ]
        )

        assert resultat["retard_ttc"] is None
        assert resultat["retard_par_devise"] == {"EUR": 100.0, "USD": 200.0}


class TestLeRetardEstBrutEtLeDitFranchement:
    """
    Cinquième passe (Soso, 28/08), second point.

    Une facture de 1 000 EUR échue et un avoir de 200 EUR donnent
    `encours_ttc: 800` et `retard_ttc: 1000`. Le retard dépasse le reste à
    encaisser, ce qui se lit comme une contradiction.

    Ce n'est pas un bug de calcul : un avoir n'est rattaché à aucune facture
    en particulier, et décider qu'il éteint CELLE-CI plutôt qu'une autre
    serait inventer une allocation comptable. Le retard est donc brut, et le
    contrat doit le dire au modèle - sinon il présentera 1 000 comme « la
    part en retard de tes 800 ».

    Nommer le champ n'est pas décorer un chiffre : la description dit ce que
    le nombre EST, elle n'excuse pas ce qu'il n'est pas.
    """

    class _Doc:
        def __init__(self, montant, type_doc="facture", echeance=None):
            self.currency = "EUR"
            self.total_ttc = montant
            self.document_type = type_doc
            self.status = "sent"
            self.due_date = echeance
            self.invoice_number = f"D-{montant}"
            self.contact = None

    def test_le_retard_peut_depasser_l_encours(self):
        from datetime import UTC, datetime, timedelta

        from app.services.workspace_tools import _totaux_des_documents

        maintenant = datetime.now(UTC).replace(tzinfo=None)
        resultat = _totaux_des_documents(
            [
                self._Doc(1000.0, echeance=maintenant - timedelta(days=5)),
                self._Doc(200.0, type_doc="avoir"),
            ],
            maintenant,
        )

        assert resultat["encours_ttc"] == 800.0
        assert resultat["retard_ttc"] == 1000.0

    def test_le_contrat_annonce_que_le_retard_est_avant_avoirs(self):
        """Sans cette phrase, le modèle présente 1 000 comme une part de 800."""
        from app.services.workspace_tools import INVOICE_TOTALS_TOOL

        description = INVOICE_TOTALS_TOOL["function"]["description"].lower()
        assert "avant" in description and "avoir" in description, (
            "le contrat doit dire que retard_ttc est brut, avant avoirs"
        )


class TestLeContratDitExactementCeQueLeCodeFait:
    """
    Sixième passe (Soso, 28/08) : la dernière contradiction, dans les mots.

    Le code rend `retard_ttc: 0` quand rien n'est échu - un zéro exact, la
    correction même de la passe 5. Mais le contrat annoncé au modèle disait
    « ne valent un nombre que s'il y a une seule devise ET un montant
    POSITIF ». Zéro n'est pas positif. Le modèle lit donc qu'un zéro ne
    devrait pas exister, et peut taire une réponse juste.

    Après cinq passes à empêcher THÉRÈSE d'affirmer le faux, la dernière
    faille était de lui faire douter du vrai. Un contrat qui décrit autre
    chose que le code est un mensonge de plus, simplement adressé au modèle
    au lieu de l'utilisateur.
    """

    class _Doc:
        def __init__(self, echeance):
            self.currency = "EUR"
            self.total_ttc = 100.0
            self.document_type = "facture"
            self.status = "sent"
            self.due_date = echeance
            self.invoice_number = "D-100"
            self.contact = None

    def test_le_code_rend_bien_zero(self):
        from datetime import UTC, datetime, timedelta

        from app.services.workspace_tools import _totaux_des_documents

        maintenant = datetime.now(UTC).replace(tzinfo=None)
        resultat = _totaux_des_documents(
            [self._Doc(maintenant + timedelta(days=10))], maintenant
        )
        assert resultat["retard_ttc"] == 0

    def test_le_contrat_de_l_outil_admet_le_zero(self):
        from app.services.workspace_tools import INVOICE_TOTALS_TOOL

        description = INVOICE_TOTALS_TOOL["function"]["description"]
        assert "positif ou nul" in description, (
            "« positif » exclut zéro, que le code rend pourtant : le modèle "
            "lit qu'un zéro ne devrait pas exister et peut le taire"
        )

    def test_le_prompt_de_conversation_dit_la_meme_chose(self):
        """La description et le prompt dynamique doivent s'accorder."""
        import inspect

        from app.routers import chat

        source = inspect.getsource(chat)
        i = source.find("invoice_totals** :")
        assert i != -1
        bloc = source[i : i + 1200]
        assert "positif" not in bloc or "positif ou nul" in bloc, (
            "le prompt dynamique répète la contradiction que la description "
            "vient de corriger"
        )


class TestUneDeviseQuiSAnnuleNeFaitPasTaireLesAutres:
    """
    Sixième passe (Grok, 28/08) : le jumeau du gate retard, que je n'avais pas
    traité en même temps.

    Le gate de l'encours comptait les devises de TOUS les documents. Une
    facture de 100 EUR annulée par un avoir de 100 EUR, à côté d'une facture
    de 500 USD, rendait `encours_ttc: null` - alors que le reste à encaisser
    vaut exactement 500 USD. L'euro qui s'annule restait une seconde devise et
    faisait taire le scalaire.

    J'ai corrigé ce défaut sur le retard à la passe précédente, sans voir
    qu'il existait à l'identique sur l'encours. Corriger un défaut sans
    chercher son jumeau, c'est la moitié du travail - et c'est le motif de
    cette session entière.
    """

    class _Doc:
        def __init__(self, montant, devise="EUR", type_doc="facture"):
            self.currency = devise
            self.total_ttc = montant
            self.document_type = type_doc
            self.status = "sent"
            self.due_date = None
            self.invoice_number = f"D-{devise}-{montant}"
            self.contact = None

    @staticmethod
    def _totaux(documents):
        from datetime import UTC, datetime

        from app.services.workspace_tools import _totaux_des_documents

        return _totaux_des_documents(documents, datetime.now(UTC).replace(tzinfo=None))

    def test_le_cas_exact_de_grok(self):
        resultat = self._totaux(
            [
                self._Doc(100.0),
                self._Doc(100.0, type_doc="avoir"),
                self._Doc(500.0, devise="USD"),
            ]
        )

        assert resultat["encours_ttc"] == 500.0, (
            f"le reste à encaisser vaut exactement 500 USD, rendu "
            f"{resultat['encours_ttc']!r}"
        )
        assert resultat["devise"] == "USD", "et il est libellé sans ambiguïté"

    def test_tout_s_annule_donne_zero(self):
        resultat = self._totaux(
            [self._Doc(100.0), self._Doc(100.0, type_doc="avoir")]
        )

        assert resultat["encours_ttc"] == 0, "« plus rien à encaisser » est exact"

    def test_deux_devises_reellement_dues_se_taisent_toujours(self):
        """La correction ne doit pas rouvrir ce que la passe 1 a fermé."""
        resultat = self._totaux(
            [self._Doc(1000.0), self._Doc(500.0, devise="USD")]
        )

        assert resultat["encours_ttc"] is None
        assert resultat["encours_par_devise"] == {"EUR": 1000.0, "USD": 500.0}


class TestLesEtiquettesNeContredisentPasLesNombres:
    """
    Septième passe : ma propre chasse aux symétries, après trois jumeaux
    manqués. Deux défauts, tous deux introduits par mes correctifs.

    A. `devises_multiples` restait calculé sur TOUS les documents. Une facture
       de 100 EUR annulée par un avoir, à côté de 500 USD, rendait
       `encours_ttc: 500`, `devise: "USD"` ET `devises_multiples: true`. Le
       modèle lit « plusieurs devises » à côté d'un total unique libellé dans
       une seule. Le gate a suivi la règle à la passe 6, le drapeau qui le
       décrit ne l'a pas suivie.

    B. `nombre` comptait les factures pendant que la liste `factures[]` porte
       désormais aussi les avoirs. Un résultat annonçait « 1 » avec deux
       lignes en dessous. C'est le prix du correctif de la passe 5, que je
       n'ai pas payé au moment de le poser : la liste a changé de contenu,
       son étiquette et son compteur sont restés.
    """

    class _Doc:
        def __init__(self, montant, devise="EUR", type_doc="facture"):
            self.currency = devise
            self.total_ttc = montant
            self.document_type = type_doc
            self.status = "sent"
            self.due_date = None
            self.invoice_number = f"{devise}-{montant}"
            self.contact = None

    @staticmethod
    def _totaux(documents):
        from datetime import UTC, datetime

        from app.services.workspace_tools import _totaux_des_documents

        return _totaux_des_documents(documents, datetime.now(UTC).replace(tzinfo=None))

    def test_le_drapeau_des_devises_suit_le_scalaire(self):
        resultat = self._totaux(
            [
                self._Doc(100.0),
                self._Doc(100.0, type_doc="avoir"),
                self._Doc(500.0, devise="USD"),
            ]
        )

        assert resultat["encours_ttc"] == 500.0
        assert resultat["devises_multiples"] is False, (
            "« plusieurs devises » à côté d'un total unique libellé USD : le "
            "modèle doit choisir laquelle des deux annonces croire"
        )

    def test_une_devise_sans_rien_a_encaisser_quitte_la_liste(self):
        """Un euro à zéro n'est pas une créance : il n'a rien à faire dans
        une table de ce qui reste à encaisser."""
        resultat = self._totaux(
            [
                self._Doc(100.0),
                self._Doc(100.0, type_doc="avoir"),
                self._Doc(500.0, devise="USD"),
            ]
        )

        assert resultat["encours_par_devise"] == {"USD": 500.0}

    def test_le_compteur_compte_ce_que_la_liste_contient(self):
        resultat = self._totaux(
            [self._Doc(1000.0), self._Doc(200.0, type_doc="avoir")]
        )

        assert len(resultat["documents"]) == 2
        assert resultat["nombre"] == 1, "une seule FACTURE impayée"
        assert resultat["nombre_avoirs"] == 1
        assert resultat["nombre_documents"] == len(resultat["documents"])

    def test_le_drapeau_reste_vrai_quand_deux_devises_sont_dues(self):
        """La correction ne doit pas éteindre le drapeau quand il est utile."""
        resultat = self._totaux([self._Doc(1000.0), self._Doc(500.0, devise="USD")])

        assert resultat["devises_multiples"] is True
        assert resultat["encours_ttc"] is None


class TestLaRegleEstBalayeeSurTousLesChamps:
    """
    Septième passe, retour de Grok : deux jumeaux de plus, sur les deux
    derniers champs que je n'avais pas balayés.

    A. La `note` affirmait « Plusieurs devises : aucun total global n'est
       calculable » pendant que `devises_multiples` valait false et que
       `encours_ttc` valait 500. J'ai fait suivre la règle au DRAPEAU à la
       passe 7 ; la PHRASE qui dit la même chose lisait toujours toutes les
       devises des documents.

    B. `retard_par_devise` n'avait pas le filtre `m > 0` que je venais de
       poser sur `encours_par_devise`. Une facture à 0 EUR échue à côté de
       500 USD échue laissait `{EUR: 0.0, USD: 500.0}` et faisait taire
       `retard_ttc`, alors que `encours_ttc` rendait bien 500.

    Quatrième et cinquième jumeaux de la session. Le motif est constant :
    poser une règle sur un champ et ne pas la balayer sur les autres.
    """

    class _Doc:
        def __init__(self, montant, devise="EUR", type_doc="facture", echeance=None):
            self.currency = devise
            self.total_ttc = montant
            self.document_type = type_doc
            self.status = "sent"
            self.due_date = echeance
            self.invoice_number = f"{devise}-{montant}"
            self.contact = None

    @staticmethod
    def _totaux(documents):
        from datetime import UTC, datetime

        from app.services.workspace_tools import _totaux_des_documents

        return _totaux_des_documents(documents, datetime.now(UTC).replace(tzinfo=None))

    def test_la_note_ne_contredit_pas_le_total_rendu(self):
        resultat = self._totaux(
            [
                self._Doc(100.0),
                self._Doc(100.0, type_doc="avoir"),
                self._Doc(500.0, devise="USD"),
            ]
        )

        assert resultat["encours_ttc"] == 500.0
        assert "aucun total global" not in resultat["note"].lower(), (
            f"la note nie le total que le champ à côté vient de rendre : "
            f"{resultat['note']!r}"
        )

    def test_la_note_previent_toujours_quand_le_total_manque(self):
        """La correction ne doit pas rendre la note muette quand elle est utile."""
        resultat = self._totaux(
            [self._Doc(1000.0), self._Doc(500.0, devise="USD")]
        )

        assert resultat["encours_ttc"] is None
        assert "aucun total global" in resultat["note"].lower()

    def test_le_retard_par_devise_a_le_meme_filtre_que_l_encours(self):
        from datetime import UTC, datetime, timedelta

        maintenant = datetime.now(UTC).replace(tzinfo=None)
        resultat = self._totaux(
            [
                self._Doc(0.0, echeance=maintenant - timedelta(days=3)),
                self._Doc(500.0, devise="USD", echeance=maintenant - timedelta(days=3)),
            ]
        )

        assert resultat["retard_par_devise"] == {"USD": 500.0}, (
            "un retard de zéro euro n'est pas un retard"
        )
        assert resultat["retard_ttc"] == 500.0, (
            f"une seule devise est réellement en retard : {resultat['retard_ttc']!r}"
        )


class TestLeGateDuRetardLitLeMemeEnsembleQueLEncours:
    """
    Huitième passe : le jumeau que le correctif de `retard_par_devise`
    a lui-même posé.

    L'encours a DEUX ensembles, à dessein :
      * `encours_par_devise` ne garde que `m > 0` (rien de nommé encours
        ne porte un zéro ni un négatif) ;
      * le gate du scalaire lit `devises_avec_encours`, `m != 0` : un
        avoir en dollars à côté d'une facture en euros doit faire taire
        le total, parce que la somme traverse encore les deux devises.

    La passe précédente a collé le gate du retard sur le dict filtré
    `m > 0`. Un zéro ne fait plus taire (c'était le but). Un négatif
    non plus : facture à -100 EUR échue à côté de 500 USD échue rendait
    `retard_ttc: 400`, un chiffre qui n'existe dans aucune des deux,
    pendant que `encours_ttc` valait null sur le même dossier. Même
    règle, mauvais ensemble.
    """

    class _Doc:
        def __init__(self, montant, devise="EUR", type_doc="facture", echeance=None):
            self.currency = devise
            self.total_ttc = montant
            self.document_type = type_doc
            self.status = "sent"
            self.due_date = echeance
            self.invoice_number = f"{devise}-{montant}"
            self.contact = None

    @staticmethod
    def _totaux(documents, maintenant=None):
        from datetime import UTC, datetime

        from app.services.workspace_tools import _totaux_des_documents

        if maintenant is None:
            maintenant = datetime.now(UTC).replace(tzinfo=None)
        return _totaux_des_documents(documents, maintenant)

    def test_un_negatif_dans_une_autre_devise_fait_taire_le_retard(self):
        from datetime import UTC, datetime, timedelta

        maintenant = datetime.now(UTC).replace(tzinfo=None)
        passe = maintenant - timedelta(days=3)
        resultat = self._totaux(
            [
                self._Doc(-100.0, echeance=passe),
                self._Doc(500.0, devise="USD", echeance=passe),
            ],
            maintenant,
        )

        assert resultat["encours_ttc"] is None, (
            "l'encours, lui, mélange bien deux devises"
        )
        assert resultat["retard_par_devise"] == {"USD": 500.0}, (
            "le négatif ne vit pas sous un nom qui promet une somme à recouvrer"
        )
        assert resultat["retard_ttc"] is None, (
            f"400 n'existe ni en EUR ni en USD : {resultat['retard_ttc']!r}"
        )

    def test_un_zero_ne_fait_toujours_pas_taire(self):
        """La correction ne doit pas rouvrir le filtre m > 0 de la passe précédente."""
        from datetime import UTC, datetime, timedelta

        maintenant = datetime.now(UTC).replace(tzinfo=None)
        passe = maintenant - timedelta(days=3)
        resultat = self._totaux(
            [
                self._Doc(0.0, echeance=passe),
                self._Doc(500.0, devise="USD", echeance=passe),
            ],
            maintenant,
        )

        assert resultat["retard_ttc"] == 500.0
        assert resultat["retard_par_devise"] == {"USD": 500.0}
