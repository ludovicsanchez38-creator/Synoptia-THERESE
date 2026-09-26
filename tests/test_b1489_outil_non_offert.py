"""B-1489 : un outil absent de la liste offerte au tour s'exécutait quand
même si le modèle l'appelait.

Cas atteignable : une carte d'agenda attend déjà validation, le flux retire
donc `create_calendar_event` de la liste du tour (D1). Un modèle local qui
analyse ses appels d'outils dans le texte peut le rappeler quand même : la
boucle d'exécution ne consultait pas la liste offerte et empilait une
seconde carte pour le même rendez-vous. Le retrait d'outils que prévoit
P-106 (lecture de fichiers sans accord) reposera sur la même garde.
"""

from types import SimpleNamespace

import pytest


def _outil(nom):
    return {"type": "function", "function": {"name": nom}}


@pytest.mark.asyncio
async def test_un_outil_non_offert_n_est_pas_execute(monkeypatch):
    from app.routers import chat
    from app.services.providers.base import StreamEvent, ToolCall

    cartes: list[str] = []
    monkeypatch.setattr(chat, "register_pending", lambda nom, *a, **k: cartes.append(nom) or "c-2")
    resultats: list = []

    class _FauxLLM:
        config = SimpleNamespace(provider=SimpleNamespace(value="ollama"), model="faux")

        async def continue_with_tool_results(self, context, assistant_content, tool_calls, tool_results, *args, **kwargs):
            resultats.extend(tool_results)
            yield StreamEvent(type="text", content="Le rendez-vous attend ta validation.")
            yield StreamEvent(type="done", stop_reason="end_turn")

    appel = ToolCall(id="t1", name="create_calendar_event", arguments={
        "title": "Point chantier", "start": "2026-10-01T10:00:00", "end": "2026-10-01T11:00:00",
    })
    evenements = [
        e async for e in chat._execute_tools_and_continue(
            _FauxLLM(), None, SimpleNamespace(messages=[], system_prompt=""), "", [appel],
            [_outil("read_emails")], "conv-b1489", remaining_iterations=2,
        )
    ]

    assert cartes == []
    assert not any("confirmation_required" in e for e in evenements)
    assert resultats and resultats[0].is_error
