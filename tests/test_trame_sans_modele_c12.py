"""B-1033 (ronde B4 du cycle 11, D-B4-7) : créer un document sans modèle
joignable renvoyait un 500 avec trace au journal, et l'écran conseillait de
« redémarrer l'application », conseil qui ne règle rien.

Le fournisseur rédige déjà sa panne pour l'écran (frontière 0.48 : « Impossible
de se connecter à Ollama… Vérifie qu'Ollama est lancé ») ; generate_content
la jetait dans un RuntimeError que message_pour_ecran remplaçait par le
générique. La panne d'un modèle n'est pas une erreur interne : 503, message
actionnable, pas de trace.
"""

import logging
from unittest.mock import patch

import pytest
from app.services.circuit_breaker import get_circuit_breaker
from app.services.error_handler import ErreurPourEcran, message_pour_ecran
from app.services.llm import LLMService
from app.services.providers.base import StreamEvent
from httpx import AsyncClient

PANNE_OLLAMA = (
    "Impossible de se connecter à Ollama (http://localhost:11434). "
    "Vérifie qu'Ollama est lancé (ouvre un terminal et tape 'ollama serve')."
)


def _flux_en_panne(*_args, **_kwargs):
    async def flux():
        yield StreamEvent(type="error", content=PANNE_OLLAMA)

    return flux()


@pytest.fixture(autouse=True)
def _disjoncteur_propre():
    get_circuit_breaker().reset()
    yield
    get_circuit_breaker().reset()


@pytest.mark.asyncio
async def test_generate_content_porte_la_panne_du_fournisseur_jusqu_a_l_ecran():
    service = LLMService.__new__(LLMService)
    with (
        patch.object(LLMService, "stream_response_with_tools", _flux_en_panne),
        patch.object(LLMService, "_resolve_with_circuit_breaker", lambda self: self.config),
        patch.object(LLMService, "_get_system_prompt_with_identity", lambda self: "système"),
        patch.object(LLMService, "prepare_context", lambda self, **kw: {}),
    ):
        service.config = type(
            "Cfg", (), {"provider": type("P", (), {"value": "ollama"})(), "max_tokens": 1000}
        )()
        with pytest.raises(RuntimeError) as info:
            await service.generate_content(prompt="Trame")
    assert isinstance(info.value, ErreurPourEcran)
    ecran = message_pour_ecran(info.value)
    assert "Ollama" in ecran
    assert "redémarre" not in ecran


@pytest.mark.asyncio
async def test_trame_sans_modele_joignable_503_actionnable_sans_trace(client: AsyncClient, caplog):
    reponse = await client.post("/api/documents", json={"title": "Proposition", "brief": "Brief"})
    assert reponse.status_code == 200, reponse.text
    document_id = reponse.json()["id"]

    caplog.set_level(logging.INFO)
    with patch.object(LLMService, "stream_response_with_tools", _flux_en_panne):
        reponse = await client.post(f"/api/documents/{document_id}/outline")

    assert reponse.status_code == 503, reponse.text
    message = reponse.json()["message"]
    assert "Ollama" in message
    assert "trame" in message.lower()
    assert "redémarre" not in message
    traces = [
        r for r in caplog.records if r.name.startswith("app.routers.documents") and r.exc_info
    ]
    assert traces == [], [r.getMessage() for r in traces]

    detail = await client.get(f"/api/documents/{document_id}")
    assert detail.json()["sections"] == []
