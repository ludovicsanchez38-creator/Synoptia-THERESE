"""P-103 (acceptée par Ludo le 24/09/2026, B-966 différé du cycle 11) : le
routage des agents devinait le fournisseur d'après l'identifiant du modèle.
« qwen3.5 », « mistral-nemo » ou « equipe/assistant:free » installés dans
Ollama pouvaient partir chez un fournisseur en ligne homonyme, et, Ollama
absent, le prompt retombait sur le service principal, lui-même parfois en
ligne. Pour une application souveraine, un agent local ne quitte jamais la
machine sans le dire.

Décision : le fournisseur voyage avec le modèle (« ollama:<nom> » pour un
modèle local proposé par l'Atelier), et un modèle local indisponible est un
échec explicite, jamais un repli.
"""

from __future__ import annotations

import pytest
from app.routers import agents as routeur_agents
from app.services import llm as module_llm
from app.services.agents.runtime import _get_llm_for_model
from app.services.error_handler import ErreurPourEcran

PRINCIPAL = object()


@pytest.fixture
def fournisseurs(monkeypatch):
    demandes: list[tuple[str, str | None]] = []
    indisponibles: set[str] = set()
    principal: list[bool] = []

    def service(provider_name, model_override=None, effort_override=None,
                max_tokens_override=None, bascule_circuit=True):
        demandes.append((provider_name, model_override))
        return None if provider_name in indisponibles else ("service", provider_name, model_override)

    def service_principal(*_a, **_k):
        principal.append(True)
        return PRINCIPAL

    monkeypatch.setattr(module_llm, "get_llm_service_for_provider", service)
    monkeypatch.setattr(module_llm, "get_llm_service", service_principal)
    return demandes, indisponibles, principal


@pytest.mark.parametrize(
    ("modele", "nom_local"),
    [
        ("ollama:qwen3.5", "qwen3.5"),
        ("ollama:mistral-nemo", "mistral-nemo"),
        ("ollama:equipe/assistant:free", "equipe/assistant:free"),
        ("ollama:qwen3:32b", "qwen3:32b"),
    ],
)
def test_un_modele_marque_local_va_a_ollama_sans_rien_deviner(fournisseurs, modele, nom_local):
    demandes, _, principal = fournisseurs
    assert _get_llm_for_model(modele) == ("service", "ollama", nom_local)
    assert demandes == [("ollama", nom_local)]
    assert principal == []


@pytest.mark.parametrize(
    "modele",
    ["ollama:qwen3.5", "qwen3.5:9b", "hf.co/bartowski/Llama-3.2-1B-Instruct-GGUF:Q4_K_M"],
)
def test_un_modele_local_indisponible_echoue_sans_repli(fournisseurs, modele):
    demandes, indisponibles, principal = fournisseurs
    indisponibles.add("ollama")
    with pytest.raises(ErreurPourEcran) as info:
        _get_llm_for_model(modele)
    assert principal == [], "repli vers le service principal"
    assert [d for d, _ in demandes] == ["ollama"], demandes
    assert "en ligne" in str(info.value), str(info.value)


def test_un_modele_en_ligne_indisponible_garde_le_repli_principal(fournisseurs):
    _, indisponibles, principal = fournisseurs
    indisponibles.add("anthropic")
    assert _get_llm_for_model("claude-opus-5") is PRINCIPAL
    assert principal == [True]


@pytest.fixture
def ollama_installe(monkeypatch):
    for cle in ("ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GEMINI_API_KEY", "MISTRAL_API_KEY",
                "GROK_API_KEY", "OPENROUTER_API_KEY", "DEEPSEEK_API_KEY"):
        monkeypatch.delenv(cle, raising=False)
    monkeypatch.setattr("app.services.llm._get_api_key_from_db", lambda _f: None)
    monkeypatch.setattr("shutil.which", lambda _nom: "/usr/local/bin/ollama")

    async def installes() -> list[str]:
        return ["qwen3.5", "qwen3:8b"]

    monkeypatch.setattr(routeur_agents, "_modeles_ollama_installes", installes)


async def test_l_atelier_propose_les_modeles_locaux_avec_leur_fournisseur(client, ollama_installe):
    reponse = await client.get("/api/agents/config")
    assert reponse.status_code == 200
    locaux = [m for m in reponse.json()["available_models"] if m["provider"] == "ollama"]
    assert [m["id"] for m in locaux] == ["ollama:qwen3.5", "ollama:qwen3:8b"]


async def test_un_choix_local_ancien_sans_fournisseur_est_relu_avec_lui(client, ollama_installe):
    assert (await client.put("/api/agents/config", json={"katia_model": "qwen3.5"})).status_code == 200
    config = (await client.get("/api/agents/config")).json()
    assert config["katia_model"] == "ollama:qwen3.5"


async def test_l_echec_explicite_devient_un_evenement_d_erreur_de_l_agent(monkeypatch):
    """Revue c12 : `_service_local` lève ErreurPourEcran ; dans `runtime.run`,
    l'exception coupait le flux (essaim) ou partait au gestionnaire général
    avec une trace. Elle devient un AgentEvent d'erreur, message intact."""
    from app.services.agents.config import AgentConfig
    from app.services.agents.runtime import AgentRuntime

    monkeypatch.setattr(module_llm, "get_llm_service_for_provider", lambda *a, **k: None)
    config = AgentConfig(id="katia", name="Katia", description="Test", system_prompt="Tu aides.", default_model="ollama:qwen3.5")
    runtime = AgentRuntime(config, tool_executor=None, tools_schema=[], model_override="ollama:qwen3.5")
    evenements = [e async for e in runtime.run("Bonjour")]
    assert [e.type for e in evenements] == ["error"], evenements
    assert "en ligne" in evenements[0].content


async def test_un_ancien_choix_local_relu_est_enregistre_avec_son_fournisseur(client, db_session, monkeypatch):
    """B-1149 (audit de release 0.75) : le préfixe n'était ajouté que dans la
    RÉPONSE ; la préférence restait nue et l'essaim, qui la relit en base, la
    routait par devinette (« equipe/assistant:free » partait chez OpenRouter
    alors que l'Atelier l'affichait local)."""
    from app.models.entities import Preference
    from app.routers import agents as routeur_agents
    from app.services.agents.runtime import PREFIXE_MODELE_LOCAL
    from sqlmodel import select

    monkeypatch.setattr("shutil.which", lambda _nom: "/usr/local/bin/ollama")

    async def installes() -> list[str]:
        return ["equipe/assistant:free"]

    monkeypatch.setattr(routeur_agents, "_modeles_ollama_installes", installes)
    db_session.add(Preference(key="agent_katia_model", value="equipe/assistant:free"))
    await db_session.commit()

    config = (await client.get("/api/agents/config")).json()
    assert config["katia_model"] == f"{PREFIXE_MODELE_LOCAL}equipe/assistant:free"

    db_session.expire_all()
    enregistre = (
        await db_session.execute(select(Preference).where(Preference.key == "agent_katia_model"))
    ).scalar_one()
    assert enregistre.value == f"{PREFIXE_MODELE_LOCAL}equipe/assistant:free"
