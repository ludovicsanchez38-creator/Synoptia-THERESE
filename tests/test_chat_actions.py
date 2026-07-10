"""
Actions déterministes du chat - tranche 1a (design 2026-07-10, validé Ludo).

Un message composé UNIQUEMENT de `{action: ...}` est exécuté localement, sans
AUCUN appel au LLM (racine de BUG-130/133 : le modèle ne doit pas être le seul
décideur de l'exécution). Tranche 1a : navigation (`ouvrir <vue>`). Action
inconnue ou malformée -> réponse locale listant les actions, jamais transmise
au LLM. Un message ordinaire (ou une action au milieu d'un texte) suit le flux
LLM habituel, strictement inchangé.
"""
import json
from unittest.mock import patch

import pytest
from httpx import AsyncClient


class TestParseActionMessage:
    """Parser pur : message-action ou pas, allowlist, malformés."""

    def _parse(self, text):
        from app.services.chat_actions import parse_action_message

        return parse_action_message(text)

    def test_navigation_valide(self):
        parsed = self._parse("{action: ouvrir email}")
        assert parsed is not None
        assert parsed.kind == "navigate"
        assert parsed.action_id == "email.open"

    def test_tolerant_casse_espaces_accents(self):
        parsed = self._parse("  {Action:  Ouvrir  Mémoire }  ")
        assert parsed is not None
        assert parsed.kind == "navigate"
        assert parsed.action_id == "memory.open"

    def test_texte_mixte_pas_un_message_action(self):
        # L'action au milieu d'un texte = flux LLM normal (tranche 1 :
        # message-action PUR uniquement, décision revue Codex).
        assert self._parse("Peux-tu {action: ouvrir email} pour moi ?") is None

    def test_message_normal(self):
        assert self._parse("Bonjour, comment vas-tu ?") is None

    def test_double_accolades_syntaxe_skill_preservee(self):
        # {{action: skill_id}} est la syntaxe de forçage de skill EXISTANTE
        # (intent_detector) : elle ne doit PAS être capturée par le parser.
        assert self._parse("{{action: docx-pro}}") is None

    def test_action_execute_generique_refusee(self):
        parsed = self._parse("{action: execute}")
        assert parsed is not None
        assert parsed.kind == "unknown"

    def test_cible_inconnue(self):
        parsed = self._parse("{action: ouvrir nimportequoi}")
        assert parsed is not None
        assert parsed.kind == "unknown"

    def test_malforme(self):
        parsed = self._parse("{action: }")
        assert parsed is not None
        assert parsed.kind == "unknown"


def _no_llm():
    """get_llm_service patché : tout appel = échec du test (zéro LLM)."""
    raise AssertionError("Le LLM ne doit JAMAIS être appelé pour un message-action")


class TestActionEndpoint:
    """Intégration /api/chat/send : exécution locale, zéro provider."""

    @pytest.mark.asyncio
    async def test_navigation_non_stream_sans_llm(self, client: AsyncClient):
        with patch("app.routers.chat.get_llm_service", side_effect=_no_llm):
            response = await client.post(
                "/api/chat/send",
                json={"message": "{action: ouvrir email}", "stream": False},
            )
        assert response.status_code == 200
        data = response.json()
        assert data["client_action"] == {
            "action": "navigate",
            "action_id": "email.open",
            "target": "email",
        }
        assert "email" in data["content"].lower()

    @pytest.mark.asyncio
    async def test_navigation_stream_client_action_avant_done(self, client: AsyncClient):
        with patch("app.routers.chat.get_llm_service", side_effect=_no_llm):
            response = await client.post(
                "/api/chat/send",
                json={"message": "{action: ouvrir crm}", "stream": True},
            )
        assert response.status_code == 200
        events = []
        for block in response.text.split("\n\n"):
            block = block.strip()
            if block.startswith("data: "):
                events.append(json.loads(block[len("data: "):]))
        types = [e["type"] for e in events]
        assert "client_action" in types
        assert types.index("client_action") < types.index("done")
        ca = next(e for e in events if e["type"] == "client_action")
        assert ca["client_action"]["action_id"] == "crm.open"

    @pytest.mark.asyncio
    async def test_action_inconnue_reponse_locale_liste(self, client: AsyncClient):
        with patch("app.routers.chat.get_llm_service", side_effect=_no_llm):
            response = await client.post(
                "/api/chat/send",
                json={"message": "{action: execute}", "stream": False},
            )
        assert response.status_code == 200
        data = response.json()
        assert data.get("client_action") is None
        # La réponse liste les actions disponibles (dont « ouvrir email »).
        assert "ouvrir email" in data["content"]

    @pytest.mark.asyncio
    async def test_message_action_persiste_en_conversation(self, client: AsyncClient):
        with patch("app.routers.chat.get_llm_service", side_effect=_no_llm):
            response = await client.post(
                "/api/chat/send",
                json={"message": "{action: ouvrir calendrier}", "stream": False},
            )
        assert response.status_code == 200
        conv_id = response.json()["conversation_id"]
        messages = await client.get(f"/api/chat/conversations/{conv_id}/messages")
        assert messages.status_code == 200
        contents = [m["content"] for m in messages.json()]
        assert "{action: ouvrir calendrier}" in contents  # message utilisateur
        assert any("calendrier" in c.lower() for c in contents[1:] or contents)

    @pytest.mark.asyncio
    async def test_non_regression_slash_contact(self, client: AsyncClient, db_session):
        """Le court-circuit /contact existant reste intact."""
        with patch("app.routers.chat.get_llm_service", side_effect=_no_llm):
            response = await client.post(
                "/api/chat/send",
                json={"message": "/contact Jean Actiontest email=ja@test.fr", "stream": False},
            )
        assert response.status_code == 200
        assert "Jean Actiontest" in response.json()["content"]
