"""B-330 (05/09/2026) : un Ollama configuré ailleurs recevait la détection
de modèle (B-268) mais pas les requêtes.

Quatre constructions de LLMConfig gardaient `http://localhost:11434` en dur
(config Ollama choisie, repli sans clé, repli du circuit breaker, routage des
agents). Avec OLLAMA_BASE_URL=http://127.0.0.1:9, `settings.ollama_base_url`
disait 127.0.0.1:9 et les quatre partaient sur localhost:11434.
"""

from __future__ import annotations

import inspect


def test_aucune_adresse_ollama_en_dur_dans_le_service_llm():
    from app.services import llm

    source = inspect.getsource(llm)
    assert 'base_url="http://localhost:11434"' not in source
    assert 'base_url = "http://localhost:11434"' not in source
