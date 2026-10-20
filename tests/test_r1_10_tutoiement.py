"""R1-10 : le registre par défaut est posé avec ou sans profil."""
import pytest
from app.services.llm import LLMService
from app.services.providers.base import LLMConfig, LLMProvider
from app.services.user_profile import UserProfile


@pytest.mark.parametrize('profil', [None, UserProfile(name='Marie', context='Rédige mes courriers en vouvoiement.')])
def test_tutoiement_par_defaut_et_consigne_personnelle_conservee(monkeypatch, profil):
    from app.services import llm, user_profile
    monkeypatch.setattr(user_profile, 'get_cached_profile', lambda: profil)
    monkeypatch.setattr(llm, 'load_therese_md', lambda: '')
    service = LLMService(LLMConfig(LLMProvider.OLLAMA, 'factice'))
    prompt = service._get_system_prompt_with_identity()
    assert 'Tutoie' in prompt
    assert 'sauf demande explicite' in prompt
    if profil:
        assert 'Rédige mes courriers en vouvoiement.' in prompt
