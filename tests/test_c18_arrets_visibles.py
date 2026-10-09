"""Une réponse coupée ou un refus arrive jusqu'au texte affiché.

OpenAI ``response.incomplete``, Anthropic ``max_tokens`` et
``model_context_window_exceeded``, et le refus Anthropic ``refusal``
ne sont pas une fin ordinaire. Le flux et l'historique le disent.
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

import pytest
from app.services.context import ContextWindow
from app.services.providers.base import LLMProvider, StreamEvent


def _evenements(texte: str) -> list[dict]:
    return [
        json.loads(ligne.removeprefix("data: "))
        for ligne in texte.splitlines()
        if ligne.startswith("data: ")
    ]


def _texte_affiche(texte: str) -> str:
    return "".join(
        evenement.get("content") or ""
        for evenement in _evenements(texte)
        if evenement.get("type") == "text"
    )


class _Service:
    def __init__(self, motif: str, texte: str = "Voici le début.") -> None:
        self.motif = motif
        self.texte = texte

        class _Config:
            model = "claude-haiku-5-5"
            provider = LLMProvider.ANTHROPIC

        self.config = _Config()

    def prepare_context(self, messages, memory_context=None):
        return ContextWindow(
            messages=list(messages),
            system_prompt="",
            max_tokens=10_000_000,
        )

    async def stream_response_with_tools(self, context, tools=None):
        if self.texte:
            yield StreamEvent(type="text", content=self.texte)
        yield StreamEvent(
            type="done",
            stop_reason=self.motif,
            input_tokens=12,
            output_tokens=4,
        )


class TestArretVisible:
    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ("motif", "annonce"),
        [
            ("incomplete", "Réponse coupée"),
            ("max_tokens", "Réponse coupée"),
            ("model_context_window_exceeded", "Réponse coupée"),
            ("refusal", "Le modèle a refusé"),
        ],
    )
    async def test_le_motif_est_dans_le_flux_et_dans_l_historique(
        self, client, monkeypatch, motif, annonce,
    ):
        monkeypatch.setattr(
            "app.routers.chat.get_llm_service", lambda: _Service(motif),
        )
        reponse = await client.post(
            "/api/chat/send",
            json={"message": "Bonjour", "stream": True, "disable_tools": True},
        )
        assert reponse.status_code == 200, reponse.text[:300]
        affiche = _texte_affiche(reponse.text)
        assert "Voici le début." in affiche
        assert annonce in affiche
        if motif == "refusal":
            assert "Réponse coupée" not in affiche
        else:
            assert "Le modèle a refusé" not in affiche
        conversation = next(
            e["conversation_id"]
            for e in _evenements(reponse.text)
            if e.get("conversation_id")
        )
        historique = await client.get(
            f"/api/chat/conversations/{conversation}/messages"
        )
        contenus = [m["content"] for m in historique.json() if m["role"] == "assistant"]
        assert any(annonce in (c or "") for c in contenus), contenus

    @pytest.mark.asyncio
    async def test_une_fin_normale_n_ajoute_pas_l_annonce(self, client, monkeypatch):
        monkeypatch.setattr(
            "app.routers.chat.get_llm_service", lambda: _Service("end_turn"),
        )
        reponse = await client.post(
            "/api/chat/send",
            json={"message": "Bonjour", "stream": True, "disable_tools": True},
        )
        affiche = _texte_affiche(reponse.text)
        assert affiche == "Voici le début."

    @pytest.mark.asyncio
    async def test_un_tour_d_outil_incomplet_reste_visible(self, client, monkeypatch):
        from app.services.llm import ToolCall

        class _AvecOutil(_Service):
            def __init__(self) -> None:
                super().__init__("incomplete", "")

            async def stream_response_with_tools(self, context, tools=None):
                yield StreamEvent(
                    type="tool_call",
                    tool_call=ToolCall(
                        id="c1", name="search_emails", arguments={"query": "a"},
                    ),
                )
                yield StreamEvent(
                    type="done",
                    stop_reason="tool_use",
                    input_tokens=20,
                    output_tokens=5,
                )

            async def continue_with_tool_results(self, *args, **kwargs):
                yield StreamEvent(type="text", content="J'ai trouvé deux fils.")
                yield StreamEvent(
                    type="done",
                    stop_reason="incomplete",
                    input_tokens=30,
                    output_tokens=8,
                )

        monkeypatch.setattr(
            "app.routers.chat.get_llm_service", lambda: _AvecOutil(),
        )
        with patch(
            "app.routers.chat.execute_workspace_tool",
            AsyncMock(return_value="rien"),
        ):
            reponse = await client.post(
                "/api/chat/send", json={"message": "Bonjour", "stream": True},
            )
        affiche = _texte_affiche(reponse.text)
        assert "J'ai trouvé deux fils." in affiche
        assert "Réponse coupée" in affiche
        conversation = next(
            e["conversation_id"]
            for e in _evenements(reponse.text)
            if e.get("conversation_id")
        )
        historique = await client.get(
            f"/api/chat/conversations/{conversation}/messages"
        )
        contenus = [m["content"] for m in historique.json() if m["role"] == "assistant"]
        assert any("Réponse coupée" in (c or "") for c in contenus), contenus


def _sse(evenement: dict) -> str:
    return f"data: {json.dumps(evenement)}"


class TestFluxAnthropicSynthetique:
    """Le fournisseur garde le motif. Le chat, lui, doit le rendre visible."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "motif",
        ["refusal", "max_tokens", "model_context_window_exceeded"],
    )
    async def test_le_motif_survit_au_flux(self, motif):
        from app.services.providers.anthropic import AnthropicProvider
        from app.services.providers.base import LLMConfig

        from tests.test_provider_tools import _collect, _FakeClient

        lignes = [
            _sse({"type": "message_start", "message": {"usage": {"input_tokens": 8}}}),
            _sse({
                "type": "content_block_start",
                "index": 0,
                "content_block": {"type": "text", "text": ""},
            }),
            _sse({
                "type": "content_block_delta",
                "index": 0,
                "delta": {"type": "text_delta", "text": "Début"},
            }),
            _sse({"type": "content_block_stop", "index": 0}),
            _sse({
                "type": "message_delta",
                "delta": {"stop_reason": motif},
                "usage": {"output_tokens": 3},
            }),
            _sse({"type": "message_stop"}),
        ]
        fournisseur = AnthropicProvider(
            LLMConfig(provider=LLMProvider.ANTHROPIC, model="claude-haiku-5-5", api_key="k"),
            client=_FakeClient(lignes),
        )
        evenements = await _collect(
            fournisseur.stream("system", [{"role": "user", "content": "Bonjour"}], None)
        )
        finis = [e for e in evenements if e.type == "done"]
        assert len(finis) == 1
        assert finis[0].stop_reason == motif
