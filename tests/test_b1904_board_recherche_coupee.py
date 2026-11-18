"""B-1904 : le Board annonce le refus sans le présenter comme une recherche."""

from contextlib import aclosing
from types import SimpleNamespace

import pytest
from app.models.board import AdvisorRole, BoardMode, BoardRequest
from app.services import board as module
from app.services import web_search
from app.services.board import BoardService


@pytest.mark.asyncio
async def test_recherche_coupee_annonce_refus_et_le_transmet_au_conseiller(monkeypatch):
    demandes = []

    class FauxLLM:
        config = SimpleNamespace(provider=SimpleNamespace(value="anthropic"), model="test")

        def prepare_context(self, messages, system_prompt=None):
            demandes.extend(message.content for message in messages)
            return SimpleNamespace()

        async def stream_response(self, *_args, **_kwargs):
            yield "Avis témoin"

    class RechercheSansReseau:
        async def search(self, *_args, **_kwargs):
            web_search.verifier_autorisation_recherche()
            raise AssertionError("aucune recherche ne doit avoir lieu")

    web_search.poser_autorisation_recherche(False)
    monkeypatch.setattr(module, "get_web_search_service", RechercheSansReseau)
    monkeypatch.setattr(module, "get_llm_service", FauxLLM)
    monkeypatch.setattr(module, "get_llm_service_for_provider", lambda *_a, **_k: FauxLLM())
    monkeypatch.setattr(module, "_get_user_context", lambda: "")
    monkeypatch.setattr(module, "derives_connues", lambda: [])
    monkeypatch.setattr("app.services.consentements.exiger_accord", lambda *_: None)
    monkeypatch.setattr("app.services.circuit_breaker.CircuitBreakerManager.is_available", lambda *_: True)
    monkeypatch.setattr(BoardService, "_track_usage", lambda *_a, **_k: {})

    demande = BoardRequest(
        question="Que décider ?", mode=BoardMode.CLOUD, advisors=[AdvisorRole.ANALYST]
    )
    evenements = []
    async with aclosing(BoardService().deliberate(demande)) as flux:
        async for evenement in flux:
            evenements.append(evenement)
            if evenement.type == "advisor_chunk":
                break

    fin_recherche = next(e for e in evenements if e.type == "web_search_done")
    assert demandes and "Recherche web coupée" in demandes[0]
    assert "coupée" in fin_recherche.content.lower() or "désactivée" in fin_recherche.content.lower()
    assert "caractères de contexte web" not in fin_recherche.content
