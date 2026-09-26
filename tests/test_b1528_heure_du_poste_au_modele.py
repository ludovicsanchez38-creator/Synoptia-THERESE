"""B-1528 (moitié « heure donnée au modèle ») : le prompt système donnait
l'heure courante en UTC. À Paris, à 3 h 45, le modèle lisait « 01:45 UTC » :
« dans une heure » devenait un rendez-vous à 2 h 45, rangé comme heure de
Paris, et entre minuit et 2 h la date du jour était celle de la veille.
Le modèle reçoit désormais l'heure du poste avec son décalage.
"""

import os
import sys
import time

import pytest


@pytest.mark.skipif(sys.platform == "win32", reason="time.tzset n'existe pas sous Windows")
def test_le_modele_recoit_l_heure_du_poste(monkeypatch):
    from datetime import datetime

    from app.services.llm import LLMConfig, LLMProvider, LLMService

    ancien = os.environ.get("TZ")
    monkeypatch.setenv("TZ", "America/Martinique")
    time.tzset()
    try:
        service = LLMService(LLMConfig(provider=LLMProvider.OLLAMA, model="qwen3:8b", api_key=None))
        prompt = service._get_system_prompt_with_identity()
        locale = datetime.now().astimezone()
        assert f"{locale.strftime('%H')}:" in prompt or locale.strftime("%H:%M") in prompt
        assert "UTC-04:00" in prompt
        assert " UTC\n" not in prompt and not prompt.rstrip().endswith("UTC")
    finally:
        if ancien is None:
            monkeypatch.delenv("TZ", raising=False)
        else:
            monkeypatch.setenv("TZ", ancien)
        time.tzset()
