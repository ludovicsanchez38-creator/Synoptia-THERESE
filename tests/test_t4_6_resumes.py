"""Atelier documentaire : titres, trames et résumés relèvent de l'accord « llm ».

Tour 6 les traitait comme documentaires ; la relecture 6 (constat 5) a montré
que l'atelier ne lit aucun fichier : tout vient de la saisie de l'utilisateur.
Retirer l'accord « documents » ne bloque donc plus l'atelier ; sans accord
« llm », rien ne part (voir tests/test_t4_7_regressions.py)."""

import httpx
import pytest
from app.models.database import get_sync_session
from app.models.entities import DocumentSection
from app.services.consentements import enregistrer_accord
from app.services.llm import LLMConfig, LLMProvider, LLMService
from app.services.providers.openai import OpenAIProvider

from tests.test_t4_5_chemins_differes import texte_sse


@pytest.mark.parametrize("etape", ["resume", "redaction", "trame"])
async def test_reprise_atelier_apres_retrait(client, monkeypatch, etape):
    from app.routers import documents

    enregistrer_accord("llm", "openai", True, "3", [])
    enregistrer_accord("documents", "openai", True, "3", [])
    enregistrer_accord("documents", "openai", False, "3", [])
    envois = []

    async def transport(req):
        envois.append(req.content)
        return httpx.Response(
            200, headers={"content-type": "text/event-stream"}, text=texte_sse("Réponse fictive")
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(transport)) as http:
        svc = LLMService(LLMConfig(LLMProvider.OPENAI, "gpt-4o", api_key="factice"))
        svc._provider = OpenAIProvider(svc.config, http)
        monkeypatch.setattr(documents, "get_llm_service", lambda: svc)
        doc = (
            await client.post(
                "/api/documents", json={"title": "REFERENCE_AMBRE", "brief": "Fictif"}
            )
        ).json()
        section = (
            await client.post(
                f"/api/documents/{doc['id']}/sections",
                json={"title": "Fictif", "brief": "", "order": 0, "depth": 0},
            )
        ).json()
        with get_sync_session() as s:
            ligne = s.get(DocumentSection, section["id"])
            ligne.content = "" if etape == "trame" else "REFERENCE_AMBRE"
            ligne.summary = "REFERENCE_AMBRE"
            s.add(ligne)
            s.commit()
        if etape == "resume":
            reponse = await client.post(f"/api/documents/sections/{section['id']}/validate")
        elif etape == "redaction":
            reponse = await client.post(f"/api/documents/sections/{section['id']}/draft", json={})
        else:
            reponse = await client.post(f"/api/documents/{doc['id']}/outline")
        # Un seul envoi, sous l'accord « llm » : la saisie de l'utilisateur.
        assert len(envois) == 1, reponse.text
        assert b"REFERENCE_AMBRE" in envois[0]
        assert "accord" not in reponse.text, reponse.text
