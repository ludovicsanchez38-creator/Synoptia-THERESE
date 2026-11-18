"""La preuve de frontière doit détecter l'absence d'erreur et toute fuite."""

import json

import pytest
from app.services.providers.base import StreamEvent, ToolCall
from app.services.providers.ollama import OllamaProvider
from app.services.providers.openrouter import OpenRouterProvider

from tests.test_frontiere_erreurs import TestRevueSosoPasse2 as VerificationFrontiere


@pytest.mark.asyncio
@pytest.mark.parametrize("provider", [OpenRouterProvider, OllamaProvider], ids=["openrouter", "ollama"])
@pytest.mark.parametrize("defaut", ["aucun_evenement", "fuite_dans_texte", "fuite_dans_outil"])
async def test_preuve_refuse_les_evenements_manquants_ou_non_surs(monkeypatch, provider, defaut):
    async def flux_defectueux(self, *args, **kwargs):
        if defaut != "aucun_evenement":
            reponse = self.client.stream()
            ligne = await anext(reponse.aiter_lines())
            charge = json.loads(ligne.removeprefix("data: "))["error"]
            contenu = charge["message"] if isinstance(charge, dict) else charge
            yield StreamEvent(type="error", content="Erreur factice.")
            if defaut == "fuite_dans_texte":
                yield StreamEvent(type="text", content=contenu)
            else:
                yield StreamEvent(type="tool_call", tool_call=ToolCall(
                    id="fictif", name="outil_fictif", arguments={"detail": contenu},
                ))

    monkeypatch.setattr(provider, "stream", flux_defectueux)
    with pytest.raises(AssertionError):
        await VerificationFrontiere().test_p7_f2_openrouter_et_ollama_ne_relaient_pas_le_detail(
            monkeypatch
        )
