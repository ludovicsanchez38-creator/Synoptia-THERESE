"""Un accord ancien pour un autre fournisseur n'autorise aucun repli."""
from unittest.mock import AsyncMock, MagicMock

import pytest
from app.services import llm
from app.services.agents.runtime import _get_llm_for_model
from app.services.consentements import enregistrer_accord
from app.services.error_handler import ErreurPourEcran


@pytest.mark.parametrize('chemin,modele,fournisseur', [
    ('catalogue', 'modele-catalogue', 'anthropic'),
    ('prefixe', 'claude-test', 'anthropic'),
    ('openrouter', 'equipe/modele:free', 'openrouter'),
    ('inconnu', 'modele-inconnu', None),
])
async def test_agent_sans_repli_meme_avec_accord_du_principal(client, monkeypatch, chemin, modele, fournisseur):
    enregistrer_accord('llm', 'openai', True, '3', [])
    principal = MagicMock()
    monkeypatch.setattr(llm, 'get_llm_service', principal)
    monkeypatch.setattr(llm, 'get_llm_service_for_provider', lambda *a, **k: None)
    monkeypatch.setattr('app.services.agents.runtime._fournisseur_du_catalogue',
                        lambda _: fournisseur if chemin == 'catalogue' else None)
    with pytest.raises(ErreurPourEcran, match=fournisseur or 'modèle'):
        _get_llm_for_model(modele)
    principal.assert_not_called()


@pytest.mark.parametrize('circuit_ouvert', [False, True])
async def test_board_refuse_avant_tout_envoi_si_conseiller_indisponible(client, monkeypatch, circuit_ouvert):
    from app.models.board import AdvisorRole, BoardRequest
    from app.services import board

    enregistrer_accord('llm', 'board', True, '3', [])
    enregistrer_accord('llm', 'openai', True, '3', [])
    role = next(iter(AdvisorRole))
    monkeypatch.setitem(board.ADVISOR_CONFIG[role], 'preferred_provider', 'anthropic')
    monkeypatch.setattr(board, 'get_llm_service', MagicMock())
    monkeypatch.setattr(board, 'get_llm_service_for_provider', lambda *a, **k: None)
    monkeypatch.setattr('app.services.circuit_breaker.get_circuit_breaker',
                        lambda: MagicMock(is_available=lambda _: not circuit_ouvert))
    service = board.BoardService()
    recherche = AsyncMock(return_value='')
    monkeypatch.setattr(service, '_search_web_for_context', recherche)
    with pytest.raises(ErreurPourEcran, match='anthropic'):
        _ = [e async for e in service.deliberate(BoardRequest(question='Choisir une stratégie', advisors=[role]))]
    recherche.assert_not_called()


async def test_profil_agent_ne_remplace_pas_le_fournisseur_indisponible(client, monkeypatch):
    def indisponible():
        raise ErreurPourEcran('Le fournisseur openai est indisponible. Vérifie sa clé dans Paramètres, Modèles IA.')

    monkeypatch.setattr(llm, 'get_llm_service', indisponible)
    response = await client.get('/api/agents/profiles')
    assert response.status_code >= 400, 'Un modèle Anthropic est proposé à la place du fournisseur choisi'
    assert 'openai' in response.text


@pytest.mark.parametrize('provider,modele', [('ollama', 'qwen3.5'), ('openrouter', 'claude-test')])
async def test_profil_conserve_la_destination_du_service_principal(client, monkeypatch, provider, modele):
    from types import SimpleNamespace

    service = SimpleNamespace(config=SimpleNamespace(provider=SimpleNamespace(value=provider), model=modele))
    monkeypatch.setattr(llm, 'get_llm_service', lambda: service)
    response = await client.get('/api/agents/profiles')
    assert response.status_code == 200
    model_id = response.json()[0]['default_model']
    demandes = []

    def fourni(provider_name, model_override=None, **kwargs):
        demandes.append((provider_name, model_override))
        return service

    monkeypatch.setattr(llm, 'get_llm_service_for_provider', fourni)
    assert _get_llm_for_model(model_id) is service
    assert demandes == [(provider, modele)]


def test_preferences_illisibles_ne_choisissent_pas_ollama(monkeypatch):
    def indisponible():
        raise RuntimeError('Base indisponible')

    monkeypatch.setattr('app.models.database.get_sync_connection', indisponible)
    detecter = MagicMock(return_value='modele-local')
    monkeypatch.setattr(llm, 'detect_default_ollama_model', detecter)
    with pytest.raises(ErreurPourEcran, match='fournisseur'):
        llm.LLMService()
    detecter.assert_not_called()
