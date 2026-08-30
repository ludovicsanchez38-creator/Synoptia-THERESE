"""Outils + reasoning_effort : la combinaison que gpt-5.6-luna refuse.

Constaté le 30/08/2026 en configurant une instance neuve sur gpt-5.6-luna,
le modèle que Ludo avait choisi pour son coût. TOUTE conversation répondait
`API error: 400`. Reproduit contre l'API réelle, qui dit :

    Function tools with reasoning_effort are not supported for gpt-5.6-luna
    in /v1/chat/completions. To use function tools, use /v1/responses or set
    reasoning_effort to 'none'.

THÉRÈSE fournit 29 outils à chaque message ET un reasoning_effort : le produit
était donc inutilisable avec ce modèle, sur tous les écrans, pas seulement
avec une pièce jointe comme on l'avait d'abord cru.

Un repli existait — chez GrokProvider seulement, pour un conflit de
documentation sur grok-4.6. Les cinq fournisseurs qui héritent d'OpenAIProvider
(grok, glm, minimax, kimi, qwen) et OpenAI lui-même n'en avaient pas.
"""

import httpx
import pytest
from app.services.llm import LLMConfig, LLMProvider
from app.services.providers.openai import OpenAIProvider

MSGS = [{"role": "user", "content": "salut"}]
OUTILS = [
    {
        "type": "function",
        "function": {"name": "chercher", "description": "c", "parameters": {}},
    }
]
REFUS = {
    "error": {
        "message": (
            "Function tools with reasoning_effort are not supported for "
            "gpt-5.6-luna in /v1/chat/completions. To use function tools, use "
            "/v1/responses or set reasoning_effort to 'none'."
        )
    }
}
FLUX_OK = (
    b'data: {"choices":[{"delta":{"content":"PRET"}}]}\n\n'
    b"data: [DONE]\n\n"
)


def test_avec_outils_leffort_est_pose_a_none():
    """Le correctif de fond : on ne compte pas sur le rejeu, on n'envoie pas
    la combinaison refusée. Omettre le paramètre NE SUFFIT PAS — le modèle a
    un effort par défaut et le refus tombe quand même."""
    provider = OpenAIProvider(
        LLMConfig(LLMProvider.OPENAI, "gpt-5.6-luna", api_key="test", effort="low"),
        httpx.AsyncClient(),
    )
    avec = provider._build_request_body(MSGS, OUTILS)
    assert avec["reasoning_effort"] == "none"
    assert avec["tools"] == OUTILS

    sans = provider._build_request_body(MSGS, None)
    assert sans["reasoning_effort"] == "low", (
        "sans outil, l'effort demandé doit partir normalement"
    )


@pytest.mark.parametrize(
    "modele", ["gpt-5.6-luna", "gpt-5.6-sol", "gpt-5.6-terra", "gpt-5.5", "gpt-5.4-mini"]
)
def test_toute_la_famille_gpt5_est_couverte(modele):
    """Les cinq modèles proposés par l'application refusaient la combinaison.
    Vérifié contre l'API réelle le 30/08/2026."""
    provider = OpenAIProvider(
        LLMConfig(LLMProvider.OPENAI, modele, api_key="test", effort="high"),
        httpx.AsyncClient(),
    )
    assert provider._build_request_body(MSGS, OUTILS)["reasoning_effort"] == "none"


@pytest.mark.asyncio
async def test_un_400_sur_effort_rejoue_sans_effort():
    corps_vus: list[dict] = []

    def repondre(requete: httpx.Request) -> httpx.Response:
        import json

        corps_vus.append(json.loads(requete.content))
        if "reasoning_effort" in corps_vus[-1]:
            return httpx.Response(400, json=REFUS)
        return httpx.Response(200, content=FLUX_OK)

    client = httpx.AsyncClient(transport=httpx.MockTransport(repondre))
    provider = OpenAIProvider(
        LLMConfig(LLMProvider.OPENAI, "gpt-5.6-luna", api_key="test", effort="low"),
        client,
    )

    # Sans outil, l'effort part : c'est le cas où le rejeu sert de filet
    # (un modèle qui refuserait l'effort pour une autre raison).
    recu = [e async for e in provider.stream(None, MSGS, None)]

    assert len(corps_vus) == 2, (
        "l'appel aurait dû être rejoué sans reasoning_effort ; "
        f"tentatives : {len(corps_vus)}"
    )
    assert "reasoning_effort" in corps_vus[0]
    assert "reasoning_effort" not in corps_vus[1]
    assert not any(e.type == "error" for e in recu), (
        f"aucune erreur ne doit remonter : {[e.content for e in recu if e.type == 'error']}"
    )
