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
        for provider_name, kwargs in par_provider.items():
            attendu = frontier(provider_name)
            assert kwargs.get("model_override") == attendu, (
                f"{provider_name} : model_override={kwargs.get('model_override')}"
            )
            assert kwargs.get("effort_override") == "max"
            assert kwargs.get("max_tokens_override") == max_tokens_recommande(attendu)
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
