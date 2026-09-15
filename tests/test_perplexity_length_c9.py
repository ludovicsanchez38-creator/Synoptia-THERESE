"""B-796 (cycle 9) : une réponse coupée par `finish_reason == "length"` ressortait
avec `stop_reason="stop"`, comme si le modèle avait fini sa phrase ; et sans aucun
contenu, rien ne disait que le budget de tokens était épuisé (OpenRouter le dit)."""
from __future__ import annotations

import contextlib
import json

import pytest


class FausseReponse:
    def __init__(self, lignes: list[str]):
        self.status_code = 200
        self._lignes = lignes
        self.headers: dict[str, str] = {}

    async def aread(self):
        return b""

    async def aiter_lines(self):
        for ligne in self._lignes:
            yield ligne

    def raise_for_status(self):
        return None


class FauxClient:
    def __init__(self, reponse: FausseReponse):
        self.reponse = reponse

    def stream(self, method, url, **kwargs):
        @contextlib.asynccontextmanager
        async def _cm():
            yield self.reponse

        return _cm()

    async def aclose(self):
        return None


def _sse(*deltas: str, finish: str) -> list[str]:
    lignes = [
        "data: " + json.dumps({"choices": [{"delta": {"content": d}, "finish_reason": None}]})
        for d in deltas
    ]
    lignes.append("data: " + json.dumps({"choices": [{"delta": {}, "finish_reason": finish}]}))
    lignes.append("data: [DONE]")
    return lignes


def _perplexity(client: FauxClient):
    from app.services.providers.base import LLMConfig, LLMProvider
    from app.services.providers.perplexity import PerplexityProvider

    return PerplexityProvider(LLMConfig(LLMProvider.PERPLEXITY, "sonar", api_key="k"), client)


async def _evenements(provider):
    sortie = []
    async for evenement in provider.stream("Tu es THÉRÈSE.", [{"role": "user", "content": "Bonjour"}]):
        sortie.append(evenement)
    return sortie


@pytest.mark.asyncio
async def test_une_reponse_coupee_est_signalee_par_stop_reason_length() -> None:
    evenements = await _evenements(_perplexity(FauxClient(FausseReponse(_sse("Bon", "jour", finish="length")))))
    done = [e for e in evenements if e.type == "done"]
    assert done and done[-1].stop_reason == "length"
    assert not [e for e in evenements if e.type == "error"]


@pytest.mark.asyncio
async def test_sans_contenu_le_budget_epuise_est_dit() -> None:
    evenements = await _evenements(_perplexity(FauxClient(FausseReponse(_sse(finish="length")))))
    erreurs = [e.content or "" for e in evenements if e.type == "error"]
    assert erreurs and "budget de tokens" in erreurs[0]
