"""Septième tour : l'atelier documentaire sous l'accord « llm » (constat 5 de la relecture 6).

Relecture 6 de la branche confidentialité ; transport HTTPX en mémoire,
adaptateur OpenAI réel, aucun envoi réseau.
"""

import json

import httpx
import pytest
from app.models.database import get_sync_session
from app.models.entities import DocumentSection
from app.services.consentements import enregistrer_accord
from app.services.llm import LLMConfig, LLMProvider, LLMService
from app.services.providers.openai import OpenAIProvider

from tests.test_t4_5_chemins_differes import texte_sse

# ---------------------------------------------------------------------------
# Bloquant 5 : l'atelier ne lit aucun document, l'accord « llm » lui suffit.
# ---------------------------------------------------------------------------


async def _atelier(client, monkeypatch, etape, transport):
    from app.routers import documents

    async with httpx.AsyncClient(transport=httpx.MockTransport(transport)) as http:
        svc = LLMService(LLMConfig(LLMProvider.OPENAI, "gpt-4o", api_key="factice"))
        svc._provider = OpenAIProvider(svc.config, http)
        monkeypatch.setattr(documents, "get_llm_service", lambda: svc)
        doc = (await client.post("/api/documents", json={"title": "Plan commercial", "brief": "Pour 2027"})).json()
        section = (await client.post(f"/api/documents/{doc['id']}/sections",
                                     json={"title": "Objectifs", "brief": "", "order": 0, "depth": 0})).json()
        if etape != "trame":
            with get_sync_session() as s:
                ligne = s.get(DocumentSection, section["id"])
                ligne.content = "Texte écrit à la main pour les objectifs de l'année."
                s.add(ligne)
                s.commit()
        if etape == "resume":
            return await client.post(f"/api/documents/sections/{section['id']}/validate")
        if etape == "redaction":
            return await client.post(f"/api/documents/sections/{section['id']}/draft", json={})
        return await client.post(f"/api/documents/{doc['id']}/outline")


@pytest.mark.parametrize("etape", ["resume", "redaction", "trame"])
async def test_atelier_avec_le_seul_accord_llm(client, monkeypatch, etape):
    enregistrer_accord("llm", "openai", True, "3", [])
    envois = []

    async def transport(req):
        envois.append(req.content)
        texte = json.dumps([{"title": "Objectifs", "brief": "Fictif"}]) if etape == "trame" else "Résumé du modèle."
        return httpx.Response(200, headers={"content-type": "text/event-stream"}, text=texte_sse(texte))

    reponse = await _atelier(client, monkeypatch, etape, transport)
    assert len(envois) == 1, reponse.text
    assert "accord" not in reponse.text, reponse.text
    if etape == "resume":
        assert reponse.status_code == 200
        assert reponse.json()["summary"] == "Résumé du modèle."
        assert reponse.json().get("avis") is None


@pytest.mark.parametrize("etape", ["resume", "redaction", "trame"])
async def test_atelier_sans_accord_rien_ne_part(client, monkeypatch, etape):
    envois = []

    async def transport(req):
        envois.append(req.content)
        return httpx.Response(200, headers={"content-type": "text/event-stream"}, text=texte_sse("Fictif"))

    reponse = await _atelier(client, monkeypatch, etape, transport)
    assert not envois
    if etape == "resume":
        # La validation reste locale, avec un avis visible.
        assert reponse.status_code == 200, reponse.text
        corps = reponse.json()
        assert corps["status"] == "validee"
        assert corps["summary"].startswith("Texte écrit à la main")
        assert "accord" in corps["avis"] and "Rien n’a été envoyé" in corps["avis"]
    elif etape == "trame":
        assert reponse.status_code == 403, reponse.text
        assert "accord" in reponse.text
    else:
        assert "accord" in reponse.text
