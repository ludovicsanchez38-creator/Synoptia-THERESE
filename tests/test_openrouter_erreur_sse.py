"""Une erreur SSE d'OpenRouter doit rester CLASSÉE pour le circuit breaker.

Régression introduite par la passe 7 des 0.48.x : en fermant la fuite du
corps de la réponse, le message est devenu « Le service OpenRouter a
signalé une erreur. » — une phrase qu'aucun marqueur de
`_is_provider_outage()` ne reconnaît. Conséquences : un 429 ne comptait
plus comme échec, et si du texte avait déjà été émis, le fournisseur
était même enregistré comme un SUCCÈS.

Le contrat tient en deux exigences opposées, et les deux comptent :
le message du fournisseur ne doit JAMAIS atteindre l'écran (il peut
porter un chemin local ou un fragment de clé), et la CLASSE de l'erreur
doit y arriver intacte.
"""

import json

import pytest
from app.services.llm import _is_provider_outage
from app.services.providers.base import LLMConfig, LLMProvider
from app.services.providers.openrouter import OpenRouterProvider

from tests.test_provider_tools import _collect, _FakeClient

SECRET = "/Users/ludo/.therese/sk-abc123 trace-interne"


def _openrouter(client) -> OpenRouterProvider:
    return OpenRouterProvider(
        LLMConfig(provider=LLMProvider.OPENROUTER, model="x/y", api_key="k"),
        client=client,
    )


async def _erreur_sse(code: int, error_type: str | None = None) -> str:
    err: dict = {"code": code, "message": SECRET}
    if error_type:
        err["metadata"] = {"error_type": error_type}
    client = _FakeClient(["data: " + json.dumps({"error": err})])
    events = await _collect(
        _openrouter(client).stream(None, [{"role": "user", "content": "x"}])
    )
    erreurs = [e for e in events if e.type == "error"]
    assert erreurs, "aucun événement d'erreur émis"
    return erreurs[0].content or ""


class TestLaClasseDeLErreurSurvit:
    @pytest.mark.asyncio
    async def test_un_429_compte_comme_panne(self):
        message = await _erreur_sse(429, "rate_limit_exceeded")

        assert _is_provider_outage(message), (
            f"le circuit breaker ignore cette erreur : {message!r}"
        )

    @pytest.mark.asyncio
    async def test_un_502_compte_comme_panne(self):
        message = await _erreur_sse(502)

        assert _is_provider_outage(message), (
            f"le circuit breaker ignore cette erreur : {message!r}"
        )

    @pytest.mark.asyncio
    async def test_les_credits_epuises_restent_actionnables(self):
        message = await _erreur_sse(402)

        assert "rédit" in message, "l'utilisateur ne sait pas quoi faire"
        assert _is_provider_outage(message)

    @pytest.mark.asyncio
    async def test_une_erreur_applicative_n_ouvre_pas_le_circuit(self):
        """Un 400 est une erreur de requête : basculer de fournisseur n'aide pas."""
        message = await _erreur_sse(400)

        assert not _is_provider_outage(message), (
            f"une erreur applicative fait basculer le circuit : {message!r}"
        )


class TestLeMessageDuFournisseurNAtteintPasLEcran:
    @pytest.mark.asyncio
    @pytest.mark.parametrize("code", [400, 402, 429, 502])
    async def test_aucun_code_ne_recopie_le_corps(self, code: int):
        message = await _erreur_sse(code, "quelconque")

        assert SECRET not in message
        assert ".therese" not in message
        assert "sk-abc123" not in message
