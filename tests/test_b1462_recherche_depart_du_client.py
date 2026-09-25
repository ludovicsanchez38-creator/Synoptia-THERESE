"""B-1462 (analyse de B-1461) : la recherche approfondie a le même motif que
le chat. Quand le client part pendant la synthèse, Starlette annule la
portée anyio du flux ; la sauvegarde de la synthèse partielle et l'écriture
de l'état final sont attendues DANS cette portée, et sont annulées à leur
tour. Test rejouant le départ comme Starlette."""

import asyncio

import anyio
import pytest
from app.models.processing import EtatTache, ProcessingTask
from sqlmodel import select


@pytest.mark.asyncio
async def test_le_depart_du_client_garde_la_synthese_partielle(client, monkeypatch):
    from app.models.database import get_session_context
    from app.models.entities import Message
    from app.routers import chat as chat_router
    from app.services import deep_research as module
    from app.services.deep_research import ResearchProgress

    bloque = asyncio.Event()

    async def recherche_lente(_question, _llm, max_queries=6):
        yield ResearchProgress(type="synthesizing", content="Premier constat de la synthèse. ")
        await bloque.wait()
        yield ResearchProgress(type="done")

    monkeypatch.setattr(module, "deep_research", recherche_lente)
    monkeypatch.setattr(chat_router, "get_llm_service", lambda: type("S", (), {
        "config": type("C", (), {"provider": type("P", (), {"value": "ollama"})(), "model": "test"})(),
    })())

    premier_texte = anyio.Event()
    async with get_session_context() as session:
        reponse = await chat_router.deep_research_endpoint(
            chat_router.DeepResearchRequest(question="Marché des menuiseries en Provence"), session,
        )
        flux = reponse.body_iterator
        conversation = {"id": None}

        async def consommer():
            async for morceau in flux:
                if '"conversation_id"' in morceau and conversation["id"] is None:
                    import json
                    conversation["id"] = json.loads(morceau.removeprefix("data: "))["content"]
                if '"type": "text"' in morceau:
                    premier_texte.set()

        async with anyio.create_task_group() as groupe:
            groupe.start_soon(consommer)
            with anyio.fail_after(5):
                await premier_texte.wait()
            groupe.cancel_scope.cancel()
        await flux.aclose()

    async with get_session_context() as session:
        messages = (await session.execute(
            select(Message).where(Message.conversation_id == conversation["id"], Message.role == "assistant")
        )).scalars().all()
        tache = (await session.execute(
            select(ProcessingTask).where(ProcessingTask.type == "deep-research",
                                         ProcessingTask.conversation_id == conversation["id"])
        )).scalars().first()
    assert any("Premier constat" in m.content for m in messages), "la synthèse partielle doit survivre"
    assert tache is not None and tache.state == EtatTache.CANCELLED, tache.state if tache else None
