"""B-968 et B-969 (cycle 11, 23/09/2026) : relevés du lecteur de carte n°10.

B-968 (sécurité, haut) : un agent sur modèle local recevait un service Ollama
avec bascule_circuit=True. Après deux échecs d'Ollama, le disjoncteur basculait
en silence vers un fournisseur cloud configuré : le prompt de l'agent quittait
la machine. Le Board passe déjà bascule_circuit=False ; les agents locaux aussi.

B-969 (sécurité) : search_codebase n'excluait que .git, .venv et node_modules.
Un `.env.yaml` passait le filtre *.yaml et ses clés d'API étaient rendues au
modèle, alors que read_file refuse ces fichiers.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from app.services import llm as module_llm
from app.services.agents.runtime import _get_llm_for_model
from app.services.agents.tools import AgentToolExecutor


@pytest.fixture
def appels(monkeypatch):
    vus: list[tuple[str, dict]] = []

    # Même signature que la vraie fonction (revue R-2 : pas de **kwargs).
    def service(provider_name, model_override=None, effort_override=None,
                max_tokens_override=None, bascule_circuit=True):
        kwargs = {"model_override": model_override}
        if bascule_circuit is not True:
            kwargs["bascule_circuit"] = bascule_circuit
        vus.append((provider_name, kwargs))
        return ("service", provider_name)

    monkeypatch.setattr(module_llm, "get_llm_service_for_provider", service)
    monkeypatch.setattr(module_llm, "get_llm_service", lambda *a, **k: "principal")
    return vus


@pytest.mark.parametrize("modele", ["qwen3.5:9b", "hf.co/bartowski/Llama-3.2-1B-Instruct-GGUF:Q4_K_M", "mon-modele:latest"])
def test_b968_un_agent_local_ne_bascule_jamais_vers_le_cloud(appels, modele):
    assert _get_llm_for_model(modele) == ("service", "ollama")
    fournisseur, options = appels[-1]
    assert fournisseur == "ollama"
    assert options.get("bascule_circuit") is False, options


@pytest.mark.parametrize("modele", ["claude-opus-5", "anthropic/claude-opus-5", "codestral-2508"])
def test_b968_un_agent_cloud_garde_la_bascule_par_defaut(appels, modele):
    _get_llm_for_model(modele)
    _, options = appels[-1]
    assert options.get("bascule_circuit", True) is True, options


@pytest.mark.skipif(shutil.which("grep") is None, reason="grep requis")
@pytest.mark.parametrize(
    ("chemin", "filtre"),
    [
        (".env.yaml", "*.yaml"),
        ("config/.env.local.json", "*.json"),
        (".env.py", "*.py"),
        # Dixième revue Codex (R-1) : read_file compare en minuscules.
        (".ENV.yaml", "*.yaml"),
        (".Env.py", "*.py"),
    ],
)
async def test_b969_la_recherche_ne_lit_pas_un_fichier_sensible(tmp_path: Path, chemin: str, filtre: str):
    sensible = tmp_path / chemin
    sensible.parent.mkdir(parents=True, exist_ok=True)
    sensible.write_text("OPENAI_API_KEY=sk-temoin-c11\n", encoding="utf-8")
    ordinaire = tmp_path / ("ordinaire" + filtre[1:])
    ordinaire.write_text("OPENAI_API_KEY=lue-dans-un-fichier-ordinaire\n", encoding="utf-8")
    sortie = await AgentToolExecutor(str(tmp_path)).search_codebase("OPENAI_API_KEY", filtre)
    assert "sk-temoin-c11" not in sortie, sortie
    assert "lue-dans-un-fichier-ordinaire" in sortie, sortie
