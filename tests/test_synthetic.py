"""Parcours Synthetic par l'API publique avec flux HTTP simulé."""

import json

import httpx
import pytest

MODELE = "hf:moonshotai/Kimi-K3.1-Pro"
ALIAS = "syn:large:text"
MODELE_TOURNANT = "hf:example/Modele-test"
CLE_FICTIVE = "cle-fictive-pour-le-test"
API = "https://api.synthetic.new/openai/v1"
OUTIL = "search_invoices"


def _flux_sse(*charges):
    return "".join(f"data: {json.dumps(c)}\n\n" for c in charges) + "data: [DONE]\n\n"


@pytest.mark.asyncio
async def test_synthetic_de_la_cle_au_rejeu_outil_par_les_routes_publiques(client, monkeypatch):
    from app.routers import config as routes_config
    from app.services import http_client, llm
    from app.services.modeles_catalogue import libelle_modele

    from tests.test_routers_invoices import _create_contact, _create_invoice

    contact_id = await _create_contact(client)
    facture = await _create_invoice(client, contact_id)
    reference = facture["invoice_number"]
    appels = []

    def fournir(request):
        if str(request.url) == f"{API}/models":
            assert request.method == "GET"
            assert "authorization" not in request.headers
            return httpx.Response(200, json={"data": [
                {"id": MODELE_TOURNANT}, {"id": MODELE}, {"id": ALIAS},
            ]})
        if request.url.path == "/api/tags":
            return httpx.Response(503)
        assert str(request.url) == f"{API}/chat/completions"
        assert request.headers["authorization"] == f"Bearer {CLE_FICTIVE}"
        corps = json.loads(request.content)
        appels.append(corps)
        assert corps["model"] == MODELE
        assert corps["stream"] is True
        if len(appels) == 1:
            assert OUTIL in {outil["function"]["name"] for outil in corps["tools"]}
            flux = _flux_sse(
                {"choices": [{"delta": {"tool_calls": [{
                    "index": 0,
                    "id": "r_facture",
                    "type": "function",
                    "function": {"name": OUTIL, "arguments": json.dumps({"query": reference})},
                }]}}]},
                {"choices": [{"delta": {}, "finish_reason": "tool_calls"}]},
            )
        else:
            assert any(
                m["role"] == "tool" and m["tool_call_id"] == "r_facture" and reference in m["content"]
                for m in corps["messages"]
            )
            flux = _flux_sse(
                {"choices": [{"delta": {"content": "Recherche Synthetic terminée."}}]},
                {"choices": [{"delta": {}, "finish_reason": "stop"}]},
            )
        return httpx.Response(200, text=flux, headers={"content-type": "text/event-stream"})

    async with httpx.AsyncClient(transport=httpx.MockTransport(fournir)) as fournisseur:
        async def get_client():
            return fournisseur

        monkeypatch.setattr(llm, "_llm_service", None)
        monkeypatch.setattr(http_client, "get_http_client", get_client)
        monkeypatch.setattr(routes_config, "get_http_client", get_client)

        pose = await client.post("/api/config/api-key", json={"provider": "synthetic", "api_key": CLE_FICTIVE})
        assert pose.status_code == 200, pose.text
        configuration = await client.get("/api/config/")
        assert configuration.json()["api_keys"]["synthetic"] is True
        verification = await client.post("/api/config/api-key/verifier", json={"provider": "synthetic"})
        assert verification.json()["etat"] == "non_verifiable"

        liste = await client.get("/api/config/llm/models/synthetic")
        assert liste.status_code == 200, liste.text
        assert {MODELE, ALIAS, MODELE_TOURNANT} <= set(liste.json()["models"])
        for identifiant in (ALIAS, MODELE):
            selection = await client.post("/api/config/llm", json={"provider": "synthetic", "model": identifiant})
            assert selection.status_code == 200, selection.text
            assert selection.json()["model"] == identifiant
            assert selection.json()["consent_provider"] == "synthetic"
            monkeypatch.setattr(llm, "_llm_service", None)
            assert (await client.get("/api/config/llm")).json()["model"] == identifiant

        assert libelle_modele(MODELE) == "Kimi K3.1 Pro"
        assert libelle_modele(ALIAS) == "Grand modèle texte (Synthetic)"
        export = await client.get("/api/data/export")
        assert export.status_code == 200, export.text
        preferences = {p["key"]: p["value"] for p in export.json()["preferences"]}
        assert preferences["llm_model"] == MODELE
        assert preferences["llm_provider"] == "synthetic"
        assert CLE_FICTIVE not in export.text

        demande = {"message": f"Cherche la facture {reference}.", "stream": True}
        autre = await client.post("/api/consents", json={
            "purpose": "documents", "provider": "openai", "granted": True, "text_version": "3",
        })
        assert autre.status_code == 200, autre.text
        refuse = await client.post("/api/chat/send", json=demande)
        assert not appels, refuse.text
        assert "accord" in refuse.text.lower()

        accord = await client.post("/api/consents", json={
            "purpose": "documents", "provider": "synthetic", "granted": True, "text_version": "3",
        })
        assert accord.status_code == 200, accord.text
        reponse = await client.post("/api/chat/send", json=demande)
        assert reponse.status_code == 200, reponse.text
        evenements = [
            json.loads(ligne.removeprefix("data: "))
            for ligne in reponse.text.splitlines() if ligne.startswith("data: ")
        ]
        assert len(appels) == 2, [(e["type"], e.get("content")) for e in evenements]
        assert any(e["type"] == "tool_result" and OUTIL in e["content"] for e in evenements)
        assert any(e["type"] == "text" and e["content"] == "Recherche Synthetic terminée." for e in evenements)


@pytest.mark.asyncio
async def test_synthetic_replie_son_catalogue_si_le_service_ne_repond_pas(client, monkeypatch):
    from app.routers import config as routes_config

    def indisponible(request):
        assert str(request.url) == f"{API}/models"
        return httpx.Response(503)

    async with httpx.AsyncClient(transport=httpx.MockTransport(indisponible)) as fournisseur:
        async def get_client():
            return fournisseur

        monkeypatch.setattr(routes_config, "get_http_client", get_client)
        liste = await client.get("/api/config/llm/models/synthetic")

    assert liste.status_code == 200
    assert liste.json()["models"][0] == ALIAS
    assert len([m for m in liste.json()["models"] if m.startswith("hf:")]) == 7


@pytest.mark.asyncio
@pytest.mark.parametrize(("base", "statut"), [(None, 200), ("https://api.synthetic.new/v1/", 404)])
async def test_synthetic_utilise_la_base_declaree_sans_essayer_un_autre_endpoint(base, statut):
    from app.services.providers.base import LLMConfig, LLMProvider
    from app.services.providers.synthetic import SyntheticProvider

    urls = []

    def fournir(request):
        urls.append(str(request.url))
        if str(request.url) == f"{API}/chat/completions":
            return httpx.Response(200, text=_flux_sse(
                {"choices": [{"delta": {"content": "Réponse de contrôle."}}]},
                {"choices": [{"delta": {}, "finish_reason": "stop"}]},
            ))
        return httpx.Response(404)

    async with httpx.AsyncClient(transport=httpx.MockTransport(fournir)) as client:
        config = LLMConfig(LLMProvider.SYNTHETIC, ALIAS, base_url=base)
        fournisseur = SyntheticProvider(config, client)
        flux = [e async for e in fournisseur.stream(None, [{"role": "user", "content": "Bonjour"}])]

    assert urls == [f"{(base or API).rstrip('/')}/chat/completions"]
    attendu = "text" if statut == 200 else "error"
    assert flux[0].type == attendu
