"""La récupération d’un fournisseur du Board admet un seul appel d’essai."""

import asyncio
from types import SimpleNamespace

import pytest
from app.models.board import AdvisorRole, BoardMode, BoardRequest
from app.services import board
from app.services.circuit_breaker import RECOVERY_TIMEOUT, CircuitState, get_circuit_breaker
from app.services.error_handler import ErreurPourEcran
from app.services.providers.base import LLMProvider


@pytest.mark.asyncio
async def test_deux_boards_prepares_ne_lancent_qu_une_sonde(monkeypatch):
    from app.services import consentements

    circuit = get_circuit_breaker()
    circuit.reset("anthropic")
    circuit.record_failure("anthropic", "Échec fictif")
    circuit.record_failure("anthropic", "Échec fictif")
    circuit._get_circuit("anthropic").last_failure_time -= RECOVERY_TIMEOUT + 1

    recherches = asyncio.Queue()
    entre_dans_le_modele = asyncio.Event()
    retenir_le_modele = asyncio.Event()
    appels = 0

    class Conseiller:
        config = SimpleNamespace(provider=LLMProvider.ANTHROPIC, model="modele-temoin")

        def prepare_context(self, messages, **kwargs):
            return SimpleNamespace(messages=messages)

        async def stream_response(self, context, **kwargs):
            nonlocal appels
            appels += 1
            if appels > 1:
                raise ErreurPourEcran("Le banc a reçu un deuxième appel au fournisseur.")
            entre_dans_le_modele.set()
            await retenir_le_modele.wait()
            yield "Avis de contrôle"

    async def preparer_recherche(*_args):
        reprendre = asyncio.Event()
        recherches.put_nowait(reprendre)
        await reprendre.wait()
        return ""

    monkeypatch.setattr(consentements, "exiger_accord", lambda *_args: None)
    monkeypatch.setenv("THERESE_SONDE_CATALOGUE", "off")
    conseiller = Conseiller()
    monkeypatch.setattr(board, "get_llm_service", lambda: conseiller)
    monkeypatch.setattr(board, "get_llm_service_for_provider", lambda *args, **kwargs: conseiller)
    monkeypatch.setattr(board, "_get_user_context", lambda: "")
    monkeypatch.setattr(board.BoardService, "_search_web_for_context", preparer_recherche)

    demande = BoardRequest(
        question="Faut-il lancer ce pilote maintenant ?",
        mode=BoardMode.CLOUD,
        advisors=[AdvisorRole.ANALYST],
    )

    async def deliberer():
        async for _ in board.BoardService().deliberate(demande):
            pass

    taches = [asyncio.create_task(deliberer())]
    try:
        premiere = await asyncio.wait_for(recherches.get(), timeout=2)
        taches.append(asyncio.create_task(deliberer()))
        seconde = await asyncio.wait_for(recherches.get(), timeout=2)
        premiere.set()
        await asyncio.wait_for(entre_dans_le_modele.wait(), timeout=2)
        assert circuit.get_state("anthropic") is CircuitState.HALF_OPEN
        seconde.set()

        with pytest.raises(ErreurPourEcran, match="fournisseur anthropic .*indisponible"):
            await asyncio.wait_for(taches[1], timeout=2)
        assert appels == 1

        taches[0].cancel()
        with pytest.raises(asyncio.CancelledError):
            await taches[0]
        assert circuit.get_state("anthropic") is CircuitState.OPEN
        assert circuit.is_available("anthropic")
    finally:
        for tache in taches:
            tache.cancel()
        await asyncio.gather(*taches, return_exceptions=True)
        circuit.reset("anthropic")
