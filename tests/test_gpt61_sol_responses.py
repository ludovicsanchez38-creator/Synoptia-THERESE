"""Lot M2 : gpt-6.1-sol. Les outils passent par Responses, jamais par none.

Sources (09/10/2026) :
- https://developers.openai.com/api/docs/models/gpt-6.1-sol
- https://developers.openai.com/api/docs/guides/reasoning
- https://developers.openai.com/api/docs/guides/function-calling
- https://developers.openai.com/api/docs/guides/streaming-responses

Client simulé : aucun appel réseau. Design :
docs/plans/2026-10-09-c18-m2-gpt61-responses.md
"""

from __future__ import annotations

import asyncio
import json

import httpx
import pytest
from app.services.providers.base import LLMConfig, LLMProvider, ToolCall, ToolResult, ToolTurn
from app.services.providers.glm import GLMProvider
from app.services.providers.grok import GrokProvider
from app.services.providers.kimi import KimiProvider
from app.services.providers.minimax import MiniMaxProvider
from app.services.providers.qwen import QwenProvider

MODELE = "gpt-6.1-sol"
OUTIL = {
    "type": "function",
    "function": {
        "name": "meteo",
        "description": "Le temps qu'il fait",
        "parameters": {"type": "object", "properties": {"ville": {"type": "string"}}},
    },
}
MESSAGES = [
    {"role": "system", "content": "Tu es THÉRÈSE."},
    {"role": "user", "content": "Quel temps à Manosque ?"},
]


def _config(modele: str = MODELE, effort: str | None = "high") -> LLMConfig:
    return LLMConfig(provider=LLMProvider.OPENAI, model=modele, api_key="cle-test", effort=effort)


def _provider(client, modele: str = MODELE, effort: str | None = "high"):
    from app.services.providers.openai import OpenAIProvider

    return OpenAIProvider(_config(modele, effort), client)


def _ligne(charge: dict) -> str:
    return f"data: {json.dumps(charge)}"


class _Reponse:
    def __init__(self, lignes: list[str], status: int = 200):
        self.status_code = status
        self._lignes = lignes
        self.text = ""

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            requete = httpx.Request("POST", "https://api.openai.com/v1/responses")
            reponse = httpx.Response(self.status_code, request=requete)
            raise httpx.HTTPStatusError("refus", request=requete, response=reponse)

    async def aiter_lines(self):
        for ligne in self._lignes:
            yield ligne

    async def aread(self) -> bytes:
        return b""


class _Client:
    """Faux httpx : enregistre l'appel, rend les lignes SSE."""

    def __init__(self, lignes: list[str], status: int = 200):
        self._lignes = lignes
        self._status = status
        self.requests: list[dict] = []
        self.ferme = False

    def stream(self, method, url, **kwargs):
        self.requests.append({"method": method, "url": url, **kwargs})
        reponse = _Reponse(self._lignes, self._status)
        client = self

        class _CM:
            async def __aenter__(self):
                return reponse

            async def __aexit__(self, *args):
                client.ferme = True
                return False

        return _CM()


class _ClientBloquant(_Client):
    """Une ligne, puis le flux reste ouvert jusqu'à la fermeture du générateur."""

    def __init__(self, ligne: str):
        super().__init__([ligne])
        self.premiere_ligne = asyncio.Event()

    def stream(self, method, url, **kwargs):
        self.requests.append({"method": method, "url": url, **kwargs})
        client = self

        class _ReponseBloquee(_Reponse):
            async def aiter_lines(self):
                yield client._lignes[0]
                client.premiere_ligne.set()
                await asyncio.Event().wait()

        reponse = _ReponseBloquee(self._lignes)

        class _CM:
            async def __aenter__(self):
                return reponse

            async def __aexit__(self, *args):
                client.ferme = True
                return False

        return _CM()


def _flux_texte() -> list[str]:
    return [
        _ligne({"type": "response.output_text.delta", "delta": "Bonjour"}),
        _ligne({"type": "response.output_text.delta", "delta": " Manosque"}),
        _ligne({
            "type": "response.completed",
            "response": {
                "status": "completed",
                "usage": {"input_tokens": 42, "output_tokens": 7},
            },
        }),
    ]


def _flux_outil() -> list[str]:
    return [
        _ligne({"type": "response.output_text.delta", "delta": "Je regarde."}),
        _ligne({
            "type": "response.output_item.added",
            "output_index": 0,
            "item": {
                "type": "function_call",
                "id": "fc_1",
                "call_id": "call_meteo",
                "name": "meteo",
                "arguments": "",
            },
        }),
        _ligne({
            "type": "response.function_call_arguments.delta",
            "output_index": 0,
            "delta": '{"ville":',
        }),
        _ligne({
            "type": "response.function_call_arguments.delta",
            "output_index": 0,
            "delta": '"Manosque"}',
        }),
        _ligne({
            "type": "response.output_item.done",
            "output_index": 0,
            "item": {
                "type": "function_call",
                "call_id": "call_meteo",
                "name": "meteo",
                "arguments": '{"ville":"Manosque"}',
            },
        }),
        _ligne({
            "type": "response.completed",
            "response": {
                "status": "completed",
                "usage": {"input_tokens": 20, "output_tokens": 8},
            },
        }),
    ]


async def _collecter(generateur):
    return [evenement async for evenement in generateur]


class TestCatalogue:
    def test_present_sans_prendre_la_tete(self):
        from app.services.modeles_catalogue import CATALOGUE, fenetre_de_contexte, frontier

        openai = CATALOGUE["openai"]
        assert frontier("openai") == "gpt-6-sol"
        assert openai.modeles[:3] == ("gpt-6-sol", "gpt-6-astra", "gpt-6-luna")
        assert MODELE in openai.modeles
        assert openai.modeles.index(MODELE) > openai.modeles.index("gpt-6-luna")
        assert fenetre_de_contexte("openai", MODELE) == 1_050_000

    @pytest.mark.parametrize("effort", ["low", "medium", "high", "xhigh", "max"])
    def test_effort_documente_transmis(self, effort):
        from app.services.modeles_catalogue import resoudre_effort

        assert resoudre_effort(MODELE, effort, "openai") == effort

    @pytest.mark.parametrize("effort", ["none", "minimal"])
    def test_none_et_minimal_ne_partent_pas(self, effort):
        from app.services.modeles_catalogue import CATALOGUE, resoudre_effort

        # Sans fiche, un modèle inconnu omet aussi l'effort : on exige la fiche.
        assert MODELE in CATALOGUE["openai"].fiches
        assert resoudre_effort(MODELE, "high", "openai") == "high"
        assert resoudre_effort(MODELE, effort, "openai") is None

    def test_le_reglage_accepte_l_effort_xhigh(self):
        from app.models.schemas import LLMConfigUpdate

        maj = LLMConfigUpdate(provider="openai", model=MODELE, effort="xhigh")
        assert maj.effort == "xhigh"


class TestTarif:
    def test_standard_connu_et_cout_des_jetons_du_flux(self):
        from app.services.token_tracker import TOKEN_PRICES, TokenTracker

        assert TOKEN_PRICES[MODELE] == {"input": 2.00, "output": 10.00}
        traceur = object.__new__(TokenTracker)
        assert traceur.tarif_connu(MODELE) is True
        # 42 jetons d'entrée et 7 de sortie, le usage du flux texte.
        assert traceur.estimate_cost(MODELE, 42, 7) == pytest.approx(
            42 / 1_000_000 * 2.00 + 7 / 1_000_000 * 10.00
        )

    def test_palier_au_dela_de_272_000_jetons_entree(self):
        """Fiche : plus de 272 k jetons d'entrée, 2× l'entrée et 1,5× la sortie."""
        from app.services import token_tracker

        palier = getattr(token_tracker, "PALIERS_TARIF", {}).get(MODELE)
        assert palier is not None
        assert palier.seuil_entree == 272_000
        assert palier.multiplicateur_entree == 2
        assert palier.multiplicateur_sortie == 1.5
        traceur = object.__new__(token_tracker.TokenTracker)
        assert traceur.estimate_cost(MODELE, 272_000, 1_000) == pytest.approx(
            272_000 / 1_000_000 * 2.00 + 1_000 / 1_000_000 * 10.00
        )
        assert traceur.estimate_cost(MODELE, 272_001, 1_000) == pytest.approx(
            272_001 / 1_000_000 * 2.00 * 2 + 1_000 / 1_000_000 * 10.00 * 1.5
        )


class TestTransport:
    @pytest.mark.asyncio
    async def test_flux_texte_sur_responses_quand_des_outils_sont_la(self):
        client = _Client(_flux_texte())
        evenements = await _collecter(_provider(client).stream(None, MESSAGES, [OUTIL]))

        appel = client.requests[0]
        assert appel["url"] == "https://api.openai.com/v1/responses"
        assert appel["headers"]["Authorization"] == "Bearer cle-test"
        corps = appel["json"]
        assert corps["model"] == MODELE
        assert corps["stream"] is True
        assert corps["reasoning"] == {"effort": "high"}
        assert "reasoning_effort" not in corps
        assert corps["tools"] == [{
            "type": "function",
            "name": "meteo",
            "description": "Le temps qu'il fait",
            "parameters": OUTIL["function"]["parameters"],
        }]
        assert corps["tool_choice"] == "auto"
        assert corps["max_output_tokens"] == 4096
        assert corps["input"][0] == {"role": "system", "content": "Tu es THÉRÈSE."}
        assert corps["input"][1] == {"role": "user", "content": "Quel temps à Manosque ?"}
        textes = [e.content for e in evenements if e.type == "text"]
        assert textes == ["Bonjour", " Manosque"]
        fini = [e for e in evenements if e.type == "done"]
        assert len(fini) == 1
        assert fini[0].stop_reason == "stop"
        assert fini[0].input_tokens == 42
        assert fini[0].output_tokens == 7

    @pytest.mark.asyncio
    async def test_max_output_tokens_borne_a_128_000(self):
        """La fiche plafonne la sortie à 128 000, même si la config est plus haute."""
        client = _Client(_flux_texte())
        fournisseur = _provider(client)
        fournisseur.config.max_tokens = 200_000
        await _collecter(fournisseur.stream(None, MESSAGES, [OUTIL]))
        assert client.requests[0]["json"]["max_output_tokens"] == 128_000

        pile = _Client(_flux_texte())
        au_plafond = _provider(pile)
        au_plafond.config.max_tokens = 128_000
        await _collecter(au_plafond.stream(None, MESSAGES, [OUTIL]))
        assert pile.requests[0]["json"]["max_output_tokens"] == 128_000

        court = _Client(_flux_texte())
        sous_plafond = _provider(court)
        sous_plafond.config.max_tokens = 4_000
        await _collecter(sous_plafond.stream(None, MESSAGES, [OUTIL]))
        assert court.requests[0]["json"]["max_output_tokens"] == 4_000

    @pytest.mark.asyncio
    async def test_response_incomplete_n_est_pas_une_fin_normale(self):
        """response.incomplete (limite de sortie) n'est pas un stop."""
        client = _Client([
            _ligne({"type": "response.output_text.delta", "delta": "Début"}),
            _ligne({
                "type": "response.incomplete",
                "response": {
                    "status": "incomplete",
                    "incomplete_details": {"reason": "max_output_tokens"},
                    "usage": {"input_tokens": 11, "output_tokens": 128000},
                },
            }),
        ])
        evenements = await _collecter(_provider(client).stream(None, MESSAGES, [OUTIL]))
        assert [e.content for e in evenements if e.type == "text"] == ["Début"]
        finis = [e for e in evenements if e.type == "done"]
        assert len(finis) == 1
        assert finis[0].stop_reason == "incomplete"
        assert finis[0].input_tokens == 11
        assert finis[0].output_tokens == 128000

    @pytest.mark.asyncio
    async def test_piece_jointe_convertie_en_input_image(self):
        """Guide vision : Responses attend input_text et input_image, pas image_url."""
        image = "data:image/png;base64,iVBORw0KGgo="
        messages = [
            {"role": "system", "content": "Tu es THÉRÈSE."},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Que vois-tu ?"},
                    {"type": "image_url", "image_url": {"url": image}},
                ],
            },
        ]
        client = _Client(_flux_texte())
        await _collecter(_provider(client).stream(None, messages, [OUTIL]))
        assert client.requests[0]["url"].endswith("/v1/responses")
        contenu = client.requests[0]["json"]["input"][1]["content"]
        assert contenu == [
            {"type": "input_text", "text": "Que vois-tu ?"},
            {"type": "input_image", "image_url": image},
        ]

    @pytest.mark.asyncio
    async def test_sans_outils_chat_completions_et_effort_conserve(self):
        chunk = {"choices": [{"delta": {"content": "Texte"}, "finish_reason": "stop"}]}
        client = _Client([_ligne(chunk), "data: [DONE]"])
        evenements = await _collecter(_provider(client).stream(None, MESSAGES, None))

        assert client.requests[0]["url"].endswith("/v1/chat/completions")
        corps = client.requests[0]["json"]
        assert corps["reasoning_effort"] == "high"
        assert "tools" not in corps
        assert [e.content for e in evenements if e.type == "text"] == ["Texte"]

    @pytest.mark.asyncio
    async def test_sans_outils_une_sortie_au_dessus_du_plafond_est_bornee(self):
        """Le maximum officiel de 128 000 vaut aussi hors Responses."""
        client = _Client(["data: [DONE]"])
        fournisseur = _provider(client)
        fournisseur.config.max_tokens = 200_000
        await _collecter(fournisseur.stream(None, MESSAGES, None))
        corps = client.requests[0]["json"]
        assert client.requests[0]["url"].endswith("/v1/chat/completions")
        assert corps["max_completion_tokens"] == 128_000

        court = _Client(["data: [DONE]"])
        sous = _provider(court)
        sous.config.max_tokens = 4_000
        await _collecter(sous.stream(None, MESSAGES, None))
        assert court.requests[0]["json"]["max_completion_tokens"] == 4_000

    @pytest.mark.asyncio
    async def test_none_et_minimal_absents_du_corps_sans_outils(self):
        temoin = _Client(["data: [DONE]"])
        await _collecter(_provider(temoin, effort="high").stream(None, MESSAGES, None))
        assert temoin.requests[0]["json"]["reasoning_effort"] == "high"

        for effort in ("none", "minimal"):
            client = _Client(["data: [DONE]"])
            await _collecter(_provider(client, effort=effort).stream(None, MESSAGES, None))
            assert "reasoning_effort" not in client.requests[0]["json"]

    @pytest.mark.asyncio
    async def test_gpt6_sol_reste_sur_chat_completions_avec_none(self):
        """Fiche gpt-6-sol (09/10/2026) : Chat Completions accepte les outils
        seulement si reasoning_effort vaut none. On ne migre pas ce modèle."""
        client = _Client(["data: [DONE]"])
        await _collecter(_provider(client, "gpt-6-sol", "high").stream(None, MESSAGES, [OUTIL]))
        assert client.requests[0]["url"].endswith("/v1/chat/completions")
        assert client.requests[0]["json"]["reasoning_effort"] == "none"

    @pytest.mark.asyncio
    async def test_gpt6_astra_avec_outils_passe_par_responses(self):
        """Guides function-calling et raisonnement (09/10/2026) : Astra exige
        Responses pour les outils, et none renvoie HTTP 400."""
        from app.services.providers.openai import _outils_via_responses

        client = _Client(_flux_texte())
        await _collecter(_provider(client, "gpt-6-astra", "high").stream(None, MESSAGES, [OUTIL]))
        appel = client.requests[0]
        assert appel["url"].endswith("/v1/responses"), appel["url"]
        corps = appel["json"]
        assert corps["reasoning"] == {"effort": "high"}
        assert "reasoning_effort" not in corps
        assert corps["tools"][0]["name"] == "meteo"
        assert _outils_via_responses("gpt-6-astra") is True

    @pytest.mark.asyncio
    async def test_appel_outil_puis_continuation_avec_historique(self):
        client = _Client(_flux_outil())
        fournisseur = _provider(client)
        premier = await _collecter(fournisseur.stream(None, list(MESSAGES), [OUTIL]))
        appels = [e.tool_call for e in premier if e.type == "tool_call"]
        assert len(appels) == 1
        assert appels[0].id == "call_meteo"
        assert appels[0].name == "meteo"
        assert appels[0].arguments == {"ville": "Manosque"}
        assert [e for e in premier if e.type == "done"][0].stop_reason == "tool_calls"

        client._lignes = _flux_texte()
        suite = await _collecter(fournisseur.continue_with_tool_results(
            None,
            list(MESSAGES),
            "Je regarde.",
            appels,
            [ToolResult(tool_call_id="call_meteo", result="grand soleil")],
            tools=[OUTIL],
            prior_turns=[ToolTurn(
                assistant_content="",
                tool_calls=[ToolCall(id="call_ancien", name="agenda", arguments={"jour": "lundi"})],
                tool_results=[ToolResult(tool_call_id="call_ancien", result="rien")],
            )],
        ))

        entrees = client.requests[1]["json"]["input"]
        types_ou_roles = [
            item.get("type") or item.get("role") for item in entrees
        ]
        assert types_ou_roles == [
            "system",
            "user",
            "function_call",
            "function_call_output",
            "function_call",
            "function_call_output",
        ]
        assert entrees[2]["call_id"] == "call_ancien"
        assert entrees[2]["name"] == "agenda"
        assert entrees[3] == {
            "type": "function_call_output",
            "call_id": "call_ancien",
            "output": "rien",
        }
        assert entrees[4]["call_id"] == "call_meteo"
        assert entrees[5]["output"] == "grand soleil"
        assert [e.content for e in suite if e.type == "text"] == ["Bonjour", " Manosque"]

    @pytest.mark.asyncio
    async def test_continuation_rejoue_les_elements_de_raisonnement(self):
        """Le guide function-calling exige de rejouer les items de raisonnement."""
        raisonnement = {
            "type": "reasoning",
            "id": "rs_1",
            "encrypted_content": "chiffre-opaque",
            "summary": [],
        }
        appel_complet = {
            "type": "function_call",
            "id": "fc_1",
            "call_id": "call_meteo",
            "name": "meteo",
            "arguments": '{"ville":"Manosque"}',
            "status": "completed",
        }
        raisonnement_ancien = {
            "type": "reasoning",
            "id": "rs_ancien",
            "encrypted_content": "ancien-chiffre",
            "summary": [],
        }
        client = _Client([
            _ligne({
                "type": "response.output_item.done",
                "output_index": 0,
                "item": raisonnement,
            }),
            _ligne({
                "type": "response.output_item.done",
                "output_index": 1,
                "item": appel_complet,
            }),
            _ligne({
                "type": "response.completed",
                "response": {
                    "status": "completed",
                    "usage": {"input_tokens": 3, "output_tokens": 2},
                },
            }),
        ])
        fournisseur = _provider(client)
        premier = await _collecter(fournisseur.stream(None, list(MESSAGES), [OUTIL]))
        emis = [e for e in premier if e.type == "tool_call"]
        assert len(emis) == 1
        assert emis[0].assistant_content_brut == [raisonnement, appel_complet]

        client._lignes = _flux_texte()
        await _collecter(fournisseur.continue_with_tool_results(
            None,
            list(MESSAGES),
            "",
            [emis[0].tool_call],
            [ToolResult(tool_call_id="call_meteo", result="grand soleil")],
            tools=[OUTIL],
            assistant_content_brut=emis[0].assistant_content_brut,
            prior_turns=[ToolTurn(
                assistant_content="",
                tool_calls=[ToolCall(id="call_ancien", name="agenda", arguments={"jour": "lundi"})],
                tool_results=[ToolResult(tool_call_id="call_ancien", result="rien")],
                assistant_content_brut=[raisonnement_ancien],
            )],
        ))
        entrees = client.requests[1]["json"]["input"]
        assert entrees[2] == raisonnement_ancien
        assert entrees[3]["type"] == "function_call"
        assert entrees[3]["call_id"] == "call_ancien"
        assert entrees[4]["type"] == "function_call_output"
        assert entrees[5] == raisonnement
        assert entrees[6] == appel_complet
        assert entrees[7] == {
            "type": "function_call_output",
            "call_id": "call_meteo",
            "output": "grand soleil",
        }

    @pytest.mark.asyncio
    async def test_base_personnalisee_pointe_responses(self):
        client = _Client(_flux_texte())
        fournisseur = _provider(client)
        fournisseur.config.base_url = "https://exemple.test/v1/chat/completions"
        await _collecter(fournisseur.stream(None, MESSAGES, [OUTIL]))
        assert client.requests[0]["url"] == "https://exemple.test/v1/responses"

    @pytest.mark.asyncio
    async def test_annulation_ferme_la_requete(self):
        client = _ClientBloquant(_ligne({
            "type": "response.output_text.delta",
            "delta": "Bonjour",
        }))
        generateur = _provider(client).stream(None, MESSAGES, [OUTIL])
        try:
            premier = await asyncio.wait_for(generateur.__anext__(), timeout=1)
        except TimeoutError:
            pytest.fail(f"pas de texte ; appels={client.requests}")
        assert client.requests[0]["url"].endswith("/v1/responses")
        assert premier.type == "text"
        assert premier.content == "Bonjour"
        await generateur.aclose()
        assert client.ferme, "fermer le flux doit fermer la requête HTTP"

    @pytest.mark.asyncio
    async def test_erreur_http_ne_montre_pas_le_corps(self):
        vus: list[str] = []

        def repondre(requete: httpx.Request) -> httpx.Response:
            vus.append(str(requete.url))
            return httpx.Response(401, json={"error": {"message": "sk-secret-99"}})

        client = httpx.AsyncClient(transport=httpx.MockTransport(repondre))
        evenements = await _collecter(_provider(client).stream(None, MESSAGES, [OUTIL]))
        erreurs = [e for e in evenements if e.type == "error"]
        assert vus == ["https://api.openai.com/v1/responses"]
        assert len(erreurs) == 1
        assert "clé" in (erreurs[0].content or "").lower()
        assert "sk-secret" not in (erreurs[0].content or "")
        assert not any(e.type == "done" for e in evenements)

    @pytest.mark.asyncio
    async def test_erreur_sse_ne_fuite_pas_et_compte_une_panne_serveur(self):
        from app.services.llm import _is_provider_outage

        client = _Client([_ligne({
            "type": "response.failed",
            "response": {
                "status": "failed",
                "error": {"code": "server_error", "message": "boom sk-secret-99"},
            },
        })])
        evenements = await _collecter(_provider(client).stream(None, MESSAGES, [OUTIL]))
        erreurs = [e for e in evenements if e.type == "error"]
        assert len(erreurs) == 1
        assert erreurs[0].content == "API error: 500"
        assert "sk-secret" not in (erreurs[0].content or "")
        assert _is_provider_outage(erreurs[0].content) is True
        assert not any(e.type == "done" for e in evenements)

    def test_propose_aux_agents_parce_que_le_transport_existe(self):
        from app.services.agents.config import AVAILABLE_MODELS
        from app.services.providers.openai import _outils_via_responses

        assert _outils_via_responses(MODELE) is True
        assert _outils_via_responses("gpt-6-sol") is False
        trouve = [m for m in AVAILABLE_MODELS if m["id"] == MODELE]
        assert len(trouve) == 1
        assert trouve[0]["provider"] == "openai"
        assert trouve[0].get("recommended") is not True


class TestResponsesReserveAOpenAI:
    """Un héritier (Grok, GLM, Kimi, MiniMax, Qwen) ne parle jamais à OpenAI.

    Le basculement Responses ne regarde que le nom du modèle. Un identifiant
    personnalisé « gpt-6.1-sol » ou « gpt-6-astra » sur un autre fournisseur
    enverrait la clé de ce fournisseur à api.openai.com.
    """

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ("type_fournisseur", "fournisseur", "adresse"),
        [
            (GrokProvider, LLMProvider.GROK, "https://api.x.ai/v1/chat/completions"),
            (GLMProvider, LLMProvider.GLM, "https://api.z.ai/api/paas/v4/chat/completions"),
            (KimiProvider, LLMProvider.KIMI, "https://api.moonshot.ai/v1/chat/completions"),
            (MiniMaxProvider, LLMProvider.MINIMAX, "https://api.minimax.io/v1/chat/completions"),
            (
                QwenProvider,
                LLMProvider.QWEN,
                "https://{EspaceDeTravail}.ap-southeast-1.maas.aliyuncs.com"
                "/compatible-mode/v1/chat/completions",
            ),
        ],
    )
    @pytest.mark.parametrize("modele", ["gpt-6.1-sol", "gpt-6-astra"])
    async def test_un_heritier_garde_sa_cle_et_son_adresse(
        self, type_fournisseur, fournisseur, adresse, modele,
    ):
        client = _Client(["data: [DONE]"])
        config = LLMConfig(
            provider=fournisseur,
            model=modele,
            api_key=f"cle-{fournisseur.value}",
        )
        instance = type_fournisseur(config, client)
        await _collecter(instance.stream(None, MESSAGES, [OUTIL]))

        assert client.requests, "aucun appel enregistré"
        for appel in client.requests:
            assert "api.openai.com" not in appel["url"], appel["url"]
            assert appel["url"] == adresse, appel["url"]
            assert appel["headers"]["Authorization"] == f"Bearer cle-{fournisseur.value}"
        repli = instance.url_responses()
        assert "api.openai.com" not in repli, repli
        assert repli == adresse.removesuffix("/chat/completions") + "/responses"
