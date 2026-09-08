"""
B-649 (persona Nadia, cycle 4) : l'onglet Agents de l'Atelier proposait cinq
modèles locaux figés (qwen3.5:9b présélectionné, qwen3-coder:30b, …) alors
qu'Ollama ne servait que gemma4-tia et qwen3:8b. Les modèles locaux proposés
par GET /api/agents/config sont ceux réellement installés.
"""
import pytest
from app.routers import agents as routeur_agents

CLES_CLOUD = (
    "ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GEMINI_API_KEY", "MISTRAL_API_KEY",
    "GROK_API_KEY", "OPENROUTER_API_KEY", "DEEPSEEK_API_KEY",
)


@pytest.fixture
def ollama_avec_deux_modeles(monkeypatch):
    for cle in CLES_CLOUD:
        monkeypatch.delenv(cle, raising=False)
    monkeypatch.setattr("app.services.llm._get_api_key_from_db", lambda _fournisseur: None)
    monkeypatch.setattr("shutil.which", lambda _nom: "/usr/local/bin/ollama")

    async def installes() -> list[str]:
        return ["gemma4-tia:latest", "qwen3:8b"]

    monkeypatch.setattr(routeur_agents, "_modeles_ollama_installes", installes)


async def test_les_modeles_locaux_proposes_sont_ceux_installes(client, ollama_avec_deux_modeles):
    resp = await client.get("/api/agents/config")
    assert resp.status_code == 200
    modeles = resp.json()["available_models"]
    locaux = [m for m in modeles if m["provider"] == "ollama"]
    assert [m["id"] for m in locaux] == ["gemma4-tia:latest", "qwen3:8b"]
    assert all(m["id"] != "qwen3.5:9b" for m in modeles)
    assert all("local" in m["name"] for m in locaux)


async def test_sans_ollama_aucun_modele_local_fantome(client, monkeypatch):
    for cle in CLES_CLOUD:
        monkeypatch.delenv(cle, raising=False)
    monkeypatch.setattr("app.services.llm._get_api_key_from_db", lambda _fournisseur: None)
    monkeypatch.setattr("shutil.which", lambda _nom: None)

    async def rien() -> list[str]:
        return []

    monkeypatch.setattr(routeur_agents, "_modeles_ollama_installes", rien)
    resp = await client.get("/api/agents/config")
    assert resp.status_code == 200
    assert [m for m in resp.json()["available_models"] if m["provider"] == "ollama"] == []
