"""Frontière d'erreurs utilisateur (lot C, 0.48).

PAS un second système : error_handler.py existant, étendu. À la limite de
l'écran (SSE, notification, HTTP, task.error), seuls les messages
localisés passent - jamais str(e) brut. Le technique va aux logs.
"""

import pytest


class TestLeMessagePourEcran:
    def test_therese_error_passe_son_message_utilisateur(self):
        from app.services.error_handler import (
            ErrorCode,
            TheresError,
            message_pour_ecran,
        )

        exc = TheresError(
            ErrorCode.API_AUTH_FAILED,
            "401 unauthorized sk-xxx",
            context={"provider": "OpenAI"},
        )
        assert message_pour_ecran(exc) == exc.user_message
        assert "sk-xxx" not in message_pour_ecran(exc)

    def test_une_exception_brute_devient_generique(self):
        from app.services.error_handler import message_pour_ecran

        msg = message_pour_ecran(KeyError("colonne_interne_42"))
        assert "colonne_interne_42" not in msg
        assert "KeyError" not in msg
        # Un message français lisible, pas une chaîne vide
        assert len(msg) > 20

    def test_le_cas_inconnu_ne_reinjecte_plus_le_technique(self):
        """Le template UNKNOWN_ERROR affichait « Détails techniques: {error} »."""
        from app.services.error_handler import ErrorCode, TheresError

        exc = TheresError(ErrorCode.UNKNOWN_ERROR, "KeyError('secret_interne')")
        assert "secret_interne" not in exc.user_message
        assert "KeyError" not in exc.user_message

    def test_le_contexte_lisible_precede_le_generique(self):
        from app.services.error_handler import message_pour_ecran

        msg = message_pour_ecran(RuntimeError("boom"), ou="pendant la délibération")
        assert "pendant la délibération" in msg
        assert "boom" not in msg


class TestLesEmetteursNExposentPlusLeBrut:
    """Verrouillage : les sites listés au design n'émettent plus str(e)."""

    def test_board_sse_sans_str_e(self):
        import inspect

        from app.routers import board as board_router

        source = inspect.getsource(board_router)
        assert '"content": str(' not in source, (
            "un chunk SSE du board émet encore str(e) brut vers l'écran"
        )

    def test_runtime_agent_event_sans_exception_brute(self):
        import inspect

        from app.services.agents import runtime

        source = inspect.getsource(runtime)
        assert 'content=f"Erreur LLM : {e}"' not in source

    def test_action_agents_task_error_sans_exception_brute(self):
        import inspect

        from app.services import action_agents

        source = inspect.getsource(action_agents)
        assert 'task.error = f"Erreur LLM : {e}"' not in source


class TestLaRouteImages:
    def test_cle_manquante_reste_un_message_intentionnel(self, client, monkeypatch):
        """Les messages écrits POUR l'utilisateur (clé API manquante)
        traversent la frontière tels quels - via TheresError."""
        for var in ("OPENAI_IMAGE_API_KEY", "OPENAI_API_KEY"):
            monkeypatch.delenv(var, raising=False)
        reponse = client.post(
            "/api/images/generate",
            json={"prompt": "un chat", "provider": "gpt-image-2"},
        )
        assert reponse.status_code == 400
        detail = reponse.json()["message"]
        assert "Clé API" in detail

    def test_erreur_technique_ne_fuit_pas(self, client, monkeypatch):
        """Une exception imprévue du générateur ne montre pas son texte brut."""
        from app.services.image_generator import get_image_service

        async def _explose(*a, **k):
            raise RuntimeError("stack interne x8_technique")

        monkeypatch.setattr(
            type(get_image_service()), "generate", _explose
        )
        reponse = client.post(
            "/api/images/generate",
            json={"prompt": "un chat", "provider": "gpt-image-2"},
        )
        assert reponse.status_code == 500
        assert "x8_technique" not in reponse.json()["message"]


class TestLaFrontiereEstTotale:
    """Revue 0.48 (F4) : la migration était partielle - l'enveloppe
    terminale des actions, les étapes, la recopie AgentEvent et le catch
    du chat exposaient encore str(e). Repro de la revue : un RuntimeError
    portant un secret et un chemin local ressortait dans task.error."""

    @pytest.mark.asyncio
    async def test_l_enveloppe_terminale_ne_fuit_pas_le_brut(
        self, client, monkeypatch
    ):
        import asyncio

        from app.services import action_agents as module
        from app.services.action_agents import ActionRunner, TaskStatus

        async def contexte_qui_fuit(_tools):
            raise RuntimeError("sk-secret /Users/ludo/interne")

        monkeypatch.setattr(module, "_gather_local_context", contexte_qui_fuit)

        task = await ActionRunner.run("rapport-hebdo")
        for _ in range(100):
            if ActionRunner.get_task(task.task_id).status == TaskStatus.ERROR:
                break
            await asyncio.sleep(0.05)
        etat = ActionRunner.get_task(task.task_id)
        assert etat.status == TaskStatus.ERROR
        assert etat.error, "une erreur lisible doit être consignée"
        assert "sk-secret" not in etat.error
        assert "/Users/ludo" not in etat.error
        assert "sk-secret" not in str(etat.to_dict())

    def test_aucun_site_str_e_dans_les_enveloppes(self):
        """Verrouillage structurel : les écritures d'erreur des actions et
        des étapes passent par la frontière, plus par str(e)."""
        import inspect

        from app.services import action_agents

        source = inspect.getsource(action_agents)
        assert "task.error = str(e)" not in source
        assert "step_result.error = str(e)" not in source

    def test_la_recopie_agent_event_passe_la_frontiere(self):
        import inspect

        from app.services.agents import runtime

        source = inspect.getsource(runtime)
        assert (
            'yield AgentEvent(type="error", content=event.content or "Erreur LLM")'
            not in source
        ), "runtime recopie encore le contenu d'erreur provider brut"

    def test_le_catch_du_chat_ne_fuit_pas_str_e(self):
        import inspect

        from app.routers import chat

        source = inspect.getsource(chat)
        assert 'content=f"Erreur de generation: {str(e)}"' not in source
        assert 'f"⚠️ Erreur de génération: {str(e)}"' not in source


class TestLaRouteImagesTechnique:
    def test_value_error_technique_ne_fuit_pas(self, client, monkeypatch):
        """Le générateur lève aussi ValueError pour du technique anglais
        (« No image data in response ») - la route ne doit relayer que les
        messages INTENTIONNELS (TheresError), pas tout ValueError."""
        from app.services.image_generator import get_image_service

        async def _explose(*a, **k):
            raise ValueError("No image data in response x9_interne")

        monkeypatch.setattr(type(get_image_service()), "generate", _explose)
        reponse = client.post(
            "/api/images/generate",
            json={"prompt": "un chat", "provider": "gpt-image-2"},
        )
        assert reponse.status_code >= 400
        assert "x9_interne" not in reponse.json()["message"]


class TestLesMessagesIntentionnelsTraversent:
    """Revue 0.48 (F5) : le Board lève des RuntimeError aux messages
    français écrits POUR l'utilisateur (« Mode souverain indisponible... »).
    La frontière les transformait en générique - l'utilisateur perdait la
    cause et l'action corrective. ErreurPourEcran marque l'intention."""

    def test_erreur_pour_ecran_traverse_la_frontiere(self):
        from app.services.error_handler import ErreurPourEcran, message_pour_ecran

        exc = ErreurPourEcran(
            "Mode souverain indisponible : aucun service Ollama local utilisable."
        )
        assert message_pour_ecran(exc) == (
            "Mode souverain indisponible : aucun service Ollama local utilisable."
        )

    def test_erreur_pour_ecran_reste_un_runtime_error(self):
        """Compat : les pytest.raises(RuntimeError) existants du Board."""
        from app.services.error_handler import ErreurPourEcran

        assert issubclass(ErreurPourEcran, RuntimeError)

    def test_les_messages_du_board_sont_marques(self):
        """Structurel : plus aucun RuntimeError NU à message utilisateur
        dans board.py - ils portent tous la marque ErreurPourEcran."""
        import inspect

        from app.services import board

        source = inspect.getsource(board)
        assert "raise RuntimeError(" not in source, (
            "un message intentionnel du Board serait masqué par la frontière"
        )


class TestLesProvidersNEmettentPasLeBrut:
    """Revue 0.48 passe 2 (F1) : le catch générique des providers émettait
    content=str(e) - la fuite remontait telle quelle au SSE du chat, au
    Board et à l'Atelier. La forme construite « API error: NNN » reste ;
    le str(e) va aux logs, l'évènement porte une forme sobre."""

    def test_aucun_provider_n_emet_str_e(self):
        import inspect

        from app.services.providers import (
            anthropic,
            deepseek,
            gemini,
            infomaniak,
            mistral,
            ollama,
            openai,
            openrouter,
            perplexity,
        )

        fautifs = []
        for module in (anthropic, deepseek, gemini, infomaniak, mistral,
                       ollama, openai, openrouter, perplexity):
            if "content=str(e)" in inspect.getsource(module):
                fautifs.append(module.__name__)
        assert fautifs == [], f"providers émettant str(e) brut : {fautifs}"

    @pytest.mark.asyncio
    async def test_un_crash_local_ne_fuit_pas_dans_l_event(self, monkeypatch):
        import httpx
        from app.services.providers.base import LLMConfig, LLMProvider
        from app.services.providers.openai import OpenAIProvider

        provider = OpenAIProvider(
            LLMConfig(provider=LLMProvider.OPENAI, model="gpt-5.6-sol", api_key="k"),
            client=httpx.AsyncClient(),
        )

        def stream_qui_crash(*a, **k):
            raise RuntimeError("sk-secret /Users/ludo/interne")

        monkeypatch.setattr(provider.client, "stream", stream_qui_crash)
        events = [e async for e in provider.stream(None, [{"role": "user", "content": "x"}], None)]
        erreurs = [e for e in events if e.type == "error"]
        assert erreurs, "un évènement d'erreur doit être émis"
        assert all("sk-secret" not in (e.content or "") for e in erreurs)
        assert all("/Users/ludo" not in (e.content or "") for e in erreurs)

    def test_les_sites_chat_et_agents_sont_fermes(self):
        import inspect

        from app.routers import agents as agents_router
        from app.routers import chat as chat_router

        assert "s'est produite: {str(e)}" not in inspect.getsource(chat_router)
        source_agents = inspect.getsource(agents_router)
        assert 'content=f"Erreur : {e}"' not in source_agents


class TestLeBoardNAvalePlusLesErreursDeFlux:
    """Revue 0.48 passe 2 (F2) : stream_response ignorait les
    StreamEvent(error) par défaut - un circuit ouvert entre le
    préchargement et l'appel donnait un avis VIDE validé, synthétisé et
    sauvegardé. Le Board exige désormais raise_on_error, et l'échec d'un
    conseiller garde son message précis dans l'erreur finale."""

    @pytest.mark.asyncio
    async def test_un_avis_en_erreur_n_est_jamais_valide_vide(self, monkeypatch):
        import contextlib
        from types import SimpleNamespace

        from app.models.board import AdvisorRole, BoardMode, BoardRequest
        from app.services import board as board_module
        from app.services.board import BoardService
        from app.services.llm import LLMProvider

        class LLMEnPanne:
            config = SimpleNamespace(provider=LLMProvider.OPENAI, model="modele-test")

            def prepare_context(self, messages, system_prompt=None):
                return messages, system_prompt

            async def stream_response(self, context, usage_sink=None, raise_on_error=False):
                # Le contrat : le Board DOIT demander raise_on_error
                assert raise_on_error is True, (
                    "le Board doit exiger raise_on_error=True - sans lui, un "
                    "StreamEvent(error) donne un avis vide validé"
                )
                raise RuntimeError("API error: 503")
                yield  # pragma: no cover

        class FakeSession:
            def add(self, _v):
                pass

            async def commit(self):
                pass

            async def rollback(self):
                pass

            async def refresh(self, _v):
                pass

        @contextlib.asynccontextmanager
        async def _session_ok():
            yield FakeSession()

        async def _empty_context():
            return ""

        monkeypatch.setattr("app.models.database.get_session_context", _session_ok)
        monkeypatch.setattr(board_module, "get_llm_service", lambda: LLMEnPanne())
        monkeypatch.setattr(
            board_module, "get_llm_service_for_provider", lambda *a, **k: LLMEnPanne()
        )
        monkeypatch.setattr(board_module, "_get_user_context", lambda: "")
        monkeypatch.setattr(BoardService, "_track_usage", lambda *a, **k: None)
        monkeypatch.setattr(
            BoardService, "_search_web_for_context", lambda *a, **k: _empty_context()
        )

        service = BoardService(FakeSession())
        request = BoardRequest(
            question="Faut-il lancer ce pilote maintenant ?",
            mode=BoardMode.CLOUD,
            advisors=[AdvisorRole.ANALYST],
        )
        chunks = []
        erreur_finale = None
        try:
            async for c in service.deliberate(request):
                chunks.append(c)
        except Exception as e:  # noqa: BLE001
            erreur_finale = e

        # Jamais un advisor_done vide suivi d'un done
        types = [c.type for c in chunks]
        assert "done" not in types
        assert erreur_finale is not None
        # Le message précis du conseiller survit dans l'erreur finale
        assert "L'Analyste" in str(erreur_finale)


class TestLaFormeSobreResteDetectable:
    """Auto-contrôle post-p2 : la forme sobre « Erreur de connexion au
    service d'IA (ConnectError) » ne matchait AUCUN marker de
    _is_provider_outage (« connection » anglais ≠ « connexion » français) -
    le circuit breaker devenait aveugle aux pannes réseau. La forme dit
    désormais la CLASSE d'erreur : transport réseau (outage) vs interne
    (jamais un motif d'ouverture de circuit - plus conservateur qu'avant,
    où un str(e) local contenant « connection » ouvrait le circuit à tort)."""

    @pytest.mark.asyncio
    async def test_une_panne_reseau_ouvre_toujours_le_circuit(self, monkeypatch):
        import httpx
        from app.services.llm import _is_provider_outage
        from app.services.providers.base import LLMConfig, LLMProvider
        from app.services.providers.openai import OpenAIProvider

        provider = OpenAIProvider(
            LLMConfig(provider=LLMProvider.OPENAI, model="gpt-5.6-sol", api_key="k"),
            client=httpx.AsyncClient(),
        )

        def stream_reseau_mort(*a, **k):
            raise httpx.ConnectError("connexion refusée vers 10.0.0.1")

        monkeypatch.setattr(provider.client, "stream", stream_reseau_mort)
        events = [e async for e in provider.stream(None, [{"role": "user", "content": "x"}], None)]
        erreurs = [e for e in events if e.type == "error"]
        assert erreurs
        assert _is_provider_outage(erreurs[0].content), (
            f"panne réseau non reconnue comme outage : {erreurs[0].content!r}"
        )
        # Et toujours aucune fuite du detail
        assert "10.0.0.1" not in (erreurs[0].content or "")

    @pytest.mark.asyncio
    async def test_un_bug_local_n_ouvre_pas_le_circuit(self, monkeypatch):
        import httpx
        from app.services.llm import _is_provider_outage
        from app.services.providers.base import LLMConfig, LLMProvider
        from app.services.providers.openai import OpenAIProvider

        provider = OpenAIProvider(
            LLMConfig(provider=LLMProvider.OPENAI, model="gpt-5.6-sol", api_key="k"),
            client=httpx.AsyncClient(),
        )

        def stream_bug_local(*a, **k):
            raise ValueError("bug applicatif avec connection dans le texte")

        monkeypatch.setattr(provider.client, "stream", stream_bug_local)
        events = [e async for e in provider.stream(None, [{"role": "user", "content": "x"}], None)]
        erreurs = [e for e in events if e.type == "error"]
        assert erreurs
        assert not _is_provider_outage(erreurs[0].content), (
            "un bug applicatif local ne doit pas ouvrir le circuit"
        )


class TestPanel048GroupeA:
    """Panel interne 0.48 (remplace la passe Soso 3) - groupe comportement."""

    @pytest.mark.asyncio
    async def test_raise_on_error_compte_l_outage_avant_de_lever(self, monkeypatch):
        """[majeur] Le RuntimeError levé au premier StreamEvent(error)
        fermait le générateur AVANT sa comptabilité post-boucle : le circuit
        du fournisseur ne s'ouvrait jamais depuis le trafic Board - le repli
        explicite (F3 p1) ne s'enclenchait donc jamais."""
        from unittest.mock import AsyncMock

        from app.services.circuit_breaker import get_circuit_breaker
        from app.services.context import ContextWindow
        from app.services.llm import LLMService
        from app.services.providers.base import LLMConfig, LLMProvider, StreamEvent

        cb = get_circuit_breaker()
        cb.reset()

        class ProviderEnPanne:
            async def stream(self, system_prompt, messages, tools, **kwargs):
                yield StreamEvent(type="error", content="API error: 503")

        service = LLMService(
            LLMConfig(provider=LLMProvider.OPENAI, model="gpt-5.6-sol", api_key="k")
        )
        service._ensure_provider = AsyncMock()
        service._resolve_with_circuit_breaker = lambda: service.config
        service._provider = ProviderEnPanne()

        context = ContextWindow(messages=[], system_prompt="s")
        with pytest.raises(RuntimeError):
            async for _ in service.stream_response(context, raise_on_error=True):
                pass

        circuit = cb._get_circuit("openai")
        assert circuit.total_failures >= 1, (
            "l'outage doit se compter AVANT le raise, sinon le circuit "
            "ne s'ouvre jamais depuis ce chemin"
        )
        cb.reset()

    @pytest.mark.asyncio
    async def test_raise_on_error_leve_un_message_pour_ecran(self, monkeypatch):
        """[moyen] Le RuntimeError nu passait au générique via
        message_pour_ecran : les messages actionnables (BUG-040 Ollama,
        « API error: 429 ») étaient perdus en non-stream et à l'Atelier."""
        from unittest.mock import AsyncMock

        from app.services.context import ContextWindow
        from app.services.error_handler import ErreurPourEcran, message_pour_ecran
        from app.services.llm import LLMService
        from app.services.providers.base import LLMConfig, LLMProvider, StreamEvent

        class ProviderModeleAbsent:
            async def stream(self, system_prompt, messages, tools, **kwargs):
                yield StreamEvent(
                    type="error",
                    content="Le modèle 'x' n'est pas installé dans Ollama. Lance 'ollama pull x'.",
                )

        service = LLMService(
            LLMConfig(provider=LLMProvider.OLLAMA, model="x", base_url="http://h")
        )
        service._ensure_provider = AsyncMock()
        service._resolve_with_circuit_breaker = lambda: service.config
        service._provider = ProviderModeleAbsent()

        context = ContextWindow(messages=[], system_prompt="s")
        with pytest.raises(ErreurPourEcran) as excinfo:
            async for _ in service.stream_response(context, raise_on_error=True):
                pass
        assert "ollama pull x" in message_pour_ecran(excinfo.value)

    @pytest.mark.asyncio
    async def test_ollama_ne_fuit_plus_str_e(self, monkeypatch):
        """[moyen] Le catch générique d'ollama émettait « Erreur Ollama:
        {str(e)} » - le provider des utilisateurs souverains, le plus exposé
        en alpha, était le seul à fuir encore."""
        import httpx
        from app.services.providers.base import LLMConfig, LLMProvider
        from app.services.providers.ollama import OllamaProvider

        provider = OllamaProvider(
            LLMConfig(provider=LLMProvider.OLLAMA, model="m", base_url="http://h"),
            client=httpx.AsyncClient(),
        )

        def stream_qui_fuit(*a, **k):
            raise RuntimeError("sk-secret /Users/ludo/interne")

        monkeypatch.setattr(provider.client, "stream", stream_qui_fuit)
        events = [e async for e in provider.stream(None, [{"role": "user", "content": "x"}], None)]
        erreurs = [e for e in events if e.type == "error"]
        assert erreurs
        assert all("sk-secret" not in (e.content or "") for e in erreurs)

    def test_deep_research_et_documents_sans_str_e(self):
        """[mineur] Deux émetteurs d'écran restaient hors frontière."""
        import inspect

        from app.routers import documents as documents_router
        from app.services import deep_research

        assert "La synthèse a échoué : {e}" not in inspect.getsource(deep_research)
        assert (
            "Erreur du fournisseur IA pendant la rédaction : {exc}"
            not in inspect.getsource(documents_router)
        )


class TestRevueSosoPasse2:
    """Passe 2 de la revue du hotfix 0.48.1 (findings 3, 4, 6)."""

    def test_f3_un_avis_de_ponctuation_seule_ne_passe_pas(self):
        """« ... », « --- », « ?! » survivent à strip() mais ne disent rien :
        la garde doit exiger du contenu SÉMANTIQUE."""
        from app.services.board import contenu_exploitable

        assert contenu_exploitable("Un vrai avis mesuré.") is True
        assert contenu_exploitable("42") is True
        for vide_de_sens in ("", "   ", "\n\t ", "...", "---", "?!", "  ***  "):
            assert contenu_exploitable(vide_de_sens) is False, vide_de_sens

    @pytest.mark.asyncio
    async def test_f4_une_cle_gemini_invalide_reste_actionnable(self, monkeypatch):
        """400/401 « API key not valid » devenait « API error: 400 » : ni
        actionnable pour l'utilisateur, ni reconnu comme panne. Le corps brut
        du fournisseur ne doit pas fuir POUR AUTANT."""
        import httpx
        from app.services.llm import _is_provider_outage
        from app.services.providers.base import LLMConfig, LLMProvider
        from app.services.providers.gemini import GeminiProvider

        def reponse(code: int, corps: bytes):
            class FauxResponse:
                status_code = code

                async def aread(self):
                    return corps

                async def aiter_lines(self):
                    if False:
                        yield ""

                async def __aenter__(self):
                    return self

                async def __aexit__(self, *a):
                    return None

            return FauxResponse()

        provider = GeminiProvider(
            LLMConfig(provider=LLMProvider.GEMINI, model="gemini-3.7-flash", api_key="k"),
            client=httpx.AsyncClient(),
        )
        messages = [{"role": "user", "parts": [{"text": "x"}]}]

        # 400 clé invalide : message actionnable, sans corps brut
        monkeypatch.setattr(
            provider.client, "stream",
            lambda *a, **k: reponse(400, b'{"error":{"message":"API key not valid trace-77"}}'),
        )
        events = [e async for e in provider.stream(None, messages, None)]
        contenu = next(e.content for e in events if e.type == "error")
        assert "trace-77" not in contenu
        assert "clé" in contenu.lower() and "api" in contenu.lower()
        assert _is_provider_outage(contenu), "une clé invalide doit ouvrir le circuit"

        # 5xx : panne technique, message sobre
        monkeypatch.setattr(
            provider.client, "stream",
            lambda *a, **k: reponse(500, b'{"error":{"message":"Internal trace-99"}}'),
        )
        events = [e async for e in provider.stream(None, messages, None)]
        contenu = next(e.content for e in events if e.type == "error")
        assert "trace-99" not in contenu
        assert _is_provider_outage(contenu)

        # 400 applicatif (pas d'authentification) : PAS une panne du fournisseur
        monkeypatch.setattr(
            provider.client, "stream",
            lambda *a, **k: reponse(400, b'{"error":{"message":"Invalid function name trace-11"}}'),
        )
        events = [e async for e in provider.stream(None, messages, None)]
        contenu = next(e.content for e in events if e.type == "error")
        assert "trace-11" not in contenu
        assert not _is_provider_outage(contenu)

    @pytest.mark.asyncio
    async def test_f6_le_suivi_qui_echoue_ne_propage_pas(self):
        """Test COMPORTEMENTAL du helper (l'ancien vérifiait juste un nom)."""
        from app.models.processing import EtatTache
        from app.routers.board import _terminer_sans_masquer

        class HandleQuiCasse:
            id = "tache-1"
            appels: list = []

            async def terminer(self, etat, error=None):
                HandleQuiCasse.appels.append((etat, error))
                raise RuntimeError("base verrouillée")

        handle = HandleQuiCasse()
        # Ne lève pas, quel que soit l'état terminal demandé
        await _terminer_sans_masquer(handle, EtatTache.FAILED, error="cause métier")
        await _terminer_sans_masquer(handle, EtatTache.DONE)
        await _terminer_sans_masquer(handle, EtatTache.CANCELLED)
        assert len(HandleQuiCasse.appels) == 3
        # handle absent : sans effet
        await _terminer_sans_masquer(None, EtatTache.DONE)

    def test_f5_le_contrat_des_prix_annonce_la_bonne_devise(self, client):
        """/api/escalation/prices annonçait « EUR » sur des tarifs relevés en
        USD : une valeur métier fausse, pas un simple nom de champ."""
        reponse = client.get("/api/escalation/prices")
        assert reponse.status_code == 200
        assert reponse.json()["currency"] == "USD"

    def test_p3_f2_les_alertes_de_budget_disent_la_bonne_devise(self):
        """Passe 3 (finding 2) : les messages d'alerte annonçaient « EUR »
        sur des montants calculés à partir de tarifs USD."""
        import inspect

        from app.services import token_tracker

        source = inspect.getsource(token_tracker)
        assert "EUR " not in source.replace("cost_eur", "").replace(
            "budget_eur", ""
        ), "un message d'alerte annonce encore des euros"

    @pytest.mark.asyncio
    async def test_p3_f3_un_modele_gemini_inconnu_est_actionnable(self, monkeypatch):
        """404 « model not found » : l'utilisateur doit savoir qu'il s'agit du
        modèle choisi - sans que le circuit s'ouvre (ce n'est pas une panne)."""
        import httpx
        from app.services.llm import _is_provider_outage
        from app.services.providers.base import LLMConfig, LLMProvider
        from app.services.providers.gemini import GeminiProvider

        class FauxResponse:
            status_code = 404

            async def aread(self):
                return b'{"error":{"message":"models/gemini-x is not found trace-55"}}'

            async def aiter_lines(self):
                if False:
                    yield ""

            async def __aenter__(self):
                return self

            async def __aexit__(self, *a):
                return None

        provider = GeminiProvider(
            LLMConfig(provider=LLMProvider.GEMINI, model="gemini-x", api_key="k"),
            client=httpx.AsyncClient(),
        )
        monkeypatch.setattr(provider.client, "stream", lambda *a, **k: FauxResponse())
        events = [
            e async for e in provider.stream(
                None, [{"role": "user", "parts": [{"text": "x"}]}], None
            )
        ]
        contenu = next(e.content for e in events if e.type == "error")
        assert "trace-55" not in contenu
        assert "modèle" in contenu.lower()
        assert not _is_provider_outage(contenu), (
            "un modèle mal choisi ne doit pas ouvrir le circuit du fournisseur"
        )

    @pytest.mark.asyncio
    async def test_p4_f3_un_400_parlant_de_modele_ne_ment_pas(self, monkeypatch):
        """Passe 4 (F3) : « Invalid function name for model X » (400) donnait
        « modèle introuvable » - une fausse piste de correction."""
        import httpx
        from app.services.providers.base import LLMConfig, LLMProvider
        from app.services.providers.gemini import GeminiProvider

        def reponse(code: int, corps: bytes):
            class FauxResponse:
                status_code = code

                async def aread(self):
                    return corps

                async def aiter_lines(self):
                    if False:
                        yield ""

                async def __aenter__(self):
                    return self

                async def __aexit__(self, *a):
                    return None

            return FauxResponse()

        provider = GeminiProvider(
            LLMConfig(provider=LLMProvider.GEMINI, model="gemini-3.7-flash", api_key="k"),
            client=httpx.AsyncClient(),
        )
        messages = [{"role": "user", "parts": [{"text": "x"}]}]

        for corps in (
            b'{"error":{"message":"Invalid function name for model X"}}',
            b'{"error":{"message":"Function get_weather not found"}}',
        ):
            monkeypatch.setattr(
                provider.client, "stream", lambda *a, _c=corps, **k: reponse(400, _c)
            )
            events = [e async for e in provider.stream(None, messages, None)]
            contenu = next(e.content for e in events if e.type == "error")
            assert "introuvable" not in contenu.lower(), contenu

        # Le vrai 404 « modèle » reste actionnable
        monkeypatch.setattr(
            provider.client, "stream",
            lambda *a, **k: reponse(404, b'{"error":{"message":"models/x is not found"}}'),
        )
        events = [e async for e in provider.stream(None, messages, None)]
        contenu = next(e.content for e in events if e.type == "error")
        assert "modèle" in contenu.lower()

    def test_p4_f4_le_tracker_ne_parle_plus_d_euros(self):
        """Passe 4 (F4) : le journal écrivait encore « (0.0123 EUR) » - de quoi
        tromper un diagnostic support. Le test précédent cherchait « EUR »
        suivi d'un espace et ratait « EUR) » et « EUR. »."""
        import inspect

        from app.services import token_tracker

        source = inspect.getsource(token_tracker)
        sans_noms_de_champs = (
            source.replace("cost_eur", "").replace("budget_eur", "")
        )
        assert "EUR" not in sans_noms_de_champs
        assert "euros" not in sans_noms_de_champs.lower()
