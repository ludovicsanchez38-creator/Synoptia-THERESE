"""B-1181 : l'erreur du fournisseur est traduite aussi dans la continuation après outil.

Attendu (B-1155, chat.py:2640-2645) : le texte brut du fournisseur
« API error: 529 » est traduit par message_fournisseur_pour_ecran avant
l'écran ; un texte vide retombe sur une phrase française.
Chemin mesuré : un outil de lecture (read_contact, sans carte de confirmation)
puis une erreur du fournisseur dans continue_with_tool_results.
"""

import json

import pytest
from app.services.providers.base import StreamEvent, ToolCall


def _faux_service(erreur_continuation):
    class FauxService:
        config = type(
            "C", (),
            {"provider": type("P", (), {"value": "anthropic"})(), "model": "test"},
        )()

        def prepare_context(self, messages, system_prompt=None, memory_context=None):
            return type(
                "Ctx", (),
                {"messages": messages, "system_prompt": system_prompt or ""},
            )()

        async def stream_response_with_tools(self, _context, _tools=None):
            yield StreamEvent(
                type="tool_call",
                tool_call=ToolCall(id="t1", name="read_contact", arguments={"query": "Martin"}),
            )
            yield StreamEvent(type="done", stop_reason="tool_use")

        async def continue_with_tool_results(
            self, context, assistant_content, tool_calls, tool_results, tools,
            prior_turns=None, assistant_content_brut=None,
        ):
            yield StreamEvent(type="error", content=erreur_continuation)

    return FauxService()


async def _chunks(client, monkeypatch, erreur):
    from app.routers import chat as chat_router

    monkeypatch.setattr(chat_router, "get_llm_service", lambda: _faux_service(erreur))
    reponse = await client.post("/api/chat/send", json={"message": "Qui est Martin ?", "stream": True})
    assert reponse.status_code == 200
    evenements = [
        json.loads(ligne.removeprefix("data: "))
        for ligne in reponse.text.splitlines()
        if ligne.startswith("data: ")
    ]
    # Le chemin est bien celui de la continuation : l'outil a tourné.
    assert any(e.get("type") == "tool_result" for e in evenements), evenements
    return evenements


@pytest.mark.asyncio
async def test_continuation_529_traduite_a_l_ecran(client, monkeypatch):
    from app.services.providers.base import message_erreur_http

    brut = message_erreur_http(None, 529)
    assert brut == "API error: 529"
    evenements = await _chunks(client, monkeypatch, brut)
    erreurs = [e["content"] for e in evenements if e.get("type") == "error"]
    assert erreurs, evenements
    assert not any("API error" in e for e in erreurs), f"chunks d'erreur à l'écran : {erreurs!r}"


@pytest.mark.asyncio
async def test_continuation_sans_texte_rend_une_phrase_francaise(client, monkeypatch):
    evenements = await _chunks(client, monkeypatch, None)
    erreurs = [e["content"] for e in evenements if e.get("type") == "error"]
    assert erreurs, evenements
    assert "Tool continuation error" not in erreurs, f"chunks d'erreur à l'écran : {erreurs!r}"


@pytest.mark.asyncio
async def test_temoin_premier_tour_traduit(client, monkeypatch):
    """Témoin : la branche du premier tour (B-1155) traduit bien."""
    from app.routers import chat as chat_router

    class Service:
        config = _faux_service(None).config
        prepare_context = _faux_service(None).prepare_context

        async def stream_response_with_tools(self, _context, _tools=None):
            yield StreamEvent(type="error", content="API error: 529")

    monkeypatch.setattr(chat_router, "get_llm_service", lambda: Service())
    reponse = await client.post("/api/chat/send", json={"message": "Salut", "stream": True})
    erreurs = [
        json.loads(ligne.removeprefix("data: "))["content"]
        for ligne in reponse.text.splitlines()
        if ligne.startswith("data: ") and '"type": "error"' in ligne
    ]
    assert erreurs and "API error" not in erreurs[0], erreurs
