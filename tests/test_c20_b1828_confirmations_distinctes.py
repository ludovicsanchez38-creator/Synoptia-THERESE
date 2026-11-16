"""Deux envois différents doivent toujours recevoir deux confirmations."""

import json
from unittest.mock import AsyncMock, MagicMock
from types import SimpleNamespace

import pytest
from app.routers import chat
from app.services.context import ContextWindow
from app.services.providers.base import StreamEvent, ToolCall


class Modele:
    config = SimpleNamespace(provider=SimpleNamespace(value="ollama"), model="fictif")

    async def continue_with_tool_results(self, *args, **kwargs):
        yield StreamEvent(type="done", stop_reason="end_turn")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("noms", "premier", "second"),
    [
        (("send_email", "send_email"), {"bcc": "un@exemple.fr"}, {"bcc": "deux@exemple.fr"}),
        (("send_email", "send_email"), {"attachments": ["a.pdf"]}, {"attachments": ["b.pdf"]}),
        (("send_email", "send_email"), {"is_html": False}, {"is_html": True}),
        (("send_email", "courrier__send_email"), {}, {}),
        (("serveur-a__send_email", "serveur-b__send_email"), {}, {}),
        (("send_email", "send_email"), {"subject": "A|B", "body": "C"},
         {"subject": "A", "body": "B|C"}),
        (("send_email", "send_email"), {"body": "texte"}, {"body": " texte"}),
        (("send_email", "send_email"), {"content": "premier"}, {"content": "second"}),
    ],
)
async def test_envois_distincts_gardent_deux_cartes(monkeypatch, noms, premier, second):
    from app.services import workspace_tools

    monkeypatch.setattr(workspace_tools, "get_email_confirmation_destination", AsyncMock(return_value={}))
    monkeypatch.setattr(chat, "_controle_du_prompt", lambda *a, **k: {"allowed": True, "warnings": [], "errors": []})
    jamais = AsyncMock(side_effect=AssertionError("Envoi sans confirmation"))
    monkeypatch.setattr(chat, "execute_workspace_tool", jamais)
    base = {"to": "personne@exemple.fr", "subject": "Sujet", "body": "Texte"}
    appels = [
        ToolCall(id="premier", name=noms[0], arguments=base | premier),
        ToolCall(id="second", name=noms[1], arguments=base | second),
    ]
    outils = [{"type": "function", "function": {"name": appel.name}} for appel in appels]
    evenements = [json.loads(bloc.removeprefix("data: ")) async for bloc in
                  chat._execute_tools_and_continue(
                      Modele(), None, ContextWindow(messages=[]), "", appels, outils,
                      "c-test", 3, session=MagicMock(),
                  )]
    cartes = [e for e in evenements if e["type"] == "confirmation_required"]
    assert len(cartes) == 2
    jamais.assert_not_awaited()
