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
        assert resultat["retard_ttc"] is None, "même règle pour le retard"
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

        assert resultat["factures"], "la facture posée doit apparaître"
        assert resultat["factures"][0]["devise"] == "EUR", (
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
        assert resultat["encours_par_devise"].get("USD") != -200.0 or (
            "avoir" in resultat["note"].lower()
        ), "si le net reste négatif, la note doit dire que ce n'est pas à encaisser"


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
        assert "avoir" in resultat["note"].lower(), (
            "-200 USD dans un champ nommé « encours » se lit comme une somme "
            "à encaisser ; la note doit dire que c'est dû au client"
        )


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

        assert resultat["avoirs_par_devise"]["EUR"] == -resultat["encours_par_devise"]["EUR"], (
            f"{resultat['avoirs_par_devise']} vs {resultat['encours_par_devise']}"
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
        assert resultat["encours_par_devise"]["EUR"] == -100.0
        note = resultat["note"].lower()
        assert "anomalie" in note, f"note muette sur un encours négatif : {note!r}"
        assert "est un avoir" not in note, (
            "aucun avoir n'existe : appeler ce montant un avoir donne une "
            "explication fausse à un chiffre faux"
        )


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

        somme = round(sum(d["montant_ttc"] for d in resultat["factures"]), 2)
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

        assert resultat["factures"][0]["type"] == "avoir"
        assert resultat["factures"][0]["montant_ttc"] == -200.0, (
            "un avoir listé positivement se resomme comme une créance"
        )

