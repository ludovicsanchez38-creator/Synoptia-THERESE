"""gpt-6.1-terra (demande de Ludo du 26/10/2026, jour de sa sortie).

Fiche lue le 26/10/2026 : https://developers.openai.com/api/docs/models/gpt-6.1-terra
- contexte 1 050 000 (entrée 922 000), sortie 128 000 ;
- reasoning.effort : none, low, medium (défaut), high, xhigh, max ;
- Chat Completions et Responses, « l'appel d'outils nécessite Responses » ;
- 1 $ / 5 $ le million ; au-delà de 272 000 jetons d'entrée, entrée × 2 et
  sortie × 1,5 sur toute la requête.

Même mécanique que gpt-6.1-sol (lot M2) : seules les données changent.
Client simulé, aucun appel réseau.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tests.test_gpt61_sol_responses import (
    MESSAGES,
    OUTIL,
    _Client,
    _collecter,
    _flux_outil,
    _flux_texte,
    _ligne,
    _provider,
)

MODELE = "gpt-6.1-terra"
RACINE = Path(__file__).resolve().parents[1]


class TestCatalogue:
    def test_present_apres_6_1_sol_sans_prendre_la_tete(self):
        from app.services.modeles_catalogue import CATALOGUE, fenetre_de_contexte, frontier

        openai = CATALOGUE["openai"]
        assert frontier("openai") == "gpt-6-sol"
        assert openai.modeles[:3] == ("gpt-6-sol", "gpt-6-astra", "gpt-6-luna")
        assert openai.modeles.index(MODELE) == openai.modeles.index("gpt-6.1-sol") + 1
        assert "gpt-5.6-terra" in openai.modeles, "l'ancien Terra reste proposé"
        assert fenetre_de_contexte("openai", MODELE) == 1_050_000

    @pytest.mark.parametrize("effort", ["none", "low", "medium", "high", "xhigh", "max"])
    def test_effort_documente_transmis_tel_quel(self, effort):
        from app.services.modeles_catalogue import resoudre_effort

        assert resoudre_effort(MODELE, effort, "openai") == effort

    def test_le_reglage_accepte_l_effort_xhigh(self):
        from app.models.schemas import LLMConfigUpdate

        assert LLMConfigUpdate(provider="openai", model=MODELE, effort="xhigh").effort == "xhigh"

    def test_l_atelier_le_propose(self):
        from app.services.agents.config import AVAILABLE_MODELS

        assert {"id": MODELE, "name": "GPT-6.1 Terra", "provider": "openai"} in AVAILABLE_MODELS

    def test_le_repli_de_l_interface_est_a_jour(self):
        from app.services.modeles_catalogue import catalogue_pour_interface

        chemin = RACINE / "src/frontend/src/lib/modelesCatalogue.generated.json"
        assert json.loads(chemin.read_text(encoding="utf-8")) == catalogue_pour_interface()


class TestTarif:
    def test_standard_1_et_5_dollars(self):
        from app.services.token_tracker import TOKEN_PRICES, TokenTracker

        assert TOKEN_PRICES[MODELE] == {"input": 1.00, "output": 5.00}
        traceur = object.__new__(TokenTracker)
        assert traceur.tarif_connu(MODELE) is True
        assert traceur.estimate_cost(MODELE, 42, 7) == pytest.approx(
            42 / 1_000_000 * 1.00 + 7 / 1_000_000 * 5.00
        )

    def test_palier_au_dela_de_272_000_jetons_entree(self):
        from app.services import token_tracker

        palier = token_tracker.PALIERS_TARIF[MODELE]
        assert (palier.seuil_entree, palier.multiplicateur_entree, palier.multiplicateur_sortie) == (
            272_000, 2.0, 1.5,
        )
        traceur = object.__new__(token_tracker.TokenTracker)
        assert traceur.estimate_cost(MODELE, 272_000, 1_000) == pytest.approx(
            272_000 / 1_000_000 * 1.00 + 1_000 / 1_000_000 * 5.00
        )
        assert traceur.estimate_cost(MODELE, 272_001, 1_000) == pytest.approx(
            272_001 / 1_000_000 * 1.00 * 2 + 1_000 / 1_000_000 * 5.00 * 1.5
        )


class TestTransport:
    @pytest.mark.asyncio
    async def test_avec_outils_responses_et_effort_conserve(self):
        from app.services.providers.openai import _outils_via_responses

        client = _Client(_flux_texte())
        evenements = await _collecter(_provider(client, MODELE, "xhigh").stream(None, MESSAGES, [OUTIL]))
        appel = client.requests[0]
        assert appel["url"] == "https://api.openai.com/v1/responses"
        corps = appel["json"]
        assert corps["model"] == MODELE
        assert corps["reasoning"] == {"effort": "xhigh"}
        assert "reasoning_effort" not in corps
        assert corps["tools"][0]["name"] == "meteo"
        assert [e.content for e in evenements if e.type == "text"] == ["Bonjour", " Manosque"]
        assert _outils_via_responses(MODELE) is True
        assert _outils_via_responses("GPT-6.1-Terra") is True

    @pytest.mark.asyncio
    async def test_l_appel_d_outil_revient_par_responses(self):
        client = _Client(_flux_outil())
        evenements = await _collecter(_provider(client, MODELE).stream(None, MESSAGES, [OUTIL]))
        appels = [e.tool_call for e in evenements if e.type == "tool_call"]
        assert len(appels) == 1
        assert appels[0].name == "meteo"
        assert appels[0].arguments == {"ville": "Manosque"}

    @pytest.mark.asyncio
    async def test_none_part_avec_les_outils(self):
        """La fiche de Terra accepte none, contrairement à 6.1 Sol et Astra."""
        client = _Client(_flux_texte())
        await _collecter(_provider(client, MODELE, "none").stream(None, MESSAGES, [OUTIL]))
        assert client.requests[0]["json"]["reasoning"] == {"effort": "none"}

    @pytest.mark.asyncio
    async def test_sortie_bornee_a_128_000_sur_les_deux_points_d_appel(self):
        avec = _Client(_flux_texte())
        fournisseur = _provider(avec, MODELE)
        fournisseur.config.max_tokens = 200_000
        await _collecter(fournisseur.stream(None, MESSAGES, [OUTIL]))
        assert avec.requests[0]["json"]["max_output_tokens"] == 128_000

        sans = _Client(["data: [DONE]"])
        fournisseur = _provider(sans, MODELE)
        fournisseur.config.max_tokens = 200_000
        await _collecter(fournisseur.stream(None, MESSAGES, None))
        assert sans.requests[0]["url"].endswith("/v1/chat/completions")
        assert sans.requests[0]["json"]["max_completion_tokens"] == 128_000

    @pytest.mark.asyncio
    async def test_sans_outils_chat_completions_et_effort_transmis(self):
        chunk = {"choices": [{"delta": {"content": "Texte"}, "finish_reason": "stop"}]}
        client = _Client([_ligne(chunk), "data: [DONE]"])
        await _collecter(_provider(client, MODELE, "max").stream(None, MESSAGES, None))
        assert client.requests[0]["url"].endswith("/v1/chat/completions")
        assert client.requests[0]["json"]["reasoning_effort"] == "max"

    # Dix entrées inventées après coup : effort, casse du nom, plafond demandé.
    @pytest.mark.asyncio
    @pytest.mark.parametrize(("effort", "demande", "attendu"), [
        ("low", 1, 1),
        ("medium", 4_096, 4_096),
        ("high", 127_999, 127_999),
        ("xhigh", 128_000, 128_000),
        ("max", 128_001, 128_000),
        ("none", 1_000_000, 128_000),
        (None, 64_000, 64_000),
        ("low", 300_000, 128_000),
        ("medium", 2, 2),
        ("max", 65_536, 65_536),
    ])
    async def test_rejeu(self, effort, demande, attendu):
        client = _Client(_flux_texte())
        fournisseur = _provider(client, MODELE, effort)
        fournisseur.config.max_tokens = demande
        await _collecter(fournisseur.stream(None, MESSAGES, [OUTIL]))
        corps = client.requests[0]["json"]
        assert client.requests[0]["url"].endswith("/v1/responses")
        assert corps["max_output_tokens"] == attendu
        if effort is None:
            assert "reasoning" not in corps
        else:
            assert corps["reasoning"] == {"effort": effort}
