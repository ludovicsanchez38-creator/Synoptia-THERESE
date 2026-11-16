"""La preuve existante doit détecter une attribution incorrecte du chat."""

import pytest
from app.routers import chat
from app.services.llm import LLMService
from app.services.providers.base import LLMConfig, LLMProvider, StreamEvent

from tests.test_pluriel_fournisseur import (
    test_apres_bascule_l_attribution_est_celle_du_repli as verifier_preuve,
)
from tests.test_r2_3_outil import fournisseur  # noqa: F401


@pytest.mark.asyncio
async def test_preuve_echoue_si_le_chat_annonce_le_fournisseur_choisi(monkeypatch):
    class FournisseurFictif:
        async def stream(self, *args, **kwargs):
            yield StreamEvent(type="text", content="Réponse fictive")
            yield StreamEvent(type="done")

    async def fournisseur_pour(self, config):
        return FournisseurFictif()

    monkeypatch.setattr(LLMService, "_provider_pour", fournisseur_pour)
    monkeypatch.setattr(chat, "_attribution", lambda service: ("anthropic", "modele-choisi"))
    with pytest.raises(AssertionError):
        await verifier_preuve(monkeypatch)


@pytest.mark.asyncio
@pytest.mark.parametrize("stream", [True, False])
async def test_reponse_chat_annonce_le_fournisseur_effectif(
    client, db_session, fournisseur, monkeypatch, stream  # noqa: F811
):
    import json

    service = fournisseur[0]
    service.config = LLMConfig(LLMProvider.ANTHROPIC, "modele-choisi")
    repli = LLMConfig(LLMProvider.OPENAI, "modele-repli")
    monkeypatch.setattr(service, "_resolve_with_circuit_breaker", lambda: repli)
    monkeypatch.setattr("app.services.consentements.verifier_envoi_llm", lambda *a, **k: None)

    async def fournisseur_pour(config):
        return service._provider

    monkeypatch.setattr(service, "_provider_pour", fournisseur_pour)
    reponse = await client.post(
        "/api/chat/send", json={"message": "Bonjour", "stream": stream, "include_memory": False}
    )
    assert reponse.status_code == 200
    if stream:
        evenements = [json.loads(ligne[6:]) for ligne in reponse.text.splitlines() if ligne.startswith("data: ")]
        resultat = next(e for e in evenements if e["type"] == "done")
        assert resultat["usage"]["model"] == "modele-repli"
        assert resultat["usage"]["provider"] == "openai"
    else:
        resultat = reponse.json()
        assert resultat["model"] == "modele-repli"
    assert resultat["provider"] == "openai"
