"""B-1461 (recette P-146, lot 4, A1) : « Arrêter la réponse » interrompt le
flux côté client. Quand la requête se ferme avant que l'arrêt soit observé
par le moteur, Starlette annule la portée anyio du flux :
- l'enveloppe classait ce `CancelledError` en ÉCHEC (Travaux : « En échec ») ;
- la sauvegarde du texte partiel, attendue dans la portée annulée, était
  annulée à son tour : la réponse partielle, visible à l'écran, disparaissait
  au rechargement (journal : « non-checked-in connection »).

Le test rejoue ce départ comme Starlette : consommateur dans un groupe de
tâches anyio, portée annulée après le premier morceau de texte."""

import asyncio

import anyio
import pytest
from app.models.processing import EtatTache, ProcessingTask
from sqlmodel import select


def _evenement(type_: str, contenu: str = ""):
    return type("E", (), {"type": type_, "content": contenu, "tool_call": None,
                          "stop_reason": "stop" if type_ == "done" else None,
                          "input_tokens": None, "output_tokens": None, "usage_estimated": True})()


@pytest.mark.asyncio
async def test_le_depart_du_client_garde_le_partiel_et_n_est_pas_un_echec(client, monkeypatch):
    from app.models.database import get_session_context
    from app.models.entities import Message
    from app.routers import chat as chat_router

    bloque = asyncio.Event()

    class FauxService:
        config = type("C", (), {"provider": type("P", (), {"value": "ollama"})(), "model": "test"})()

        def prepare_context(self, messages, system_prompt=None, memory_context=None):
            return type("Ctx", (), {"messages": messages, "system_prompt": system_prompt or ""})()

        async def stream_response_with_tools(self, _context, _tools=None):
            yield _evenement("text", "Début de réponse longue ")
            await bloque.wait()  # le modèle réfléchit encore quand le client part
            yield _evenement("done")

    monkeypatch.setattr(chat_router, "get_llm_service", lambda: FauxService())
    conversation = (await client.post("/api/chat/conversations", json={"title": "Départ"})).json()["id"]
    chat_router._register_generation(conversation)

    premier_texte = anyio.Event()
    async with get_session_context() as session:
        flux = chat_router._stream_response(conversation, "Explique en dix points", session, [])

        async def consommer():
            async for morceau in flux:
                if '"type": "text"' in morceau:
                    premier_texte.set()

        async with anyio.create_task_group() as groupe:
            groupe.start_soon(consommer)
            with anyio.fail_after(5):
                await premier_texte.wait()
            groupe.cancel_scope.cancel()  # Starlette : le client est parti
        await flux.aclose()

    async with get_session_context() as session:
        messages = (await session.execute(
            select(Message).where(Message.conversation_id == conversation, Message.role == "assistant")
        )).scalars().all()
        tache = (await session.execute(
            select(ProcessingTask).where(ProcessingTask.type == "chat", ProcessingTask.conversation_id == conversation)
        )).scalars().first()
    assert any("Début de réponse" in m.content for m in messages), "le partiel doit survivre au rechargement"
    assert tache is not None and tache.state == EtatTache.CANCELLED, tache.state if tache else None
