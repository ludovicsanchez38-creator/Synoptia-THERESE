"""Une recherche vide ne doit pas devenir une réponse inventée."""

import json
from unittest.mock import AsyncMock, MagicMock

import pytest
from app.routers import chat
from app.services.context import ContextWindow
from app.services.providers.base import StreamEvent, ToolCall


class ModeleInventeur:
    config = None

    def __init__(self):
        self.continuations = 0

    def prepare_context(self, messages):
        return ContextWindow(messages=messages)

    async def continue_with_tool_results(self, *args, **kwargs):
        self.continuations += 1
        yield StreamEvent(type="text", content="Le fichier décrit un comité imaginaire.")
        yield StreamEvent(type="done", stop_reason="end_turn")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("nom", "resultat"),
    [
        ("search_files", '{"found": false, "total": 0, "documents": []}'),
        ("search_emails", "Aucun email trouve pour la recherche 'comité'."),
        ("search_invoices", "Aucune facture ni devis local ne correspond à « comité »."),
    ],
)
async def test_recherche_vide_ne_devient_pas_un_contenu_invente(monkeypatch, nom, resultat):
    modele = ModeleInventeur()
    monkeypatch.setattr(chat, "_perimetre_de_conversation", AsyncMock(return_value=("global", None)))
    monkeypatch.setattr(chat, "execute_memory_tool", AsyncMock(return_value=resultat))
    monkeypatch.setattr(chat, "execute_workspace_tool", AsyncMock(return_value=resultat))
    appel = ToolCall(id="recherche", name=nom, arguments={"query": "comité"})
    outils = [{"type": "function", "function": {"name": nom}}]

    evenements = [json.loads(bloc.removeprefix("data: ")) async for bloc in
                  chat._execute_tools_and_continue(
                      modele, None, ContextWindow(messages=[]), "", [appel], outils,
                      "c-test", 3, session=object(),
                  )]
    texte = " ".join(e.get("content", "") for e in evenements if e["type"] == "text")

    assert "aucun" in texte.lower() or "rien trouvé" in texte.lower()
    assert "comité imaginaire" not in texte
    assert modele.continuations == 0


@pytest.mark.asyncio
async def test_recherche_web_confirmee_vide_ne_devient_pas_un_contenu_invente(monkeypatch):
    modele = ModeleInventeur()
    monkeypatch.setattr(chat, "get_llm_service", lambda: modele)
    monkeypatch.setattr(chat, "filtrer_historique", lambda messages, config: (messages, None))
    monkeypatch.setattr(chat, "_attribution", lambda service: ("local", "fictif"))
    monkeypatch.setattr(chat, "get_token_tracker", lambda: MagicMock())

    reponse = await chat._repondre_apres_recherche(
        {"query": "comité", "_provenance_documents": "sans_document"},
        "Aucun résultat trouvé pour: comité", None, object(),
    )

    assert "aucun" in reponse.lower() or "rien trouvé" in reponse.lower()
    assert "comité imaginaire" not in reponse
    assert modele.continuations == 0


@pytest.mark.asyncio
async def test_resultat_non_vide_continue_normalement(monkeypatch):
    modele = ModeleInventeur()
    monkeypatch.setattr(chat, "_perimetre_de_conversation", AsyncMock(return_value=("global", None)))
    monkeypatch.setattr(chat, "execute_memory_tool", AsyncMock(return_value=(
        '{"found": true, "total": 1, "documents": [{"nom": "contexte.md"}]}'
    )))
    appel = ToolCall(id="recherche", name="search_files", arguments={"query": "contexte"})
    outils = [{"type": "function", "function": {"name": "search_files"}}]
    evenements = [json.loads(bloc.removeprefix("data: ")) async for bloc in
                  chat._execute_tools_and_continue(
                      modele, None, ContextWindow(messages=[]), "", [appel], outils,
                      "c-test", 3, session=object(),
                  )]
    assert modele.continuations == 1
    assert any(e["type"] == "text" and "comité imaginaire" in e["content"] for e in evenements)
