"""B-1146 (audit de release 0.75, agent sécurité) : Ollama liste ses modèles
Cloud (« gpt-oss:120b-cloud », « kimi-k2.6:cloud ») parmi les modèles
installés, mais leur traitement a lieu sur ollama.com. THÉRÈSE les présentait
« (local, installé) » et sa consigne système les disait sans fournisseur tiers.
"""
import pytest
from app.routers import agents as routeur_agents
from app.services.ollama_capabilites import est_modele_ollama_cloud


@pytest.mark.parametrize(
    ("nom", "attendu"),
    [
        ("gpt-oss:120b-cloud", True),
        ("kimi-k2.6:cloud", True),
        ("Qwen3-Coder:480B-CLOUD", True),
        ("qwen3:8b", False),
        ("gemma4-tia:latest", False),
        ("cloudy-model:7b", False),
    ],
)
def test_reconnaitre_un_modele_ollama_cloud(nom: str, attendu: bool):
    assert est_modele_ollama_cloud(nom) is attendu


async def test_les_agents_ne_presentent_pas_un_modele_cloud_comme_local(client, monkeypatch):
    for cle in ("ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GEMINI_API_KEY", "MISTRAL_API_KEY", "GROK_API_KEY", "OPENROUTER_API_KEY", "DEEPSEEK_API_KEY"):
        monkeypatch.delenv(cle, raising=False)
    monkeypatch.setattr("app.services.llm._get_api_key_from_db", lambda _fournisseur: None)
    monkeypatch.setattr("shutil.which", lambda _nom: "/usr/local/bin/ollama")

    async def installes() -> list[str]:
        return ["qwen3:8b", "gpt-oss:120b-cloud"]

    monkeypatch.setattr(routeur_agents, "_modeles_ollama_installes", installes)
    resp = await client.get("/api/agents/config")
    assert resp.status_code == 200
    noms = {m["id"]: m["name"] for m in resp.json()["available_models"] if m["provider"] == "ollama"}
    assert "local" in noms["ollama:qwen3:8b"]
    assert "local" not in noms["ollama:gpt-oss:120b-cloud"]
    assert "en ligne" in noms["ollama:gpt-oss:120b-cloud"]


def test_la_consigne_systeme_ne_dit_pas_local_un_modele_ollama_cloud():
    from app.services.llm import LLMService

    assert "Ollama Cloud" in LLMService.SOVEREIGNTY_BLOCK
