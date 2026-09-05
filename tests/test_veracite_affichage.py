"""Revue 30/08 : un état affiché doit correspondre à un fait vérifié."""

from __future__ import annotations

import inspect
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parent.parent / "src" / "backend"


def _monitor_vierge():
    """Le singleton de perf ne doit pas hériter des latences d'un autre test."""
    import app.services.performance as perf

    perf._performance_monitor = None
    perf.PerformanceMonitor._instance = None
    return perf.get_performance_monitor()


class TestTokensEtSla:
    def test_un_morceau_de_flux_n_est_pas_un_token(self):
        from app.services.performance import StreamingMetrics

        metrics = StreamingMetrics(conversation_id="c")
        metrics.record_token()
        metrics.record_token()
        assert metrics.total_tokens == 0

    def test_seuls_les_tokens_d_usage_sont_comptes(self):
        from app.services.performance import StreamingMetrics

        metrics = StreamingMetrics(conversation_id="c")
        metrics.record_token()
        metrics.record_output_tokens(17)
        summary = metrics.finish()
        assert summary["total_tokens"] == 17
        assert summary["tokens_measured"] is True

    def test_sans_usage_les_tokens_ne_sont_pas_mesures(self):
        from app.services.performance import StreamingMetrics

        metrics = StreamingMetrics(conversation_id="c")
        metrics.record_token()
        summary = metrics.finish()
        assert summary["total_tokens"] == 0
        assert summary["tokens_measured"] is False

    def test_sla_inconnu_avant_la_premiere_mesure(self):
        stats = _monitor_vierge().get_stats()
        assert stats["total_requests"] == 0
        assert stats["meets_sla"] is None

    def test_sla_respecte_seulement_si_la_moyenne_est_sous_2s(self):
        monitor = _monitor_vierge()
        metrics = monitor.start_stream("c-ok")
        metrics.first_token_time = metrics.start_time + 0.4
        monitor.finish_stream("c-ok")
        assert monitor.get_stats()["meets_sla"] is True

    def test_sla_non_respecte_si_la_moyenne_depasse_2s(self):
        monitor = _monitor_vierge()
        metrics = monitor.start_stream("c-lent")
        metrics.first_token_time = metrics.start_time + 3.0
        monitor.finish_stream("c-lent")
        assert monitor.get_stats()["meets_sla"] is False

    def test_tokens_non_mesures_tant_qu_aucun_usage_n_est_enregistre(self):
        monitor = _monitor_vierge()
        monitor.start_stream("c")
        monitor.finish_stream("c")
        stats = monitor.get_stats()
        assert stats["tokens_measured"] is False
        assert stats["total_tokens"] == 0

    def test_chat_n_incremente_plus_un_chunk_comme_token(self):
        chat_py = (SRC / "app" / "routers" / "chat.py").read_text(encoding="utf-8")
        assert "stream_metrics.record_token()" not in chat_py
        assert "record_output_tokens" in chat_py


class TestActionPasTermineeSiEtapeEnEchec:
    @pytest.mark.asyncio
    async def test_une_etape_en_echec_interdit_le_statut_termine(self, monkeypatch):
        from app.services.action_agents import (
            ActionAgentDef,
            ActionAgentStep,
            ActionRunner,
            StepResult,
            StepStatus,
            TaskState,
            TaskStatus,
        )

        agent = ActionAgentDef(
            id="t",
            name="Test",
            description="",
            icon="",
            category="x",
            steps=[
                ActionAgentStep(id="s1", label="Veille", prompt="p1"),
                ActionAgentStep(id="s2", label="Synthèse", prompt="p2"),
            ],
        )
        task = TaskState(
            task_id="task-1",
            agent_id="t",
            agent_name="Test",
            steps=[
                StepResult(step_id="s1", label="Veille"),
                StepResult(step_id="s2", label="Synthèse"),
            ],
        )

        n = {"i": 0}

        class FakeLLM:
            def prepare_context(self, messages, system_prompt=None):
                return object()

            async def stream_response(self, context):
                n["i"] += 1
                if n["i"] == 1:
                    raise RuntimeError("quota")
                    yield "x"
                yield "ok"

        monkeypatch.setattr(
            "app.services.llm.get_llm_service", lambda: FakeLLM()
        )

        async def pas_de_contexte(*_args, **_kwargs):
            return ""

        monkeypatch.setattr(
            "app.services.action_agents._gather_local_context",
            pas_de_contexte,
        )

        await ActionRunner._derouler(task, agent, {}, None)
        assert task.status == TaskStatus.ERROR
        assert task.steps[0].status == StepStatus.ERROR
        assert task.steps[1].status == StepStatus.COMPLETED
        assert task.error
        assert "Veille" in task.error


class TestRechercheApprofondiePersisteLesSources:
    def test_la_sauvegarde_emporte_les_sources(self):
        """01/09 : ce test lisait le TEXTE de la fonction, et c'est ce qui a
        laissé passer un correctif cassé.

        Il faisait `assert '"sources"' in source` sur le code source de
        `deep_research_endpoint`. La chaîne y était, donc il passait, pendant
        que la ligne voisine `async with get_session()` levait une TypeError
        avalée par un `except` : rien n'était jamais écrit.

        La garantie de comportement vit désormais dans
        `tests/test_persistance_sources_recherche.py`, qui écrit puis relit.
        Ce qui reste ici est une garde de forme, explicitement nommée comme
        telle : la fonction doit employer le gestionnaire de contexte, pas la
        génératrice de dépendance.
        """
        from app.routers import chat as chat_mod

        source = inspect.getsource(chat_mod.deep_research_endpoint)
        assert "extra_data" in source
        lignes_de_code = [
            ligne for ligne in source.splitlines()
            if not ligne.strip().startswith("#")
        ]
        assert not [
            ligne for ligne in lignes_de_code
            if "async with get_session()" in ligne
        ], "get_session est une génératrice de dépendance : utiliser get_session_context"
