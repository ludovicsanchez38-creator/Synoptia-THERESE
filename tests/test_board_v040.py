"""Garde-fous Board introduits pour l'interface conversationnelle 0.40."""

import asyncio
import json
from types import SimpleNamespace

import pytest
from app.models.board import (
    AdvisorOpinion,
    AdvisorRole,
    BoardDecision,
    BoardMode,
    BoardRequest,
    BoardSynthesis,
)
from app.routers import board as board_router
from app.services import board as board_module
from app.services.board import BoardService
from app.services.llm import LLMProvider


class FakeLLM:
    def __init__(self, responses: list[str], provider: LLMProvider = LLMProvider.OPENAI):
        self.responses = responses
        self.calls = 0
        self.config = SimpleNamespace(provider=provider, model="modele-test")

    def prepare_context(self, messages, system_prompt=None):
        return messages, system_prompt

    async def stream_response(self, context, usage_sink=None):
        response = self.responses[self.calls]
        self.calls += 1
        yield response


class FailingCommitSession:
    def __init__(self):
        self.added = False
        self.rolled_back = False

    def add(self, _value):
        self.added = True

    async def commit(self):
        raise RuntimeError("disque indisponible")

    async def rollback(self):
        self.rolled_back = True


@pytest.mark.asyncio
async def test_sovereign_mode_never_falls_back_to_cloud(monkeypatch):
    cloud = FakeLLM(["ne doit jamais être appelé"])
    monkeypatch.setattr(board_module, "get_llm_service", lambda: cloud)
    monkeypatch.setattr(board_module, "get_llm_service_for_provider", lambda *args, **kwargs: None)
    monkeypatch.setattr(board_module, "_get_user_context", lambda: "")

    service = BoardService()
    request = BoardRequest(
        question="Faut-il lancer cette expérimentation locale ?",
        mode=BoardMode.SOVEREIGN,
        advisors=[AdvisorRole.ANALYST],
    )

    with pytest.raises(RuntimeError, match="Ollama"):
        _ = [chunk async for chunk in service.deliberate(request)]

    assert cloud.calls == 0


@pytest.mark.asyncio
async def test_persistence_failure_never_emits_done(monkeypatch):
    synthesis = json.dumps({
        "consensus_points": ["Tester"],
        "divergence_points": [],
        "recommendation": "Lancer un pilote.",
        "confidence": "high",
        "next_steps": ["Cadrer"],
    })
    llm = FakeLLM(["Avis mesuré.", synthesis])
    session = FailingCommitSession()
    monkeypatch.setattr(board_module, "get_llm_service", lambda: llm)
    monkeypatch.setattr(board_module, "get_llm_service_for_provider", lambda *args, **kwargs: llm)
    monkeypatch.setattr(board_module, "_get_user_context", lambda: "")
    monkeypatch.setattr(BoardService, "_track_usage", lambda *args, **kwargs: None)
    monkeypatch.setattr(BoardService, "_search_web_for_context", lambda *args, **kwargs: _empty_context())

    service = BoardService(session)
    request = BoardRequest(
        question="Faut-il lancer ce pilote dès maintenant ?",
        mode=BoardMode.CLOUD,
        advisors=[AdvisorRole.ANALYST],
    )
    received = []

    with pytest.raises(RuntimeError, match="sauvegardée"):
        async for chunk in service.deliberate(request):
            received.append(chunk.type)

    assert session.added is True
    assert session.rolled_back is True
    assert "synthesis_chunk" not in received
    assert "done" not in received


async def _empty_context() -> str:
    return ""


@pytest.mark.asyncio
async def test_closing_stream_cancels_advisor_tasks(monkeypatch):
    class BlockingLLM:
        def __init__(self):
            self.config = SimpleNamespace(provider=LLMProvider.OPENAI, model="modele-test")
            self.cancelled = 0

        def prepare_context(self, messages, system_prompt=None):
            return messages, system_prompt

        async def stream_response(self, context, usage_sink=None):
            try:
                await asyncio.Event().wait()
                yield "inaccessible"
            finally:
                self.cancelled += 1

    llm = BlockingLLM()
    monkeypatch.setattr(board_module, "get_llm_service", lambda: llm)
    monkeypatch.setattr(board_module, "get_llm_service_for_provider", lambda *args, **kwargs: llm)
    monkeypatch.setattr(board_module, "_get_user_context", lambda: "")
    monkeypatch.setattr(BoardService, "_search_web_for_context", lambda *args, **kwargs: _empty_context())

    service = BoardService(FailingCommitSession())
    stream = service.deliberate(BoardRequest(
        question="Faut-il interrompre proprement ce traitement ?",
        mode=BoardMode.CLOUD,
        advisors=[AdvisorRole.ANALYST, AdvisorRole.STRATEGIST],
    ))

    while True:
        chunk = await anext(stream)
        if chunk.type == "advisor_start":
            break
    await asyncio.sleep(0)
    await stream.aclose()

    assert llm.cancelled >= 1


@pytest.mark.asyncio
async def test_decision_list_preserves_sovereign_mode(monkeypatch):
    decision = BoardDecision(
        id="decision-souveraine",
        question="Une question stratégique suffisamment longue",
        opinions=[AdvisorOpinion(
            role=AdvisorRole.ANALYST,
            name="L'Analyste",
            emoji="",
            content="Avis local",
        )],
        synthesis=BoardSynthesis(
            consensus_points=["Local"], divergence_points=[],
            recommendation="Continuer localement.", confidence="high", next_steps=["Tester"],
        ),
        mode="sovereign",
    )

    class FakeBoardService:
        def __init__(self, _session):
            pass

        async def list_decisions(self, limit=50):
            return [decision]

    monkeypatch.setattr(board_router, "BoardService", FakeBoardService)
    result = await board_router.list_decisions(limit=10, session=object())

    assert result[0].mode == "sovereign"


@pytest.mark.asyncio
async def test_history_preserves_sources_models_and_usage(monkeypatch, db_session):
    synthesis = json.dumps({
        "consensus_points": ["Tester"],
        "divergence_points": [],
        "recommendation": "Lancer un pilote.",
        "confidence": "high",
        "next_steps": ["Cadrer"],
    })
    llm = FakeLLM(["Avis documenté.", synthesis])
    monkeypatch.setattr(board_module, "get_llm_service", lambda: llm)
    monkeypatch.setattr(board_module, "get_llm_service_for_provider", lambda *args, **kwargs: llm)
    monkeypatch.setattr(board_module, "_get_user_context", lambda: "")

    async def web_context(service, _question):
        service._last_web_sources = [{
            "title": "Source vérifiable",
            "url": "https://example.test/source",
            "snippet": "Contexte factuel",
        }]
        return "Source: https://example.test/source"

    monkeypatch.setattr(BoardService, "_search_web_for_context", web_context)

    service = BoardService(db_session)
    chunks = [chunk async for chunk in service.deliberate(BoardRequest(
        question="Faut-il lancer un pilote documenté maintenant ?",
        advisors=[AdvisorRole.ANALYST],
        mode=BoardMode.CLOUD,
    ))]
    decision_id = next(chunk.content for chunk in chunks if chunk.type == "done")

    decision = await service.get_decision(decision_id)
    assert decision is not None
    assert decision.web_sources[0]["url"] == "https://example.test/source"
    assert decision.opinions[0].provider == "openai"
    assert decision.opinions[0].model == "modele-test"
    assert decision.opinions[0].input_tokens > 0
    assert decision.synthesis_usage["model"] == "modele-test"
