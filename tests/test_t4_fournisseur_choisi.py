"""T4 : une clé absente ne change jamais le destinataire."""
from contextlib import contextmanager
from unittest.mock import MagicMock

import pytest

from app.services import llm
from app.services.error_handler import ErreurPourEcran


def preferences(monkeypatch, provider):
    @contextmanager
    def connection():
        conn = MagicMock()
        conn.execute.side_effect = lambda _q, params=None: MagicMock(
            fetchone=lambda: (provider,) if params and params['key'] == 'llm_provider' else None
        )
        yield conn
    monkeypatch.setattr('app.models.database.get_sync_connection', connection)
    monkeypatch.setattr(llm, '_get_api_key_from_db', lambda p: 'cle-factice' if p == 'anthropic' else None)
    monkeypatch.setattr(llm, '_cle_depuis_environnement', lambda p: None)
    monkeypatch.setattr(llm, 'detect_default_ollama_model', lambda: 'modele-local')


@pytest.mark.parametrize('provider', ['openai', 'gemini', 'mistral', 'openrouter'])
def test_cle_manquante_erreur_francaise_sans_repli(monkeypatch, provider):
    preferences(monkeypatch, provider)
    with pytest.raises(ErreurPourEcran, match=rf'{provider}.*Paramètres'):
        llm.LLMService().config


def test_ollama_sans_cle_reste_ollama(monkeypatch):
    preferences(monkeypatch, 'ollama')
    assert llm.LLMService().config.provider == llm.LLMProvider.OLLAMA


def test_absence_de_choix_ne_selectionne_pas_une_cle(monkeypatch):
    preferences(monkeypatch, None)
    assert llm.LLMService().config.provider == llm.LLMProvider.OLLAMA


def test_circuit_ouvert_ne_change_pas_le_destinataire(monkeypatch):
    config = llm.LLMConfig(llm.LLMProvider.OPENAI, 'modele', api_key='cle-factice')
    service = llm.LLMService(config)
    monkeypatch.setattr(llm, 'get_circuit_breaker', lambda: MagicMock(is_available=lambda p: p != 'openai'))
    monkeypatch.setattr(service, '_get_fallback_configs', lambda: [llm.LLMConfig(llm.LLMProvider.ANTHROPIC, 'autre')])
    assert service._resolve_with_circuit_breaker() is config
