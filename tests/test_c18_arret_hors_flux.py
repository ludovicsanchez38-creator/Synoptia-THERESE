"""La voie directe annonce une réponse coupée ou un refus, comme le flux.

stream_response ne rendait que le texte. send_message enregistrait
alors la coupe comme une réponse ordinaire.
"""

from __future__ import annotations

import pytest
from app.services.llm import LLMService
from app.services.providers.base import LLMConfig, LLMProvider, StreamEvent


def _service(motif: str) -> LLMService:
    service = LLMService(LLMConfig(
        provider=LLMProvider.ANTHROPIC, model="claude-haiku-5-5", api_key="k",
    ))

    async def faux(context, tools=None, enable_grounding=True, config=None):
        yield StreamEvent(type="text", content="Debut.")
        yield StreamEvent(
            type="done", stop_reason=motif, input_tokens=8, output_tokens=3,
        )

    service.stream_response_with_tools = faux  # type: ignore[method-assign]
    return service


class TestArretHorsFlux:
    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ("motif", "annonce"),
        [
            ("max_tokens", "Réponse coupée"),
            ("incomplete", "Réponse coupée"),
            ("refusal", "Le modèle a refusé"),
        ],
    )
    async def test_le_motif_est_dans_la_reponse_et_l_historique(
        self, client, monkeypatch, motif: str, annonce: str,
    ):
        monkeypatch.setattr(
            "app.routers.chat.get_llm_service", lambda: _service(motif),
        )
        reponse = await client.post(
            "/api/chat/send",
            json={"message": "Bonjour", "stream": False, "disable_tools": True},
        )
        assert reponse.status_code == 200, reponse.text[:400]
        contenu = reponse.json()["content"]
        assert "Debut." in contenu
        assert annonce in contenu
        historique = await client.get(
            f"/api/chat/conversations/{reponse.json()['conversation_id']}/messages"
        )
        sauve = [
            m["content"] for m in historique.json() if m["role"] == "assistant"
        ]
        assert any(annonce in (c or "") for c in sauve), sauve

    @pytest.mark.asyncio
    async def test_une_fin_ordinaire_n_ajoute_rien(self, client, monkeypatch):
        monkeypatch.setattr(
            "app.routers.chat.get_llm_service", lambda: _service("end_turn"),
        )
        reponse = await client.post(
            "/api/chat/send",
            json={"message": "Bonjour", "stream": False, "disable_tools": True},
        )
        contenu = reponse.json()["content"]
        assert contenu == "Debut."
