"""La provenance survit aux écritures, corrections et anciens schémas."""

import json
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from unittest.mock import AsyncMock

import pytest
from app.models.entities import Conversation, Message
from app.services import memory_cards
from app.services.context import ContextWindow
from app.services.providers.base import Message as LLMMessage
from app.services.providers.base import ToolCall

from tests.test_chat_tool_confirmation import _FakeLLM, _parse_chunks


async def test_fiche_entriere_et_correction_gardent_origine(db_session):
    conversation = Conversation(title="Fictif")
    db_session.add(conversation)
    await db_session.flush()
    source = Message(
        conversation_id=conversation.id,
        role="user",
        content="Je préfère des devis courts",
        extra_data=json.dumps({"provenance_documents": "sans_document"}),
    )
    db_session.add(source)
    await db_session.commit()
    fiche = await memory_cards.ecrire(
        {
            "kind": "preference",
            "subject": "Maison Ambre",
            "title": "Devis Maison Ambre",
            "content": source.content,
        },
        automatique=True,
        conversation_id=conversation.id,
        message_id=source.id,
        contient_documents=True,
    )
    assert fiche["provenance_documents"] == "documents"
    corrigee = await memory_cards.ecrire(
        {
            "id": fiche["id"],
            "version": 1,
            "title": "Devis court",
            "provenance_documents": "sans_document",
        }
    )
    assert corrigee["provenance_documents"] == "documents"


def test_migration_conserve_fiches_et_marque_inconnu(tmp_path):
    import sqlalchemy as sa
    from alembic.migration import MigrationContext
    from alembic.operations import Operations

    path = Path("src/backend/alembic/versions/t4memoire03_provenance_fiches.py")
    spec = spec_from_file_location("migration_t6", path)
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    engine = sa.create_engine("sqlite:///" + str(tmp_path / "fiches.db"))
    with engine.begin() as conn:
        conn.exec_driver_sql("CREATE TABLE memory_cards (id TEXT, title TEXT, content TEXT)")
        conn.exec_driver_sql("INSERT INTO memory_cards VALUES ('a', 'Maison Ambre', 'Fictif')")
        with Operations.context(MigrationContext.configure(conn)):
            module.upgrade()
            module.upgrade()
        assert conn.exec_driver_sql("SELECT * FROM memory_cards").one() == (
            "a",
            "Maison Ambre",
            "Fictif",
            "inconnue",
        )


@pytest.mark.parametrize("documentaire", [False, True, None])
@pytest.mark.parametrize(
    "outil",
    ["create_contact", "create_project", "create_task", "create_invoice", "create_calendar_event"],
)
async def test_ecriture_ancienne_sans_provenance_ne_blanchit_pas_document(
    client, monkeypatch, outil, documentaire
):
    from app.routers import chat

    executer = AsyncMock(return_value="Écrit")
    monkeypatch.setattr(chat, "execute_memory_tool", executer)
    monkeypatch.setattr(chat, "execute_workspace_tool", executer)
    context = ContextWindow(
        messages=[LLMMessage(role="user", content="Fictif")], contient_documents=documentaire
    )
    appel = ToolCall(id="appel-fictif", name=outil, arguments={"title": "Maison Ambre"})
    chunks = _parse_chunks(
        [
            e
            async for e in chat._execute_tools_and_continue(
                _FakeLLM(),
                None,
                context,
                "",
                [appel],
                [{"type": "function", "function": {"name": outil}}],
                None,
                3,
            )
        ]
    )
    carte = next(e["confirmation"] for e in chunks if e["type"] == "confirmation_required")
    reponse = await client.post(
        "/api/chat/confirm-tool",
        json={"confirmation_id": carte["confirmation_id"], "approved": True},
    )
    if documentaire is not False:
        assert reponse.json()["status"] == "refused"
        assert "document" in reponse.json()["result"]
        executer.assert_not_called()
    else:
        assert reponse.json()["status"] == "executed"
        executer.assert_awaited_once()


@pytest.mark.parametrize('destination', ['openai', 'mistral'])
@pytest.mark.parametrize('origine', ['documents', 'inconnue'])
async def test_fiche_retrait_tardif_verifie_au_transport(client, monkeypatch, destination, origine):
    import httpx
    from app.services import memory_card_context
    from app.services.consentements import enregistrer_accord
    from app.services.error_handler import ErreurPourEcran
    from app.services.llm import LLMConfig, LLMProvider, LLMService
    from app.services.providers.mistral import MistralProvider
    from app.services.providers.openai import OpenAIProvider

    for purpose in ('llm', 'documents'):
        enregistrer_accord(purpose, destination, True, '3', ['memory_cards_r2_v1'])
    fiches = [{'id': 'fiche-fictive', 'kind': 'preference', 'title': 'Maison Ambre',
               'content': 'Devis courts', 'provenance_documents': origine}]
    monkeypatch.setattr(memory_card_context, 'lire_pour_chat', AsyncMock(return_value=fiches))
    envois = []
    async def transport(req):
        envois.append(req.content)
        return httpx.Response(500)
    async with httpx.AsyncClient(transport=httpx.MockTransport(transport)) as http:
        svc = LLMService(LLMConfig(LLMProvider(destination), 'fictif', api_key='factice'))
        svc._provider = (OpenAIProvider if destination == 'openai' else MistralProvider)(svc.config, http)
        async def retirer():
            enregistrer_accord('documents', destination, False, '3', [])
        monkeypatch.setattr(svc, '_ensure_provider', retirer)
        ctx = ContextWindow(messages=[LLMMessage(role='user', content='Bonjour')])
        memory_card_context.attacher_relecture(ctx, ctx.messages, None, scope='global', scope_id=None,
                                               conversation_id='fictif', query='devis', grants=[])
        with pytest.raises(ErreurPourEcran, match='documents'):
            async for _ in svc.stream_response_with_tools(ctx):
                pass
        assert not envois
