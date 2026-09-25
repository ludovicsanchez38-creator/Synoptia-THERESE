"""P-122 (Ludo, 25/09/2026) : Claude Opus 5.5 entre dans THÉRÈSE. Prérequis.

Sur `claude-opus-5-5`, la réflexion adaptative est TOUJOURS active : chaque
réponse peut commencer par des blocs `thinking` (texte vide par défaut, plus
une `signature`). Dans une boucle d'outils, la doc exige de renvoyer le
message de l'assistant tel que reçu : « the API rejects edited, reordered, or
partially dropped thinking blocks with a 400 error »
(platform.claude.com/docs/en/models/opus-5-5/migration-guide, relevé le
25/09/2026).

Le fournisseur Anthropic ignorait ces blocs et reconstruisait le tour avec le
seul texte et les `tool_use` : chaque action (contact, agenda) aurait échoué au
second tour. Le transport `assistant_content_brut` (créé en 0.48 pour Mistral)
porte désormais le contenu brut du tour, rejoué tel quel ; un tour sans
réflexion garde la reconstruction historique.
"""

import json

import pytest
from app.services.providers.anthropic import AnthropicProvider
from app.services.providers.base import LLMConfig, LLMProvider, ToolCall, ToolResult, ToolTurn

from tests.test_provider_tools import _collect, _FakeClient


def _sse(evenement: dict) -> str:
    return f"data: {json.dumps(evenement)}"


def _flux(*blocs: list[dict]) -> list[str]:
    """Un message Anthropic en SSE : chaque bloc = [start, deltas..., stop]."""
    lignes = [_sse({"type": "message_start", "message": {"usage": {"input_tokens": 10}}})]
    for bloc in blocs:
        lignes += [_sse(e) for e in bloc]
    lignes += [
        _sse({"type": "message_delta", "delta": {"stop_reason": "tool_use"}, "usage": {"output_tokens": 5}}),
        _sse({"type": "message_stop"}),
    ]
    return lignes


def _reflexion(index: int, signature: str, texte: str = "") -> list[dict]:
    deltas = [{"type": "content_block_delta", "index": index, "delta": {"type": "thinking_delta", "thinking": texte}}] if texte else []
    return [
        {"type": "content_block_start", "index": index, "content_block": {"type": "thinking", "thinking": "", "signature": ""}},
        *deltas,
        {"type": "content_block_delta", "index": index, "delta": {"type": "signature_delta", "signature": signature}},
        {"type": "content_block_stop", "index": index},
    ]


def _texte(index: int, texte: str) -> list[dict]:
    return [
        {"type": "content_block_start", "index": index, "content_block": {"type": "text", "text": ""}},
        {"type": "content_block_delta", "index": index, "delta": {"type": "text_delta", "text": texte}},
        {"type": "content_block_stop", "index": index},
    ]


def _outil(index: int, ident: str, nom: str, arguments: dict) -> list[dict]:
    return [
        {"type": "content_block_start", "index": index, "content_block": {"type": "tool_use", "id": ident, "name": nom, "input": {}}},
        {"type": "content_block_delta", "index": index, "delta": {"type": "input_json_delta", "partial_json": json.dumps(arguments)}},
        {"type": "content_block_stop", "index": index},
    ]


def _fournisseur(client: _FakeClient, modele: str = "claude-opus-5-5") -> AnthropicProvider:
    return AnthropicProvider(
        LLMConfig(provider=LLMProvider.ANTHROPIC, model=modele, api_key="k"),
        client=client,
    )


ATTENDU = [
    {"type": "thinking", "thinking": "", "signature": "sig-1"},
    {"type": "text", "text": "Je regarde."},
    {"type": "tool_use", "id": "tu_1", "name": "read_contact", "input": {"name": "Hélène"}},
]


@pytest.mark.asyncio
async def test_le_tour_brut_porte_la_reflexion_signee_dans_l_ordre():
    client = _FakeClient(_flux(_reflexion(0, "sig-1"), _texte(1, "Je regarde."), _outil(2, "tu_1", "read_contact", {"name": "Hélène"})))
    evenements = await _collect(_fournisseur(client).stream("system", [{"role": "user", "content": "Hélène ?"}], None))

    appels = [e for e in evenements if e.type == "tool_call"]
    assert len(appels) == 1
    assert appels[0].assistant_content_brut == ATTENDU
    assert [e.content for e in evenements if e.type == "text"] == ["Je regarde."], "la réflexion ne s'affiche jamais"


@pytest.mark.asyncio
async def test_deux_appels_d_outils_partagent_le_tour_complet():
    client = _FakeClient(_flux(
        _reflexion(0, "sig-2"),
        _outil(1, "tu_1", "read_contact", {"name": "Hélène"}),
        _outil(2, "tu_2", "list_projects", {}),
    ))
    evenements = await _collect(_fournisseur(client).stream("system", [{"role": "user", "content": "?"}], None))

    appels = [e for e in evenements if e.type == "tool_call"]
    assert len(appels) == 2
    for appel in appels:
        assert [b["type"] for b in appel.assistant_content_brut] == ["thinking", "tool_use", "tool_use"]


@pytest.mark.asyncio
async def test_une_reflexion_masquee_est_gardee_telle_quelle():
    redacted = [
        {"type": "content_block_start", "index": 0, "content_block": {"type": "redacted_thinking", "data": "chiffre"}},
        {"type": "content_block_stop", "index": 0},
    ]
    client = _FakeClient(_flux(redacted, _outil(1, "tu_1", "read_contact", {})))
    evenements = await _collect(_fournisseur(client).stream("system", [{"role": "user", "content": "?"}], None))

    brut = next(e for e in evenements if e.type == "tool_call").assistant_content_brut
    assert brut[0] == {"type": "redacted_thinking", "data": "chiffre"}


@pytest.mark.asyncio
async def test_sans_reflexion_le_tour_n_a_pas_de_contenu_brut():
    client = _FakeClient(_flux(_texte(0, "Je regarde."), _outil(1, "tu_1", "read_contact", {})))
    evenements = await _collect(_fournisseur(client, "claude-opus-4-8").stream("system", [{"role": "user", "content": "?"}], None))

    assert next(e for e in evenements if e.type == "tool_call").assistant_content_brut is None


@pytest.mark.asyncio
async def test_la_reprise_rejoue_le_tour_tel_que_recu():
    client = _FakeClient([_sse({"type": "message_stop"})])
    await _collect(_fournisseur(client).continue_with_tool_results(
        "system",
        [{"role": "user", "content": "Hélène ?"}],
        assistant_content="Je regarde.",
        tool_calls=[ToolCall(id="tu_1", name="read_contact", arguments={"name": "Hélène"})],
        tool_results=[ToolResult(tool_call_id="tu_1", result="fiche")],
        tools=None,
        assistant_content_brut=ATTENDU,
    ))

    envoye = client.last_request["json"]["messages"]
    assistant = [m for m in envoye if m["role"] == "assistant"]
    assert assistant[-1]["content"] == ATTENDU
    assert envoye[-1]["content"][0] == {"type": "tool_result", "tool_use_id": "tu_1", "content": "fiche", "is_error": False}


@pytest.mark.asyncio
async def test_les_tours_precedents_rejouent_aussi_leur_reflexion():
    precedent = [
        {"type": "thinking", "thinking": "", "signature": "sig-0"},
        {"type": "tool_use", "id": "tu_0", "name": "read_contact", "input": {}},
    ]
    client = _FakeClient([_sse({"type": "message_stop"})])
    await _collect(_fournisseur(client).continue_with_tool_results(
        "system",
        [{"role": "user", "content": "?"}],
        assistant_content="Je regarde.",
        tool_calls=[ToolCall(id="tu_1", name="read_contact", arguments={"name": "Hélène"})],
        tool_results=[ToolResult(tool_call_id="tu_1", result="fiche")],
        tools=None,
        prior_turns=[ToolTurn(
            assistant_content="",
            tool_calls=[ToolCall(id="tu_0", name="read_contact", arguments={})],
            tool_results=[ToolResult(tool_call_id="tu_0", result="rien")],
            assistant_content_brut=precedent,
        )],
        assistant_content_brut=ATTENDU,
    ))

    assistants = [m["content"] for m in client.last_request["json"]["messages"] if m["role"] == "assistant"]
    assert assistants == [precedent, ATTENDU]


@pytest.mark.asyncio
async def test_sans_contenu_brut_la_reprise_reconstruit_comme_avant():
    client = _FakeClient([_sse({"type": "message_stop"})])
    await _collect(_fournisseur(client, "claude-opus-4-8").continue_with_tool_results(
        "system",
        [{"role": "user", "content": "?"}],
        assistant_content="Je regarde.",
        tool_calls=[ToolCall(id="tu_1", name="read_contact", arguments={"name": "Hélène"})],
        tool_results=[ToolResult(tool_call_id="tu_1", result="fiche")],
        tools=None,
    ))

    assistant = [m for m in client.last_request["json"]["messages"] if m["role"] == "assistant"][-1]
    assert assistant["content"] == [
        {"type": "text", "text": "Je regarde."},
        {"type": "tool_use", "id": "tu_1", "name": "read_contact", "input": {"name": "Hélène"}},
    ]
