"""Gemini 3 exige le renvoi de la thought signature au tour suivant.

Documentation Google (Thought signatures) : « When using Gemini 3 models,
you must pass back thought signatures during function calling, otherwise
you will get a validation error (4xx status code). » La signature est un
champ du PART, à côté de `functionCall`, et seul le PREMIER functionCall
d'une étape la porte.

Sans elle, tout usage d'outil sur un modèle Gemini 3 (mail, agenda,
recherche, facture) casse au second tour. Contrôle post-release des
0.48.x, trouvé le 26/08/2026.
"""

import json

import pytest
from app.services.providers.base import LLMConfig, LLMProvider, ToolCall, ToolResult
from app.services.providers.gemini import GeminiProvider

from tests.test_provider_tools import OPENAI_TOOLS, _collect, _FakeClient


def _gemini(client, model: str = "gemini-3.7-flash") -> GeminiProvider:
    return GeminiProvider(
        LLMConfig(provider=LLMProvider.GEMINI, model=model, api_key="x"),
        client=client,
    )


def _chunk(parts: list[dict]) -> str:
    return "data: " + json.dumps({"candidates": [{"content": {"parts": parts}}]})


class TestLaSignatureEstCaptee:
    @pytest.mark.asyncio
    async def test_le_parser_retient_la_signature_du_part(self):
        client = _FakeClient([
            _chunk([
                {
                    "functionCall": {"name": "create_contact", "args": {"name": "Marie"}},
                    "thoughtSignature": "SIG_PREMIER",
                }
            ])
        ])

        events = await _collect(
            _gemini(client).stream(
                None, [{"role": "user", "parts": [{"text": "x"}]}], tools=OPENAI_TOOLS
            )
        )

        appels = [e.tool_call for e in events if e.type == "tool_call"]
        assert len(appels) == 1
        assert appels[0].signature_raisonnement == "SIG_PREMIER"

    @pytest.mark.asyncio
    async def test_un_appel_sans_signature_n_en_invente_pas(self):
        """Sur des appels parallèles, Google n'en met que sur le premier."""
        client = _FakeClient([
            _chunk([
                {
                    "functionCall": {"name": "create_contact", "args": {"name": "A"}},
                    "thoughtSignature": "SIG_PREMIER",
                },
                {"functionCall": {"name": "create_contact", "args": {"name": "B"}}},
            ])
        ])

        events = await _collect(
            _gemini(client).stream(
                None, [{"role": "user", "parts": [{"text": "x"}]}], tools=OPENAI_TOOLS
            )
        )

        appels = [e.tool_call for e in events if e.type == "tool_call"]
        assert len(appels) == 2
        assert appels[0].signature_raisonnement == "SIG_PREMIER"
        assert appels[1].signature_raisonnement is None


class TestLaSignatureEstRejouee:
    @pytest.mark.asyncio
    async def test_le_tour_model_rejoue_la_signature_a_cote_du_function_call(self):
        client = _FakeClient([_chunk([{"text": "fini"}])])
        appel = ToolCall(
            id="call_1",
            name="create_contact",
            arguments={"name": "Marie"},
            signature_raisonnement="SIG_PREMIER",
        )

        await _collect(
            _gemini(client).continue_with_tool_results(
                None,
                [{"role": "user", "parts": [{"text": "x"}]}],
                "",
                [appel],
                [ToolResult(tool_call_id="call_1", result={"ok": True})],
                tools=OPENAI_TOOLS,
            )
        )

        contents = client.last_request["json"]["contents"]
        tour_model = [c for c in contents if c["role"] == "model"][-1]
        part = tour_model["parts"][0]
        assert "functionCall" in part
        assert part.get("thoughtSignature") == "SIG_PREMIER", (
            "signature absente du rejeu : Gemini 3 répondra 400"
        )

    @pytest.mark.asyncio
    async def test_sans_signature_aucun_champ_n_est_ajoute(self):
        """Gemini 2.x n'en émet pas : ne pas inventer un champ vide."""
        client = _FakeClient([_chunk([{"text": "fini"}])])
        appel = ToolCall(id="call_1", name="create_contact", arguments={})

        await _collect(
            _gemini(client, "gemini-2.5-flash").continue_with_tool_results(
                None,
                [{"role": "user", "parts": [{"text": "x"}]}],
                "",
                [appel],
                [ToolResult(tool_call_id="call_1", result={"ok": True})],
                tools=OPENAI_TOOLS,
            )
        )

        contents = client.last_request["json"]["contents"]
        tour_model = [c for c in contents if c["role"] == "model"][-1]
        assert "thoughtSignature" not in tour_model["parts"][0]


class TestLeSamplingNEstPasEnvoyeAuxGemini3:
    """Google : « Strip temperature, top_p, and top_k from generation configs. »

    Le paramètre n'est pas rejeté (il est accepté puis ignoré), donc rien ne
    casse visiblement — mais Google avertit qu'une température sous 1.0 sur
    Gemini 3 provoque « boucles ou performance dégradée, en particulier sur
    les tâches de raisonnement complexes ». Or le Board délibère en effort
    maximal sur `gemini-3.7-flash`, avec 0.7 par défaut : exactement le cas
    décrit. On cesse donc d'envoyer un paramètre sans effet et nuisible.
    """

    @pytest.mark.asyncio
    async def test_gemini_3_ne_recoit_pas_de_temperature(self):
        client = _FakeClient([_chunk([{"text": "ok"}])])

        await _collect(
            _gemini(client, "gemini-3.7-flash").stream(
                None, [{"role": "user", "parts": [{"text": "x"}]}]
            )
        )

        config = client.last_request["json"]["generationConfig"]
        assert "temperature" not in config
        assert config["maxOutputTokens"], "le reste de la config doit survivre"

    @pytest.mark.asyncio
    async def test_les_gemini_2_gardent_leur_temperature(self):
        """Le retrait ne vaut QUE pour la famille 3."""
        client = _FakeClient([_chunk([{"text": "ok"}])])

        await _collect(
            _gemini(client, "gemini-2.5-flash").stream(
                None, [{"role": "user", "parts": [{"text": "x"}]}]
            )
        )

        assert "temperature" in client.last_request["json"]["generationConfig"]
