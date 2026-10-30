"""Reproductions API du cinquième tour : transport en mémoire exclusivement."""

import json

import httpx
import pytest
from app.services.consentements import accord_valide, enregistrer_accord
from app.services.context import ContextWindow
from app.services.envoi_fournisseur import TransportAvecAccord
from app.services.error_handler import ErreurPourEcran
from app.services.llm import LLMConfig, LLMProvider, LLMService
from app.services.providers.base import Message as LLMMessage
from app.services.providers.openai import OpenAIProvider

EXTRAIT = "TEMOIN_DOCUMENTAIRE_RELECTURE_QUATRE"



def texte_sse(texte):
    return (
        "data: "
        + json.dumps(
            {"choices": [{"index": 0, "delta": {"content": texte}, "finish_reason": None}]}
        )
        + "\n\n"
        + "data: "
        + json.dumps({"choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}]})
        + "\n\n"
        + "data: [DONE]\n\n"
    )


@pytest.mark.parametrize("code", [307, 308])
async def test_redirection_http_refuse_apres_retrait(client, code):
    enregistrer_accord("llm", "openai", True, "3", [])
    envois = []

    async def transport(req):
        envois.append({"body": req.content.decode(), "accord": accord_valide("llm", "openai")})
        if len(envois) == 1:
            enregistrer_accord("llm", "openai", False, "3", [])
            return httpx.Response(
                code, headers={"location": "https://api.openai.com/v1/suite-fictive"}
            )
        return httpx.Response(
            200, headers={"content-type": "text/event-stream"}, text=texte_sse("Réponse fictive")
        )

    async with httpx.AsyncClient(
        transport=httpx.MockTransport(transport), follow_redirects=True
    ) as http:
        svc = LLMService(LLMConfig(LLMProvider.OPENAI, "gpt-4o", api_key="factice"))
        svc._provider = OpenAIProvider(svc.config, http)
        context = ContextWindow(messages=[LLMMessage(role="user", content=EXTRAIT)])
        with pytest.raises(ErreurPourEcran, match="redirection"):
            _ = [e async for e in svc.stream_response_with_tools(context)]
    assert len(envois) == 1 and [x["accord"] for x in envois] == [True]


@pytest.mark.parametrize("methode", ["post", "get", "stream"])
@pytest.mark.parametrize("code", [301, 302, 303, 307, 308])
@pytest.mark.parametrize(
    "destination", ["https://api.openai.com/suite", "https://autre.invalid/suite"]
)
async def test_aucune_redirection_automatique(methode, code, destination):
    envois = []

    async def repondre(request):
        envois.append(request)
        return httpx.Response(code, headers={"location": destination})

    async with httpx.AsyncClient(
        transport=httpx.MockTransport(repondre), follow_redirects=True
    ) as client:
        transport = TransportAvecAccord(client, lambda: None)
        with pytest.raises(ErreurPourEcran, match="Vérifie la destination"):
            if methode == "stream":
                async with transport.stream(
                    "POST", "https://api.openai.com/fictif", content="PRIVE", follow_redirects=True
                ):
                    pass
            else:
                await getattr(transport, methode)(
                    "https://api.openai.com/fictif", follow_redirects=True
                )
    assert len(envois) == 1
