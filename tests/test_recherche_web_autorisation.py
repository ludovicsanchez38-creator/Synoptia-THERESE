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

    @pytest.mark.asyncio
    async def test_la_recherche_approfondie_dit_le_refus_a_l_ecran(self):
        """On EXÉCUTE le générateur réel, on ne lit pas la source.

        Le premier jet de ce test cherchait « RechercheWebRefusee » dans le
        module. Il était vert — parce que le nom se trouvait dans
        `search_parallel`, une fonction que PERSONNE n'appelle. Pendant ce
        temps, le générateur vivant avalait le refus dans son `except
        Exception` et affichait « Aucun résultat trouvé. Vérifie ta clé Brave
        Search ». Un utilisateur qui vient de couper l'interrupteur lisait donc
        qu'il avait un problème de clé API.

        Un test qui lit du code mort est pire qu'une absence de test : il
        rassure. Celui-ci consomme les événements que l'écran affiche.
        """
        from app.services.deep_research import deep_research as recherche_approfondie

        web_search.poser_autorisation_recherche(False)

        class _ModeleMuet:
            async def generate_content(self, *args, **kwargs):
                return "sous-question 1"

        evenements = []
        async for progression in recherche_approfondie(
            "une question", _ModeleMuet(), max_queries=1
        ):
            evenements.append(progression)

        erreurs = [e for e in evenements if getattr(e, "type", None) == "error"]
        assert erreurs, "un refus doit produire un événement d'erreur visible"

        texte = " ".join(getattr(e, "content", "") or "" for e in erreurs)
        assert "Brave" not in texte, (
            "ne pas envoyer l'utilisateur vérifier une clé API alors qu'il a "
            "lui-même coupé la recherche web"
        )
        assert "Réglages" in texte or "coupée" in texte.lower(), (
            f"le message doit dire que la recherche est coupée. Reçu : {texte!r}"
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


class TestAucunAppelantNEchappeAuGarde:
    """Inventaire : tout code qui obtient un service de recherche doit traiter
    le refus explicitement, sinon il le déguise en panne.

    Recensé à la main le 28/08 : `board.py`, `deep_research.py` (deux chemins :
    parallèle et avec progression) et `agents/tools.py`. Le chat passe par
    `execute_web_search`, gardé lui aussi.
    """

    @pytest.mark.parametrize(
        "module",
        ["app.services.board", "app.services.deep_research", "app.services.agents.tools"],
    )
    def test_chaque_appelant_traite_le_refus(self, module):
        import importlib
        import inspect

        source = inspect.getsource(importlib.import_module(module))
        # On cherche la CLAUSE, pas le mot : l'import contient déjà le nom, et
        # un test qui se contente de le trouver reste vert quand le `except`
        # disparaît. (Trouvé par la preuve par sabotage.)
        assert "except RechercheWebRefusee" in source, (
            f"{module} obtient un service de recherche sans RATTRAPER un refus : "
            "il le laisserait tomber dans son except générique et l'utilisateur "
            "croirait que le web n'a rien trouvé"
        )

    def test_les_deux_chemins_de_la_recherche_approfondie_sont_couverts(self):
        """Le module a DEUX points d'appel, traités différemment.

        Le premier lance les recherches en parallèle (`asyncio.gather` avec
        `return_exceptions=True`) : le refus arrive comme une VALEUR, il se
        teste par `isinstance`. Le second est un générateur de progression :
        le refus arrive comme une exception, il se rattrape par `except`.

        Le second avait été oublié à la première passe — d'où ce test qui
        vérifie les deux zones séparément, plutôt qu'un comptage global qui
        aurait été vert avec deux fois la même forme.
        """
        import inspect

        from app.services import deep_research

        source = inspect.getsource(deep_research)
        separateur = "# Étape 2 : Recherches parallèles (avec progression)"
        assert separateur in source, "repère de découpage introuvable"

        chemin_parallele, chemin_progression = source.split(separateur, 1)

        assert "isinstance(resp, RechercheWebRefusee)" in chemin_parallele, (
            "le chemin parallèle doit reconnaître le refus parmi les valeurs "
            "renvoyées par gather(return_exceptions=True)"
        )
        assert "except RechercheWebRefusee" in chemin_progression, (
            "le chemin avec progression doit rattraper le refus avant son "
            "except générique, sinon le rapport sort vide sans explication"
        )


class TestLaRechercheApprofondieDemarre:
    """Bug préexistant révélé par le test ci-dessus, hors périmètre initial.

    `deep_research()` et `decompose_question()` importent `LLMMessage` depuis
    `app.services.providers`. Ce nom n'existe pas : la classe s'appelle
    `Message`. L'import est la PREMIÈRE ligne exécutable du générateur — la
    recherche approfondie plantait donc avant même de commencer, à chaque
    appel, alors qu'elle est atteignable depuis l'écran
    (`ChatInput.tsx` → `POST /api/chat/deep-research`).

    Personne ne l'avait vu parce qu'aucun test n'exécutait le générateur : ils
    lisaient sa source. C'est la deuxième leçon du jour sur les tests qui
    rassurent au lieu de vérifier.
    """

    def test_les_imports_du_module_existent_vraiment(self):
        from app.services import providers

        assert hasattr(providers, "Message"), "la classe s'appelle bien Message"
        assert not hasattr(providers, "LLMMessage"), (
            "si LLMMessage apparaît un jour, ce test doit être revu plutôt que "
            "supprimé : c'est lui qui a attrapé l'import fantôme"
        )

    @pytest.mark.asyncio
    async def test_le_generateur_demarre_sans_ImportError(self):
        from app.services.deep_research import deep_research as recherche_approfondie

        web_search.poser_autorisation_recherche(False)

        class _ModeleMuet:
            async def generate_content(self, *args, **kwargs):
                return "sous-question"

        # On consomme au moins un événement : si l'import est cassé, l'appel
        # lève ImportError avant le premier yield.
        agen = recherche_approfondie("question", _ModeleMuet(), max_queries=1)
        premier = await agen.__anext__()
        assert premier is not None
        await agen.aclose()
