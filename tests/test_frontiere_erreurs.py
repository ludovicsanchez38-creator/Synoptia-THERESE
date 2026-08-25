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
            anthropic, deepseek, gemini, infomaniak, mistral,
            ollama, openai, openrouter, perplexity,
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
