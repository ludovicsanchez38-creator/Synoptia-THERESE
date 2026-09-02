"""Board frontier + effort max (0.48, lot A1 - design V3.5, point 2).

Chaque conseiller cloud reçoit le FRONTIER de son fournisseur (tête de
liste du catalogue), l'effort « max » (traduit par le résolveur dans la
syntaxe du fournisseur) et le max_tokens recommandé - quelles que soient
les préférences utilisateur. Le chat, lui, garde ses défauts.
"""

import json
from types import SimpleNamespace

import pytest
from app.services.modeles_catalogue import frontier, max_tokens_recommande


class TestLeHelperOverrides:
    """get_llm_service_for_provider : effort_override + max_tokens_override."""

    def test_effort_override_pose_l_effort_resolu(self, client, monkeypatch):
        from app.services.llm import get_llm_service_for_provider

        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
        service = get_llm_service_for_provider(
            "anthropic",
            model_override=frontier("anthropic"),
            effort_override="max",
        )
        assert service is not None
        assert service.config.model == "claude-opus-5"
        assert service.config.effort == "max"
        # claude-opus-5 : max se traduit max (output_config.effort)
        assert service.config.effort_resolu == "max"

    def test_max_tokens_override_pose_la_config(self, client, monkeypatch):
        from app.services.llm import get_llm_service_for_provider

        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
        service = get_llm_service_for_provider(
            "anthropic",
            model_override="claude-opus-5",
            max_tokens_override=64000,
        )
        assert service is not None
        assert service.config.max_tokens == 64000

    def test_sans_override_comportement_intact(self, client, monkeypatch):
        from app.services.llm import get_llm_service_for_provider

        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
        service = get_llm_service_for_provider("anthropic")
        assert service is not None
        assert service.config.effort is None
        assert service.config.max_tokens == 4096

    def test_preferences_non_frontier_ignorees_par_l_override(self, client, monkeypatch):
        """Design : préférence utilisateur gpt-5.5 -> le conseiller reçoit
        quand même gpt-5.6-sol (model_override gagne sur user_model)."""
        from app.models.database import get_sync_connection
        from app.services.llm import get_llm_service_for_provider
        from sqlalchemy import text

        with get_sync_connection() as conn:
            for cle, valeur in (("llm_provider", "openai"), ("llm_model", "gpt-5.5")):
                conn.execute(
                    text(
                        "INSERT OR REPLACE INTO preferences"
                        " (id, key, value, category, created_at, updated_at)"
                        " VALUES (lower(hex(randomblob(16))), :k, :v, 'llm',"
                        " datetime('now'), datetime('now'))"
                    ),
                    {"k": cle, "v": valeur},
                )
            conn.commit()

        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
        service = get_llm_service_for_provider(
            "openai",
            model_override=frontier("openai"),
            effort_override="max",
        )
        assert service is not None
        assert service.config.model == "gpt-5.6-sol"
        # gpt-5.6-sol : reasoning_effort max transmis tel quel
        assert service.config.effort_resolu == "max"


class TestPrepareContextLitLaConfig:
    """La réserve de prepare_context lit la config effective (plus de 4096 codé)."""

    def test_la_reserve_suit_max_tokens(self):
        from app.services.llm import LLMService
        from app.services.providers.base import LLMConfig, LLMProvider

        config = LLMConfig(
            provider=LLMProvider.ANTHROPIC,
            model="claude-opus-5",
            api_key="sk-test",
            context_window=200000,
            max_tokens=64000,
        )
        service = LLMService(config)
        context = service.prepare_context([], system_prompt="s")
        assert context.max_tokens == 200000 - 64000

    def test_le_defaut_reste_4096(self):
        from app.services.llm import LLMService
        from app.services.providers.base import LLMConfig, LLMProvider

        config = LLMConfig(
            provider=LLMProvider.OPENAI,
            model="gpt-5.6-sol",
            api_key="sk-test",
            context_window=128000,
        )
        service = LLMService(config)
        context = service.prepare_context([], system_prompt="s")
        assert context.max_tokens == 128000 - 4096


class TestLeBoardPrechargeEnFrontier:
    """board.py demande frontier + effort max + max_tokens recommandé."""

    @pytest.mark.asyncio
    async def test_les_conseillers_cloud_recoivent_les_overrides(self, monkeypatch):
        import contextlib

        from app.models.board import AdvisorRole, BoardMode, BoardRequest
        from app.services import board as board_module
        from app.services.board import BoardService
        from app.services.llm import LLMProvider

        synthesis = json.dumps({
            "consensus_points": ["OK"],
            "divergence_points": [],
            "recommendation": "Y aller.",
            "confidence": "high",
            "next_steps": ["Cadrer"],
        })

        class FakeLLM:
            def __init__(self, responses, provider=LLMProvider.OPENAI):
                self.responses = responses
                self.calls = 0
                self.config = SimpleNamespace(provider=provider, model="modele-test")

            def prepare_context(self, messages, system_prompt=None):
                return messages, system_prompt

            async def stream_response(self, context, usage_sink=None, raise_on_error=False):
                response = self.responses[min(self.calls, len(self.responses) - 1)]
                self.calls += 1
                yield response

        appels: list[tuple[tuple, dict]] = []

        def faux_helper(*args, **kwargs):
            appels.append((args, kwargs))
            return FakeLLM(["Avis mesuré."])

        class FakeSession:
            def add(self, _value):
                pass

            async def commit(self):
                pass

            async def rollback(self):
                pass

            async def refresh(self, _value):
                pass

        @contextlib.asynccontextmanager
        async def _session_ok():
            yield FakeSession()

        async def _empty_context():
            return ""

        monkeypatch.setattr(
            "app.models.database.get_session_context", _session_ok
        )
        monkeypatch.setattr(
            board_module, "get_llm_service", lambda: FakeLLM([synthesis])
        )
        monkeypatch.setattr(board_module, "get_llm_service_for_provider", faux_helper)
        monkeypatch.setattr(board_module, "_get_user_context", lambda: "")
        monkeypatch.setattr(BoardService, "_track_usage", lambda *a, **k: None)
        monkeypatch.setattr(
            BoardService, "_search_web_for_context", lambda *a, **k: _empty_context()
        )

        service = BoardService(FakeSession())
        request = BoardRequest(
            question="Faut-il lancer ce pilote maintenant ?",
            mode=BoardMode.CLOUD,
            advisors=[AdvisorRole.ANALYST, AdvisorRole.STRATEGIST],
        )
        async for _chunk in service.deliberate(request):
            pass

        # analyst -> anthropic, strategist -> openai
        par_provider = {
            (a[0] if a else k.get("provider_name")): k for a, k in appels
        }
        assert "anthropic" in par_provider and "openai" in par_provider
        from app.services.board import PLANCHER_MAX_TOKENS_CONSEILLER

        for provider_name, kwargs in par_provider.items():
            attendu = frontier(provider_name)
            assert kwargs.get("model_override") == attendu, (
                f"{provider_name} : model_override={kwargs.get('model_override')}"
            )
            assert kwargs.get("effort_override") == "max"
            # Panel 0.48 : recommandation du catalogue si sourcée, sinon le
            # plancher Board (effort max : le raisonnement décompte du plafond,
            # 4096 pouvait rendre un avis vide).
            recommande = max_tokens_recommande(attendu)
            assert kwargs.get("max_tokens_override") == (
                recommande if recommande is not None else PLANCHER_MAX_TOKENS_CONSEILLER
            )
        # claude-opus-5 porte un max_tokens recommandé (64k, doc officielle)
        assert par_provider["anthropic"]["max_tokens_override"] == 64000


class TestLeTrimDuMessageUnique:
    """Revue 0.48 F2 : le Board place question + contexte + résultats web
    dans UN message ; trim_to_fit ne retirait du contenu que s'il restait
    plus d'un message - un message unique au-delà du budget partait intact
    et la requête échouait hors limite au lieu d'être tronquée."""

    def test_un_message_unique_est_tronque_au_budget(self):
        from app.services.context import ContextWindow
        from app.services.providers.base import Message

        contenu = "x" * 40000  # ~10 000 tokens estimés
        context = ContextWindow(
            messages=[Message(role="user", content=contenu)],
            system_prompt="s",
            max_tokens=1000,
        ).trim_to_fit()

        assert len(context.messages) == 1
        assert context.total_tokens() <= 1000
        # La coupe est annoncée, pas silencieuse
        assert "tronqué" in context.messages[0].content

    def test_un_message_sous_le_budget_reste_intact(self):
        from app.services.context import ContextWindow
        from app.services.providers.base import Message

        context = ContextWindow(
            messages=[Message(role="user", content="courte question")],
            system_prompt="s",
            max_tokens=1000,
        ).trim_to_fit()

        assert context.messages[0].content == "courte question"


class TestLeBoardNeBasculePasEnSilence:
    """Revue 0.48 F3 : le circuit breaker basculait silencieusement le
    fournisseur d'un conseiller - identité SSE, usage, effort et sémaphore
    anti-429 devenaient faux. Contrat du design : repli EXPLICITE sur le
    service principal (visible dans actual_provider), jamais de bascule
    cachée au sein du flux d'un conseiller."""

    def test_le_service_sans_bascule_garde_son_fournisseur(self, monkeypatch):
        from app.services.circuit_breaker import get_circuit_breaker
        from app.services.llm import LLMService
        from app.services.providers.base import LLMConfig, LLMProvider

        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
        cb = get_circuit_breaker()
        cb.reset()
        for _ in range(10):
            cb.record_failure("anthropic", "boom")
        assert not cb.is_available("anthropic")

        service = LLMService(
            LLMConfig(
                provider=LLMProvider.ANTHROPIC,
                model="claude-opus-5",
                api_key="sk-ant-test",
            ),
            bascule_circuit=False,
        )
        config = service._resolve_with_circuit_breaker()
        assert config.provider is LLMProvider.ANTHROPIC
        cb.reset()

    def test_le_helper_transmet_le_refus_de_bascule(self, client, monkeypatch):
        from app.services.llm import get_llm_service_for_provider

        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
        service = get_llm_service_for_provider(
            "anthropic", bascule_circuit=False
        )
        assert service is not None
        assert service.bascule_circuit is False

    @pytest.mark.asyncio
    async def test_circuit_ouvert_au_prechargement_repli_explicite(self, monkeypatch):
        """Circuit du fournisseur préféré ouvert -> le conseiller part sur le
        service principal, et actual_provider dit la vérité."""
        import contextlib

        from app.models.board import AdvisorRole, BoardMode, BoardRequest
        from app.services import board as board_module
        from app.services.board import BoardService
        from app.services.circuit_breaker import get_circuit_breaker
        from app.services.llm import LLMProvider

        cb = get_circuit_breaker()
        cb.reset()
        for _ in range(10):
            cb.record_failure("anthropic", "boom")

        synthesis = json.dumps({
            "consensus_points": ["OK"], "divergence_points": [],
            "recommendation": "Y aller.", "confidence": "high",
            "next_steps": ["Cadrer"],
        })

        class FakeLLM:
            def __init__(self, responses, provider=LLMProvider.OPENAI):
                self.responses = responses
                self.calls = 0
                self.config = SimpleNamespace(provider=provider, model="modele-test")

            def prepare_context(self, messages, system_prompt=None):
                return messages, system_prompt

            async def stream_response(self, context, usage_sink=None, raise_on_error=False):
                response = self.responses[min(self.calls, len(self.responses) - 1)]
                self.calls += 1
                yield response

        class FakeSession:
            def add(self, _value):
                pass

            async def commit(self):
                pass

            async def rollback(self):
                pass

            async def refresh(self, _value):
                pass

        @contextlib.asynccontextmanager
        async def _session_ok():
            yield FakeSession()

        async def _empty_context():
            return ""

        conseiller_anthropic = FakeLLM(["ne doit pas être appelé"])

        monkeypatch.setattr("app.models.database.get_session_context", _session_ok)
        principal = FakeLLM(["Avis du principal.", synthesis])
        monkeypatch.setattr(board_module, "get_llm_service", lambda: principal)
        monkeypatch.setattr(
            board_module, "get_llm_service_for_provider",
            lambda *a, **k: conseiller_anthropic,
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
            advisors=[AdvisorRole.ANALYST],  # préféré : anthropic (circuit ouvert)
        )
        chunks = [c async for c in service.deliberate(request)]

        # Le conseiller dédié n'a JAMAIS été appelé (circuit ouvert au
        # préchargement) ; les chunks annoncent le fournisseur RÉEL (openai,
        # celui du service principal), pas anthropic.
        assert conseiller_anthropic.calls == 0
        providers_annonces = {
            c.provider for c in chunks if c.type == "advisor_start"
        }
        assert providers_annonces == {"openai"}
        cb.reset()


class TestLeTrimNeVidePasLaDemande:
    """Revue 0.48 p2 (F3) : la coupe ne gardait que le DÉBUT (une question
    placée après un long collage disparaissait) et un budget déjà épuisé
    par le prompt système remplaçait toute la demande par la seule marque."""

    def test_une_question_en_fin_de_collage_survit(self):
        from app.services.context import ContextWindow
        from app.services.providers.base import Message

        contenu = ("x" * 40000) + "\nQUESTION-FINALE : que retenir ?"
        context = ContextWindow(
            messages=[Message(role="user", content=contenu)],
            system_prompt="s",
            max_tokens=1000,
        ).trim_to_fit()

        assert context.total_tokens() <= 1000
        assert "QUESTION-FINALE" in context.messages[0].content
        assert context.messages[0].content.startswith("xxx")

    def test_budget_epuise_ne_vide_pas_le_message(self):
        from app.services.context import ContextWindow
        from app.services.providers.base import Message

        context = ContextWindow(
            messages=[Message(role="user", content="ma vraie question")],
            system_prompt="p" * 4000,  # ~1000 tokens : budget déjà dépassé
            max_tokens=100,
        ).trim_to_fit()

        # Mieux vaut un refus PROPRE de l'API qu'une demande vidée en silence
        assert context.messages[0].content == "ma vraie question"


class TestRevueSosoS2:
    """Contrôle post-release 0.48 (passe Soso du 25/08 au soir)."""

    @pytest.mark.asyncio
    async def test_s2_1_un_avis_vide_ne_passe_jamais_pour_termine(self, monkeypatch):
        """raise_on_error ne couvre que les évènements error : un flux qui se
        termine SANS texte (budget consommé, [DONE] immédiat) produisait un
        AdvisorOpinion vide, synthétisé et sauvegardé comme un avis."""
        import contextlib

        from app.models.board import AdvisorRole, BoardMode, BoardRequest
        from app.services import board as board_module
        from app.services.board import BoardService
        from app.services.llm import LLMProvider

        class LLMMuet:
            config = SimpleNamespace(provider=LLMProvider.OPENAI, model="modele-test")

            def prepare_context(self, messages, system_prompt=None):
                return messages, system_prompt

            async def stream_response(self, context, usage_sink=None, raise_on_error=False):
                # Aucun chunk : le fournisseur termine sans rien dire.
                return
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
        monkeypatch.setattr(board_module, "get_llm_service", lambda: LLMMuet())
        monkeypatch.setattr(
            board_module, "get_llm_service_for_provider", lambda *a, **k: LLMMuet()
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
        erreur = None
        try:
            async for c in service.deliberate(request):
                chunks.append(c)
        except Exception as e:  # noqa: BLE001
            erreur = e

        vides = [
            c for c in chunks
            if c.type == "advisor_done" and not (c.content or "").strip()
        ]
        assert vides == [], "un avis VIDE a été validé comme terminé"
        assert "done" not in [c.type for c in chunks]
        assert erreur is not None
        assert "L'Analyste" in str(erreur)

    @pytest.mark.asyncio
    async def test_s2_2_le_message_metier_part_meme_si_le_suivi_echoue(
        self, monkeypatch
    ):
        """handle.terminer() commite et peut lever : il ne doit jamais
        empêcher l'émission du chunk d'erreur destiné à l'utilisateur.

        B-078 : cette garantie était « prouvée » par `inspect.getsource()` et
        un `assert "_terminer_sans_masquer" in source`. Or la DÉFINITION du
        helper (`async def _terminer_sans_masquer(`, board.py:41) contient déjà
        cette chaîne : retirer les huit appels réels laissait l'assertion
        vraie. On exécute donc le chemin, avec un suivi qui lève.
        """
        from app.models.board import AdvisorRole, BoardMode, BoardRequest
        from app.routers import board as board_router
        from app.services import traitements

        class SuiviQuiLeveALaCloture:
            id = "traitement-de-test"
            annulation_demandee = None

            async def demarrer(self):
                return None

            async def lier_adaptateur(self, adaptateur):
                return None

            async def progresser(self, progress=None):
                return None

            async def terminer(self, etat, error=None):
                raise RuntimeError("base verrouillée pendant le commit du suivi")

        async def _creer_traitement(**kwargs):
            return SuiviQuiLeveALaCloture()

        class BoardEnPanne:
            _persistance_en_cours = None

            def __init__(self, session):
                self.session = session

            async def deliberate(self, request, **kwargs):
                raise RuntimeError("le fournisseur a coupé")
                yield  # pragma: no cover - fait de deliberate un générateur

        class SessionSansDecision:
            async def execute(self, requete):
                class Resultat:
                    def scalars(self):
                        return self

                    def first(self):
                        return None

                return Resultat()

        class ContexteDeSession:
            async def __aenter__(self):
                return SessionSansDecision()

            async def __aexit__(self, *args):
                return None

        monkeypatch.setattr(traitements, "creer_traitement", _creer_traitement)
        monkeypatch.setattr(board_router, "BoardService", BoardEnPanne)
        monkeypatch.setattr(
            board_router, "get_session_context", lambda: ContexteDeSession()
        )

        reponse = await board_router.deliberate(
            BoardRequest(
                question="Faut-il lancer ce pilote maintenant ?",
                mode=BoardMode.CLOUD,
                advisors=[AdvisorRole.ANALYST],
            )
        )
        morceaux = [m async for m in reponse.body_iterator]

        evenements = [
            json.loads(m.split("data: ", 1)[1])
            for m in morceaux
            if m.startswith("data: ")
        ]
        erreurs = [e for e in evenements if e.get("type") == "error"]
        assert erreurs, (
            "l'échec du SUIVI a emporté le message métier : le client ne voit "
            f"jamais la cause. Évènements émis : {evenements}"
        )
        assert erreurs[0]["content"].strip(), (
            "un chunk d'erreur vide ne dit rien à l'utilisateur"
        )

    def test_s2_2_aucun_terminer_nu_hors_du_helper(self):
        """Ceinture structurelle : un seul site exécuté sur les huit.

        Le test ci-dessus ne traverse qu'UN des huit appels. Ce verrou couvre
        les sept autres, et il compte des APPELS dans l'arbre syntaxique - la
        ligne `async def _terminer_sans_masquer(` n'en est pas un.
        """
        import ast
        from pathlib import Path

        from app.routers import board as board_router

        source = Path(board_router.__file__).read_text(encoding="utf-8")
        arbre = ast.parse(source)

        helper = next(
            n for n in ast.walk(arbre)
            if isinstance(n, ast.AsyncFunctionDef)
            and n.name == "_terminer_sans_masquer"
        )
        dedans, dehors = [], []
        for noeud in ast.walk(arbre):
            if not isinstance(noeud, ast.Call):
                continue
            cible = noeud.func
            if not isinstance(cible, ast.Attribute) or cible.attr != "terminer":
                continue
            if not isinstance(cible.value, ast.Name) or cible.value.id != "handle":
                continue
            if helper.lineno <= noeud.lineno <= (helper.end_lineno or helper.lineno):
                dedans.append(noeud.lineno)
            else:
                dehors.append(noeud.lineno)

        assert dedans, "le helper n'appelle plus terminer() : il ne sert plus à rien"
        assert dehors == [], (
            "des terminer() appellent le suivi SANS filet, lignes "
            f"{dehors} : un échec du suivi y emporterait le message métier"
        )

    @pytest.mark.asyncio
    async def test_s2_3_un_5xx_gemini_ouvre_le_circuit(self, monkeypatch):
        """La branche manuelle status_code != 200 retirait le code HTTP :
        _is_provider_outage ne voyait plus la panne (et le message brut du
        fournisseur partait à l'écran)."""
        import httpx
        from app.services.llm import _is_provider_outage
        from app.services.providers.base import LLMConfig, LLMProvider
        from app.services.providers.gemini import GeminiProvider

        provider = GeminiProvider(
            LLMConfig(provider=LLMProvider.GEMINI, model="gemini-3.7-flash", api_key="k"),
            client=httpx.AsyncClient(),
        )

        class FauxResponse:
            status_code = 500

            async def aread(self):
                return (
                    b'{"error":{"message":"Internal error encountered. '
                    b'trace-id 42 interne"}}'
                )

            async def aiter_lines(self):
                if False:
                    yield ""

            async def __aenter__(self):
                return self

            async def __aexit__(self, *a):
                return None

        monkeypatch.setattr(provider.client, "stream", lambda *a, **k: FauxResponse())
        # Format Gemini : parts[], pas content (sinon le provider sort avant l'appel)
        messages = [{"role": "user", "parts": [{"text": "x"}]}]
        events = [e async for e in provider.stream(None, messages, None)]
        erreurs = [e for e in events if e.type == "error"]
        assert erreurs
        assert _is_provider_outage(erreurs[0].content), (
            f"5xx non reconnu comme panne : {erreurs[0].content!r}"
        )
        assert "trace-id 42" not in (erreurs[0].content or "")
