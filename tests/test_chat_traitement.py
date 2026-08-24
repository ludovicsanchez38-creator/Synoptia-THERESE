"""Phase 4 du chantier 0.46 - le chat par génération, honnête jusqu'au bout.

Contrats (design V2.1) :
- une ligne ProcessingTask PAR GÉNÉRATION LLM, créée immédiatement,
  `ProcessingTask.id` EST le generation_id, émis dans le SSE ;
- la façade /api/chat/cancel/{conversation_id} (frontend J1b déployé) résout
  la génération active puis passe par le service canonique ;
- sur annulation, le message PARTIEL est persisté (aujourd'hui il disparaît),
  mais aucun effet de skill ni d'outil n'est produit ;
- après les outils, aucune NOUVELLE étape n'est lancée si l'arrêt est demandé.
"""

import json

import pytest
from app.models.processing import EtatTache, ProcessingTask
from sqlmodel import select


def _faux_service(evenements):
    class FauxService:
        config = type(
            "C", (),
            {"provider": type("P", (), {"value": "ollama"})(), "model": "test"},
        )()

        def prepare_context(self, messages, system_prompt=None, memory_context=None):
            return type(
                "Ctx", (),
                {"messages": messages, "system_prompt": system_prompt or ""},
            )()

        async def stream_response_with_tools(self, _context, _tools=None):
            for evenement in evenements():
                yield evenement

    return FauxService()


def _texte(contenu):
    return type("E", (), {"type": "text", "content": contenu, "tool_call": None,
                          "stop_reason": None, "input_tokens": None,
                          "output_tokens": None, "usage_estimated": True})()


def _fin():
    return type("E", (), {"type": "done", "content": "", "tool_call": None,
                          "stop_reason": "stop", "input_tokens": None,
                          "output_tokens": None, "usage_estimated": True})()


async def _generation_de(conversation_id: str) -> ProcessingTask | None:
    from app.models.database import get_session_context

    async with get_session_context() as session:
        resultat = await session.execute(
            select(ProcessingTask).where(
                ProcessingTask.type == "chat",
                ProcessingTask.conversation_id == conversation_id,
            ).order_by(ProcessingTask.created_at.desc())
        )
        return resultat.scalars().first()


class TestLaGenerationEstUnTraitement:
    @pytest.mark.asyncio
    async def test_le_sse_emet_le_generation_id_et_la_ligne_finit_done(
        self, client, monkeypatch
    ):
        from app.routers import chat as chat_router

        monkeypatch.setattr(
            chat_router, "get_llm_service",
            lambda: _faux_service(lambda: [_texte("Bonjour "), _texte("Ludo."), _fin()]),
        )

        reponse = await client.post(
            "/api/chat/send",
            json={"message": "Salut", "stream": True},
        )
        assert reponse.status_code == 200

        evenement = next(
            (json.loads(ligne.removeprefix("data: "))
             for ligne in reponse.text.splitlines()
             if ligne.startswith("data: ") and '"generation"' in ligne),
            None,
        )
        assert evenement is not None, "le SSE doit émettre le generation_id"
        assert evenement["generation_id"]

        from app.services import traitements

        ligne = await traitements.lire(evenement["generation_id"])
        assert ligne is not None
        assert ligne.type == "chat"
        assert ligne.state == EtatTache.DONE

    @pytest.mark.asyncio
    async def test_la_facade_cancel_passe_par_le_service_canonique(
        self, client, monkeypatch
    ):
        """Le frontend J1b envoie un conversation_id : la façade résout la
        génération active et la demande d'arrêt suit le chemin canonique."""
        from app.routers import chat as chat_router
        from app.services import task_registry, traitements

        conversation = "conv-facade"
        chat_router._register_generation(conversation)
        handle = await traitements.creer_traitement(
            type="chat", label="essai", conversation_id=conversation,
        )
        await handle.demarrer()
        await handle.lier_adaptateur(
            task_registry.AnnulationCooperative(
                poser_drapeau=lambda: chat_router._cancel_generation(conversation)
            )
        )

        reponse = await client.post(f"/api/chat/cancel/{conversation}")

        assert reponse.status_code == 200
        assert reponse.json()["cancelled"] is True
        assert chat_router._is_cancelled(conversation) is True, (
            "le drapeau historique doit être posé via l'adaptateur"
        )
        assert (await traitements.lire(handle.id)).state == EtatTache.CANCEL_REQUESTED

        await handle.terminer(EtatTache.CANCELLED)
        chat_router._unregister_generation(conversation)

    @pytest.mark.asyncio
    async def test_l_annulation_persiste_le_message_partiel(
        self, client, monkeypatch
    ):
        """Aujourd'hui le partiel disparaît au rechargement - contrat V2.1 :
        le texte déjà produit est persisté, les effets (skill, outils) non."""
        from app.models.entities import Message
        from app.routers import chat as chat_router

        capture: dict[str, str] = {}

        def evenements():
            yield _texte("Début de réponse ")
            # l'utilisateur clique Arrêter en plein flux
            chat_router._cancel_generation(capture["conversation"])
            yield _texte("suite jamais montrée")
            yield _fin()

        monkeypatch.setattr(
            chat_router, "get_llm_service", lambda: _faux_service(evenements),
        )

        # conversation créée d'avance pour en connaître l'identifiant
        creation = await client.post(
            "/api/chat/conversations", json={"title": "Partiel"},
        )
        conversation = creation.json()["id"]
        capture["conversation"] = conversation

        reponse = await client.post(
            "/api/chat/send",
            json={"message": "Long récit", "stream": True,
                  "conversation_id": conversation},
        )
        assert reponse.status_code == 200
        assert '"cancelled"' in reponse.text

        from app.models.database import get_session_context

        async with get_session_context() as session:
            resultat = await session.execute(
                select(Message).where(
                    Message.conversation_id == conversation,
                    Message.role == "assistant",
                )
            )
            messages = list(resultat.scalars().all())
        assert messages, "le partiel doit survivre au rechargement"
        assert "Début de réponse" in messages[-1].content

        generation = await _generation_de(conversation)
        assert generation is not None
        assert generation.state == EtatTache.CANCELLED
