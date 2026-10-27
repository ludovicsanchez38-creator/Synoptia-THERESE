"""B-1343 : une clé Claude non rattachée à un espace de travail.

Constaté en rédigeant le guide de la bêta (27/10/2026), vérifié dans la
documentation d'Anthropic (« Authentication », section Select a workspace) :
une clé personnelle peut ne viser aucun espace en particulier ; l'API refuse
alors chaque requête sans l'en-tête `anthropic-workspace-id`, en 400 avec le
message « This API key is not scoped to a workspace… ». THÉRÈSE n'envoie pas
cet en-tête : le testeur lisait « Requête refusée par le service d'IA (400) »,
sans cause ni geste. Même page d'erreurs : un 402 `billing_error` signale un
problème de paiement, rendu jusqu'ici comme un 402 nu.

Le corps de la réponse ne s'affiche jamais (frontière 0.48) : il sert
seulement à classer l'erreur.
"""
import json

import httpx
import pytest
from app.services.llm import _is_provider_outage
from app.services.providers.anthropic import AnthropicProvider
from app.services.providers.base import LLMConfig, LLMProvider

NON_RATTACHEE = {
    "type": "error",
    "error": {
        "type": "invalid_request_error",
        "message": "This API key is not scoped to a workspace, so this request must include the "
        "anthropic-workspace-id header with the ID of the workspace to use. Add the header, or "
        "use an API key that is scoped to a workspace.",
    },
    "request_id": "req_011CSHoEeqs5C35K2UUqR7Fy",
}


def _provider(code: int, corps) -> AnthropicProvider:
    contenu = corps if isinstance(corps, bytes) else json.dumps(corps).encode()

    def repondre(request: httpx.Request) -> httpx.Response:
        return httpx.Response(code, content=contenu)

    return AnthropicProvider(
        LLMConfig(provider=LLMProvider.ANTHROPIC, model="claude-sonnet-5-5", api_key="cle-de-test"),
        client=httpx.AsyncClient(transport=httpx.MockTransport(repondre)),
    )


async def _erreur(code: int, corps) -> str:
    evenements = [e async for e in _provider(code, corps).stream(None, [{"role": "user", "content": "Bonjour"}], None)]
    erreurs = [e for e in evenements if e.type == "error"]
    assert erreurs
    return erreurs[0].content or ""


@pytest.mark.asyncio
async def test_cle_non_rattachee_dit_quoi_faire():
    message = await _erreur(400, NON_RATTACHEE)

    assert "espace de travail" in message
    assert "Console Claude" in message and "Paramètres" in message
    assert "anthropic-workspace-id" not in message, "le corps ne s'affiche jamais"


@pytest.mark.asyncio
async def test_probleme_de_paiement_dit_ou_regarder():
    message = await _erreur(402, {"type": "error", "error": {"type": "billing_error", "message": "x"}})

    assert "paiement" in message and "Console Claude" in message


@pytest.mark.asyncio
@pytest.mark.parametrize("corps", [
    {"type": "error", "error": {"type": "invalid_request_error", "message": "max_tokens: too large"}},
    b"pas du json", b"", {"error": "chaine"}, {"error": {"message": None}}, [], {"type": "error"},
    {"type": "error", "error": {"type": "invalid_request_error", "message": "workspace not found"}},
])
async def test_un_autre_400_reste_le_message_general(corps):
    assert await _erreur(400, corps) == "Requête refusée par le service d'IA (400)."


@pytest.mark.asyncio
async def test_les_autres_codes_ne_changent_pas():
    assert "invalide ou expirée" in await _erreur(401, NON_RATTACHEE)
    assert await _erreur(503, NON_RATTACHEE) == "API error: 503", "forme lue par le disjoncteur de pannes"


@pytest.mark.asyncio
async def test_une_cle_non_rattachee_ne_passe_pas_pour_une_panne():
    """Changer de fournisseur n'y fait rien : c'est la clé qu'il faut refaire."""
    assert _is_provider_outage(await _erreur(400, NON_RATTACHEE)) is False
