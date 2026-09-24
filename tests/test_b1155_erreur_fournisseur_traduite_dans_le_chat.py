"""B-1155 (cycle 13) : le chat relayait « API error: 529 » brut.

`message_erreur_http` rend « API error: {code} » pour tout 5xx (forme que le
disjoncteur reconnaît), et B-1147 (0.75) ne traduisait ce texte que dans
`generate_content`. Le chat en flux l'affichait et le gardait dans
l'historique ; le chemin qui lève `ErreurPourEcran` le laissait aussi passer.
La traduction se fait à la frontière de l'écran, après le comptage de panne.
"""

import json

import pytest


def _faux_service(evenements):
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
            for evenement in evenements():
                yield evenement

    return FauxService()


def _erreur(contenu):
    return type("E", (), {"type": "error", "content": contenu, "tool_call": None,
                          "stop_reason": None, "input_tokens": None,
                          "output_tokens": None, "usage_estimated": True})()


@pytest.mark.asyncio
async def test_le_chat_en_flux_ne_montre_pas_api_error_529(client, monkeypatch):
    from app.routers import chat as chat_router
    from app.services.providers.base import message_erreur_http

    # Le texte exact qu'un fournisseur émet pour une surcharge 529.
    brut = message_erreur_http(None, 529)
    assert brut == "API error: 529"

    monkeypatch.setattr(
        chat_router, "get_llm_service",
        lambda: _faux_service(lambda: [_erreur(brut)]),
    )
    reponse = await client.post(
        "/api/chat/send", json={"message": "Salut", "stream": True},
    )
    assert reponse.status_code == 200
    evenements = [
        json.loads(ligne.removeprefix("data: "))
        for ligne in reponse.text.splitlines()
        if ligne.startswith("data: ")
    ]
    erreurs = [e for e in evenements if e.get("type") == "error"]
    assert erreurs, f"aucun chunk d'erreur : {evenements}"
    conversation_id = erreurs[0].get("conversation_id")
    historique = await client.get(f"/api/chat/conversations/{conversation_id}/messages")
    contenus = [m["content"] for m in historique.json()]
    assert "API error" not in erreurs[0]["content"] and not any(
        "API error" in c for c in contenus
    ), (
        f"chunk d'erreur affiché à l'écran : {erreurs[0]['content']!r} ; "
        f"historique persisté : {contenus!r}"
    )


@pytest.mark.asyncio
async def test_stream_response_raise_on_error_leve_un_message_traduit(monkeypatch):
    """Chemin non streamé et recherche approfondie (llm.py:940)."""
    from app.services.error_handler import ErreurPourEcran, message_pour_ecran
    from app.services.llm import LLMService

    service = LLMService.__new__(LLMService)
    service.config = type(
        "C", (), {"provider": type("P", (), {"value": "anthropic"})(), "model": "x"}
    )()

    async def faux_flux(self, context, tools=None, enable_grounding=True, config=None):
        yield _erreur("API error: 529")

    monkeypatch.setattr(LLMService, "stream_response_with_tools", faux_flux)
    import app.services.llm as llm_mod

    class FauxDisjoncteur:
        def record_failure(self, *a, **k):
            pass

    monkeypatch.setattr(llm_mod, "get_circuit_breaker", lambda: FauxDisjoncteur())
    with pytest.raises(ErreurPourEcran) as info:
        async for _ in service.stream_response(object(), raise_on_error=True):
            pass
    ecran = message_pour_ecran(info.value, ou="pendant la génération")
    assert "API error" not in ecran, f"message à l'écran : {ecran!r}"


@pytest.mark.asyncio
async def test_le_disjoncteur_voit_toujours_la_forme_brute(monkeypatch):
    """Témoin : traduire pour l'écran ne doit pas cacher la panne au disjoncteur."""
    from app.services.error_handler import ErreurPourEcran
    from app.services.llm import LLMService

    service = LLMService.__new__(LLMService)
    service.config = type(
        "C", (), {"provider": type("P", (), {"value": "anthropic"})(), "model": "x"}
    )()

    async def faux_flux(self, context, tools=None, enable_grounding=True, config=None):
        yield _erreur("API error: 529")

    monkeypatch.setattr(LLMService, "stream_response_with_tools", faux_flux)
    import app.services.llm as llm_mod

    pannes: list[str] = []

    class Disjoncteur:
        def record_failure(self, fournisseur, texte):
            pannes.append(texte)

    monkeypatch.setattr(llm_mod, "get_circuit_breaker", lambda: Disjoncteur())
    with pytest.raises(ErreurPourEcran):
        async for _ in service.stream_response(object(), raise_on_error=True):
            pass
    assert pannes == ["API error: 529"]
