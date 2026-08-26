"""Le corps d'une réponse Ollama ne va jamais à l'écran, quel que soit le statut.

Le contrôle post-release des 0.48.x a montré que seuls le 404, le 500 et
les erreurs en flux avaient été assainis : la branche générique recopiait
encore `detail` pour tout autre statut (400, 422…). Ollama tourne en
local, donc ce corps porte typiquement un chemin de fichier de la machine.

Le rapport de la v0.48.1 affirmait « 5 sites fermés à la source ». C'était
faux : il en restait un.
"""

import json

import pytest
from app.services.llm import _is_provider_outage
from app.services.providers.base import LLMConfig, LLMProvider
from app.services.providers.ollama import OllamaProvider

from tests.test_provider_tools import _collect

SECRET = "/Users/ludo/.therese/models/sk-abc123 trace-interne"


class _ReponseHTTP:
    def __init__(self, status: int, corps: dict):
        self.status_code = status
        self._corps = json.dumps(corps).encode()

    async def aread(self):
        return self._corps

    async def aiter_lines(self):
        return
        yield  # pragma: no cover

    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return False


class _ClientHTTP:
    def __init__(self, status: int, corps: dict):
        self._status, self._corps = status, corps

    def stream(self, *a, **k):
        return _ReponseHTTP(self._status, self._corps)


async def _erreur(status: int, message: str = SECRET) -> str:
    provider = OllamaProvider(
        LLMConfig(provider=LLMProvider.OLLAMA, model="qwen3:1.7b", api_key=""),
        client=_ClientHTTP(status, {"error": message}),
    )
    events = await _collect(provider.stream(None, [{"role": "user", "content": "x"}]))
    erreurs = [e for e in events if e.type == "error"]
    assert erreurs, f"aucune erreur émise pour un HTTP {status}"
    return erreurs[0].content or ""


class TestAucunStatutNeRecopieLeCorps:
    @pytest.mark.asyncio
    @pytest.mark.parametrize("status", [400, 403, 413, 422, 503])
    async def test_le_corps_reste_au_journal(self, status: int):
        message = await _erreur(status)

        assert SECRET not in message
        assert ".therese" not in message
        assert "sk-abc123" not in message
        assert str(status) in message, "le statut reste utile au diagnostic"


class TestLesMessagesUtilesSurvivent:
    @pytest.mark.asyncio
    async def test_le_modele_absent_reste_actionnable(self):
        message = await _erreur(404, "model 'qwen3:1.7b' not found")

        assert "ollama pull" in message

    @pytest.mark.asyncio
    async def test_le_manque_de_memoire_reste_actionnable(self):
        message = await _erreur(500, "out of memory: cannot alloc")

        assert "RAM" in message

    @pytest.mark.asyncio
    async def test_une_erreur_ollama_n_ouvre_deliberement_pas_le_circuit(self):
        """Ollama est LOCAL : basculer de fournisseur enverrait au cloud.

        Tentation écartée en écrivant ces tests : classer un 503 comme panne
        aurait paru cohérent avec OpenRouter, mais le circuit breaker bascule
        vers un autre fournisseur — donc vers le cloud, chez quelqu'un qui a
        choisi de tout garder chez lui. Un service local arrêté se règle en le
        relançant, pas en envoyant ses données ailleurs.
        """
        message = await _erreur(503)

        assert not _is_provider_outage(message)
        assert "503" in message
