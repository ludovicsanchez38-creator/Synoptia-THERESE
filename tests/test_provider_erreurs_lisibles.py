"""B-203 et B-215 : « API error: 401 » n'est pas un message pour un humain.

Une clé refusée arrivait dans le fil de conversation sous la forme brute
`API error: 401` : anglais, sans sujet, sans cause, sans action. Deux
fournisseurs traduisaient déjà leur code HTTP avant de le rendre - Gemini
(`_message_erreur_http`) et OpenRouter (`_message_erreur_sse`) - mais les six
qui passent par `response.raise_for_status()` rendaient le code nu depuis leur
`except httpx.HTTPStatusError` : anthropic, openai, mistral, deepseek,
infomaniak, perplexity. Grok hérite d'OpenAIProvider et héritait donc du même
défaut, en plus du risque de se faire appeler « OpenAI » à l'écran.

Deux exigences OPPOSÉES, toutes deux obligatoires (mêmes que celles écrites
dans openrouter.py) :

- un 401 doit nommer le fournisseur, la clé et l'action ;
- un 5xx doit GARDER la forme « API error: {code} », seule forme que le regex
  de `_is_provider_outage` (llm.py) sait relire pour compter une panne.

Le troisième test fixe la classification obtenue au circuit breaker, parce
qu'elle CHANGE avec ce correctif : « Clé API … invalide ou expirée » porte les
marqueurs `clé api` et `invalide ou expir`, donc un 401 compte désormais comme
une panne du fournisseur - exactement comme chez Gemini et OpenRouter depuis la
0.48.1, et conformément à la docstring de `_is_provider_outage` qui range la
« clé invalide » parmi les cas où basculer de fournisseur aide.
"""

import httpx
import pytest
from app.services.llm import _is_provider_outage
from app.services.providers.anthropic import AnthropicProvider
from app.services.providers.base import LLMConfig, LLMProvider
from app.services.providers.deepseek import DeepSeekProvider
from app.services.providers.grok import GrokProvider
from app.services.providers.infomaniak import InfomaniakProvider
from app.services.providers.mistral import MistralProvider
from app.services.providers.openai import OpenAIProvider
from app.services.providers.perplexity import PerplexityProvider

# (classe, provider de config, modèle, nom attendu à l'écran)
FOURNISSEURS = [
    (AnthropicProvider, LLMProvider.ANTHROPIC, "claude-sonnet-5", "Anthropic"),
    (OpenAIProvider, LLMProvider.OPENAI, "gpt-5.6-sol", "OpenAI"),
    (MistralProvider, LLMProvider.MISTRAL, "mistral-medium-latest", "Mistral"),
    (DeepSeekProvider, LLMProvider.DEEPSEEK, "deepseek-v4-pro", "DeepSeek"),
    (InfomaniakProvider, LLMProvider.INFOMANIAK, "mixtral", "Infomaniak"),
    (PerplexityProvider, LLMProvider.PERPLEXITY, "sonar", "Perplexity"),
    # Grok hérite d'OpenAIProvider : sans nom dérivé de la configuration, il
    # annoncerait la clé « OpenAI » à qui a saisi une clé xAI.
    (GrokProvider, LLMProvider.GROK, "grok-4.6", "Grok"),
]

IDS = [f[3] for f in FOURNISSEURS]


def _provider(classe, marque, modele, code: int, corps: bytes = b'{"error":"nope"}'):
    """Un vrai HTTPStatusError : httpx.MockTransport, pas un faux objet."""

    def repondre(request: httpx.Request) -> httpx.Response:
        return httpx.Response(code, content=corps)

    client = httpx.AsyncClient(transport=httpx.MockTransport(repondre))
    return classe(
        LLMConfig(provider=marque, model=modele, api_key="cle-de-test"),
        client=client,
    )


async def _contenu_erreur(provider) -> str:
    messages = [{"role": "user", "content": "Bonjour"}]
    evenements = [e async for e in provider.stream(None, messages, None)]
    erreurs = [e for e in evenements if e.type == "error"]
    assert erreurs, f"aucun évènement d'erreur émis : {evenements}"
    return erreurs[0].content or ""


class TestUn401NommeLaCleEtLAction:
    @pytest.mark.parametrize("classe,marque,modele,nom", FOURNISSEURS, ids=IDS)
    @pytest.mark.asyncio
    async def test_401_de_chaque_provider_nomme_la_cle_et_l_action(
        self, classe, marque, modele, nom
    ):
        contenu = await _contenu_erreur(_provider(classe, marque, modele, 401))

        assert "api error" not in contenu.lower(), (
            f"{nom} rend encore le code HTTP brut à l'écran : {contenu!r}"
        )
        assert nom.lower() in contenu.lower(), (
            f"le message ne dit pas de QUEL fournisseur vient la clé : {contenu!r}"
        )
        assert "clé" in contenu.lower(), (
            f"le message ne nomme pas la clé : {contenu!r}"
        )
        assert "paramètres" in contenu.lower(), (
            f"le message ne dit pas où corriger : {contenu!r}"
        )

    @pytest.mark.asyncio
    async def test_le_corps_du_fournisseur_ne_fuit_pas_a_l_ecran(self):
        """Frontière 0.48 : le corps peut porter un fragment de clé."""
        provider = _provider(
            OpenAIProvider,
            LLMProvider.OPENAI,
            "gpt-5.6-sol",
            401,
            corps=b'{"error":{"message":"Incorrect API key sk-proj-abc123 trace/77"}}',
        )
        contenu = await _contenu_erreur(provider)

        assert "sk-proj" not in contenu
        assert "trace/77" not in contenu


class TestLes5xxGardentLaFormeLueParLeCircuitBreaker:
    @pytest.mark.parametrize("classe,marque,modele,nom", FOURNISSEURS, ids=IDS)
    @pytest.mark.asyncio
    async def test_un_503_garde_api_error_503(self, classe, marque, modele, nom):
        contenu = await _contenu_erreur(_provider(classe, marque, modele, 503))

        assert "api error: 503" in contenu.lower(), (
            f"{nom} : la forme lue par _is_provider_outage a disparu : {contenu!r}"
        )
        assert _is_provider_outage(contenu) is True


class TestLaClassificationAuCircuitBreakerEstFixee:
    """Ce que le correctif CHANGE, dit explicitement plutôt que subi."""

    @pytest.mark.asyncio
    async def test_un_401_compte_desormais_comme_panne(self):
        contenu = await _contenu_erreur(
            _provider(OpenAIProvider, LLMProvider.OPENAI, "gpt-5.6-sol", 401)
        )
        assert _is_provider_outage(contenu) is True

    @pytest.mark.asyncio
    async def test_un_400_ne_compte_pas_comme_panne(self):
        """Une requête refusée n'est pas une panne : basculer n'aiderait pas."""
        contenu = await _contenu_erreur(
            _provider(OpenAIProvider, LLMProvider.OPENAI, "gpt-4o", 400)
        )
        assert "api error" not in contenu.lower()
        assert _is_provider_outage(contenu) is False
