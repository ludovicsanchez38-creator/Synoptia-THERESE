"""B-1513 : la synthèse d'une recherche approfondie s'écrivait dans une
conversation supprimée pendant la recherche.

Le tiroir permet de supprimer la conversation affichée pendant sa
recherche ; la synthèse s'écrivait ensuite par sa propre session, hors du
point d'écriture de B-1494 : un message orphelin, invisible mais conservé.
"""

import json

import pytest
from sqlmodel import select


@pytest.mark.asyncio
async def test_la_synthese_n_est_pas_ecrite_dans_une_conversation_supprimee(client, monkeypatch):
    from app.models.database import get_session_context
    from app.models.entities import Conversation, Message
    from app.routers import chat as chat_router
    from app.services import deep_research as module
    from app.services.deep_research import ResearchProgress

    async def recherche(_question, _llm, max_queries=6):
        yield ResearchProgress(type="synthesizing", content="Premier constat. ")
        async with get_session_context() as autre:
            derniere = (await autre.execute(
                select(Conversation).order_by(Conversation.created_at.desc())
            )).scalars().first()
            await autre.delete(derniere)
            await autre.commit()
        yield ResearchProgress(type="done", content="Synthèse complète.")

    monkeypatch.setattr(module, "deep_research", recherche)
    monkeypatch.setattr(chat_router, "get_llm_service", lambda: type("S", (), {
        "config": type("C", (), {"provider": type("P", (), {"value": "ollama"})(), "model": "test"})(),
    })())

    conversation_id = None
    async with get_session_context() as session:
        reponse = await chat_router.deep_research_endpoint(
            chat_router.DeepResearchRequest(question="Marché des menuiseries en Provence"), session,
        )
        async for morceau in reponse.body_iterator:
            if conversation_id is None and '"conversation_id"' in morceau:
                conversation_id = json.loads(morceau.removeprefix("data: "))["content"]

    assert conversation_id is not None
    async with get_session_context() as session:
        orphelins = (await session.execute(
            select(Message).where(Message.conversation_id == conversation_id)
        )).scalars().all()
    assert orphelins == []
