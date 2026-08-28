"""Le garde de la recherche web est au niveau de la SORTIE, pas du chat.

Campagne dix personas du 28/08. Trois personas dont le métier l'exige (avocat,
médecin, magistrate) ont trouvé que leurs questions partaient sur Internet sans
qu'on le leur dise. La magistrate avait même demandé explicitement d'attendre sa
confirmation : la requête est partie quand même.

La préférence `web_search_enabled` existait déjà en base. Elle n'était lue qu'à
UN endroit — `chat.py`, pour décider si l'outil est proposé au modèle. Le garde
était donc au mauvais étage : Board, recherche approfondie et Atelier appellent
le service directement (18 appels, zéro lecture du réglage) et le
contournaient.

Ce module vérifie que le garde est descendu au niveau du service : quel que
soit l'appelant, connu ou pas encore écrit, aucune requête ne part sans
autorisation.
"""
import pytest
from app.services import web_search


@pytest.fixture(autouse=True)
def _reinitialiser_le_cache():
    """Le garde met la préférence en cache, comme la clé Brave."""
    web_search.poser_autorisation_recherche(None)
    yield
    web_search.poser_autorisation_recherche(None)


class TestGardeAuNiveauDuService:
    """Le garde protège la sortie réseau, pas une liste d'outils."""

    def test_le_garde_laisse_passer_quand_la_recherche_est_autorisee(self):
        web_search.poser_autorisation_recherche(True)
        # Ne lève pas.
        web_search.verifier_autorisation_recherche()

    def test_le_garde_refuse_quand_la_recherche_est_coupee(self):
        web_search.poser_autorisation_recherche(False)
        with pytest.raises(web_search.RechercheWebRefusee):
            web_search.verifier_autorisation_recherche()

    def test_le_defaut_reste_autorise(self):
        """Décision de la relecture : ne pas changer le comportement existant.

        Les trois personas sont partis sur un MENSONGE (l'écran affirmait que
        rien ne sortait), pas sur un défaut allumé. Une fois que l'interrupteur
        coupe vraiment et que l'écran le dit, ils peuvent l'éteindre. Passer le
        défaut à « éteint » priverait de recherche, du jour au lendemain et
        sans trace d'un choix, un boulanger ou un plombier qui n'ont rien
        demandé.
        """
        web_search.poser_autorisation_recherche(None)
        web_search.verifier_autorisation_recherche()

    def test_l_exception_dit_ou_reactiver(self):
        """L'erreur doit être lisible par l'utilisateur, pas un code."""
        web_search.poser_autorisation_recherche(False)
        with pytest.raises(web_search.RechercheWebRefusee) as capture:
            web_search.verifier_autorisation_recherche()
        message = str(capture.value)
        assert "Réglages" in message and "Services" in message

    def test_l_exception_se_distingue_d_une_panne_reseau(self):
        """Board et la recherche approfondie avalent les erreurs réseau.

        Sans un type distinct, un refus deviendrait « aucun résultat » et
        l'utilisateur croirait que le web n'a rien trouvé.
        """
        assert issubclass(web_search.RechercheWebRefusee, Exception)
        assert not issubclass(web_search.RechercheWebRefusee, OSError)


class TestTousLesMoteursSontGardes:
    """Les trois moteurs, pas seulement celui du chat."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize("classe", ["BraveSearchService", "WebSearchService", "SearXNGService"])
    async def test_chaque_moteur_refuse_de_chercher(self, classe):
        web_search.poser_autorisation_recherche(False)
        fabrique = {
            "BraveSearchService": lambda: web_search.BraveSearchService("clef-de-test"),
            "WebSearchService": lambda: web_search.WebSearchService(),
            "SearXNGService": lambda: web_search.SearXNGService("http://exemple.test"),
        }[classe]
        service = fabrique()
        with pytest.raises(web_search.RechercheWebRefusee):
            await service.search("une question qui ne doit pas partir")


class TestLaPreferenceEstChargeeEtSuivie:
    """Le cache doit refléter la base, au démarrage et à chaque changement.

    Copie du motif de la clé Brave (`set_brave_api_key`) : sans cela, le
    service ferait une requête SQL par recherche, ou l'interrupteur aurait un
    coup de retard.
    """

    def test_le_demarrage_charge_la_preference(self):
        """`main.py` doit poser l'autorisation au lifespan, comme la clé Brave."""
        import inspect

        from app import main

        source = inspect.getsource(main)
        assert "poser_autorisation_recherche" in source, (
            "le démarrage doit charger web_search_enabled dans le cache du service"
        )

    def test_changer_le_reglage_met_le_cache_a_jour(self):
        """Le POST qui bascule l'interrupteur doit prévenir le service."""
        import inspect

        from app.routers import config as routeur_config

        source = inspect.getsource(routeur_config)
        assert "poser_autorisation_recherche" in source, (
            "POST /config/web-search doit poser l'autorisation dans le service, "
            "sinon l'interrupteur ne prend effet qu'au prochain démarrage"
        )


class TestUnRefusNeSeDeguiseJamaisEnPanne:
    """Le point le plus fin, relevé par la relecture de design.

    Board fait `except Exception: return ""` et la recherche approfondie
    utilise `return_exceptions=True`. Sans traitement distinct, un refus
    deviendrait « aucun résultat » : l'utilisateur croirait que le web n'a rien
    trouvé au lieu de comprendre qu'il l'a coupé — un mensonge de plus, dans le
    chantier qui existe pour les faire cesser.
    """

    def test_board_distingue_le_refus_d_une_panne(self):
        import inspect

        from app.services import board

        source = inspect.getsource(board)
        assert "RechercheWebRefusee" in source, (
            "Board doit rattraper RechercheWebRefusee AVANT son except Exception, "
            "sinon un refus s'affiche comme « aucun résultat »"
        )

    def test_la_recherche_approfondie_distingue_aussi(self):
        import inspect

        from app.services import deep_research

        source = inspect.getsource(deep_research)
        assert "RechercheWebRefusee" in source, (
            "la recherche approfondie doit dire qu'elle a été refusée, pas se taire"
        )

    @pytest.mark.asyncio
    async def test_la_navigation_web_est_gardee_comme_la_recherche(self):
        """`browser_navigate` sort aussi sur le réseau."""
        web_search.poser_autorisation_recherche(False)
        resultat = await web_search.execute_browser_action({"action": "navigate", "url": "http://exemple.test"})
        assert "désactivée" in resultat.lower() or "réglages" in resultat.lower()

    @pytest.mark.asyncio
    async def test_l_outil_de_chat_dit_pourquoi_il_ne_cherche_pas(self):
        """Le modèle doit pouvoir l'expliquer, pas inventer une panne."""
        web_search.poser_autorisation_recherche(False)
        resultat = await web_search.execute_web_search({"query": "peu importe"})
        assert "réglages" in resultat.lower()


class TestLAncrageGoogleSuitLeMemeInterrupteur:
    """Gemini cherche par son fournisseur, sans passer par notre service.

    `gemini.py` active l'ancrage Google Search par défaut. Ce chemin ne
    traverse ni `web_search.py` ni l'outil du chat : couper l'interrupteur
    laissait donc Gemini interroger Google.

    Relecture de design : « Couper le service et laisser Gemini chercher, c'est
    le même mensonge d'étage, côté fournisseur. » L'interrupteur doit valoir
    pour lui aussi — et l'écran doit le dire, ce qui est fait dans le même lot.

    On ne câble PAS chaque appelant (le chat, le Board, et le prochain qu'on
    oubliera) : la décision descend dans le fournisseur, comme le garde est
    descendu dans le service.
    """

    def test_l_ancrage_est_coupe_quand_la_recherche_l_est(self):
        import inspect

        from app.services.providers import gemini

        source = inspect.getsource(gemini)
        assert "recherche_web_autorisee" in source, (
            "l'ancrage Google doit suivre la préférence de recherche web, "
            "sinon l'interrupteur ment sur Gemini"
        )

    def test_le_calcul_de_l_ancrage_combine_les_deux_conditions(self):
        """L'appelant garde son mot à dire, la préférence a le dernier.

        On lit le bloc d'affectation entier, pas une ligne : le calcul tient
        sur plusieurs lignes et un test ligne-à-ligne casserait au premier
        reformatage sans rien prouver de plus.
        """
        import inspect

        from app.services.providers.gemini import GeminiProvider

        source = inspect.getsource(GeminiProvider.stream)
        assert "grounding_ok" in source, "grounding_ok doit être calculé dans stream()"

        debut = source.index("grounding_ok")
        bloc = source[debut : source.index("if declarations", debut)]
        assert "enable_grounding" in bloc, "l'appelant garde son mot à dire"
        assert "recherche_web_autorisee" in bloc, (
            "grounding_ok doit tenir compte de la préférence utilisateur"
        )
