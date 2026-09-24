"""B-1092 (cycle 12, réparé au cycle 13) : une panne du fournisseur est
comptée une seule fois par le disjoncteur.

`generate_content` consomme `stream_response_with_tools`, qui compte déjà
les pannes (erreurs 429 et 5xx, exceptions). `generate_content` les
recomptait : un seul « API error: 529 » faisait deux échecs, et avec un
seuil de 2 il ouvrait à lui seul le disjoncteur (lecteur D de la carte c13).
"""

import pytest
from app.services.circuit_breaker import get_circuit_breaker
from app.services.error_handler import ErreurDuModele
from app.services.llm import LLMConfig, LLMProvider, LLMService
from app.services.providers.base import StreamEvent


class _Fournisseur:
    def __init__(self, evenements=None, exception=None):
        self.evenements = evenements or []
        self.exception = exception

    async def stream(self, system_prompt, messages, tools=None, enable_grounding=True):
        if self.exception:
            raise self.exception
        for evenement in self.evenements:
            yield evenement


def _service(monkeypatch, fournisseur) -> LLMService:
    service = LLMService(LLMConfig(LLMProvider.ANTHROPIC, "claude-test", api_key="k", max_tokens=1024))

    async def _pret():
        service._provider = fournisseur

    monkeypatch.setattr(service, "_ensure_provider", _pret)
    return service


@pytest.fixture(autouse=True)
def _disjoncteur_neuf():
    get_circuit_breaker().reset()
    yield
    get_circuit_breaker().reset()


def _echecs() -> int:
    return get_circuit_breaker()._get_circuit("anthropic").consecutive_failures


@pytest.mark.asyncio
async def test_une_erreur_529_compte_un_seul_echec(monkeypatch):
    service = _service(monkeypatch, _Fournisseur([StreamEvent(type="error", content="API error: 529")]))
    with pytest.raises(ErreurDuModele):
        await service.generate_content("Bonjour")
    assert _echecs() == 1


@pytest.mark.asyncio
async def test_une_exception_du_fournisseur_compte_un_seul_echec(monkeypatch):
    service = _service(monkeypatch, _Fournisseur(exception=ConnectionError("coupure")))
    with pytest.raises(ConnectionError):
        await service.generate_content("Bonjour")
    assert _echecs() == 1
