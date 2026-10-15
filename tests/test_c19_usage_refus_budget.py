"""L'usage déjà payé survit au refus d'une continuation, avant l'erreur SSE."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, Mock, patch

import pytest
from app.routers import chat

from tests.test_c18_budget_continuation import _poser, _restaurer, _Service


@pytest.mark.asyncio
async def test_usage_comptabilise_avant_erreur_de_budget(client, monkeypatch):
    service = _Service()
    monkeypatch.setattr(chat, "get_llm_service", lambda: service)
    traceur, limites, compteurs = _poser(0.02)
    compter = Mock(wraps=traceur.record_usage)
    monkeypatch.setattr(traceur, "record_usage", compter)
    flux_produit = chat._do_stream_response
    compte_au_refus: list[bool] = []

    async def observer_flux(*args, **kwargs):
        async for trame in flux_produit(*args, **kwargs):
            if trame.startswith("data:"):
                evenement = json.loads(trame.removeprefix("data:").strip())
                if evenement.get("type") == "error":
                    compte_au_refus.append(compter.called)
            yield trame

    monkeypatch.setattr(chat, "_do_stream_response", observer_flux)
    try:
        with patch(
            "app.routers.chat.execute_workspace_tool",
            AsyncMock(return_value="r" * (120_000 * 4)),
        ):
            reponse = await client.post(
                "/api/chat/send", json={"message": "Bonjour", "stream": True},
            )
    finally:
        _restaurer(traceur, limites, compteurs)

    assert reponse.status_code == 200, reponse.text[:400]
    assert "Budget mensuel atteint" in reponse.text
    assert service.continuation is False
    assert compte_au_refus == [True], "L'usage payé doit être durable avant l'erreur terminale"
    compter.assert_called_once()
    assert compter.call_args.kwargs["input_tokens"] == 20
    assert compter.call_args.kwargs["output_tokens"] == 5
    assert compter.call_args.kwargs["appels"] == [(20, 5)]
    assert '"type": "done"' not in reponse.text
