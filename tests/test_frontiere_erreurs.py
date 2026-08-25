"""Frontière d'erreurs utilisateur (lot C, 0.48).

PAS un second système : error_handler.py existant, étendu. À la limite de
l'écran (SSE, notification, HTTP, task.error), seuls les messages
localisés passent - jamais str(e) brut. Le technique va aux logs.
"""

import pytest


class TestLeMessagePourEcran:
    def test_therese_error_passe_son_message_utilisateur(self):
        from app.services.error_handler import (
            ErrorCode,
            TheresError,
            message_pour_ecran,
        )

        exc = TheresError(
            ErrorCode.API_AUTH_FAILED,
            "401 unauthorized sk-xxx",
            context={"provider": "OpenAI"},
        )
        assert message_pour_ecran(exc) == exc.user_message
        assert "sk-xxx" not in message_pour_ecran(exc)

    def test_une_exception_brute_devient_generique(self):
        from app.services.error_handler import message_pour_ecran

        msg = message_pour_ecran(KeyError("colonne_interne_42"))
        assert "colonne_interne_42" not in msg
        assert "KeyError" not in msg
        # Un message français lisible, pas une chaîne vide
        assert len(msg) > 20

    def test_le_cas_inconnu_ne_reinjecte_plus_le_technique(self):
        """Le template UNKNOWN_ERROR affichait « Détails techniques: {error} »."""
        from app.services.error_handler import ErrorCode, TheresError

        exc = TheresError(ErrorCode.UNKNOWN_ERROR, "KeyError('secret_interne')")
        assert "secret_interne" not in exc.user_message
        assert "KeyError" not in exc.user_message

    def test_le_contexte_lisible_precede_le_generique(self):
        from app.services.error_handler import message_pour_ecran

        msg = message_pour_ecran(RuntimeError("boom"), ou="pendant la délibération")
        assert "pendant la délibération" in msg
        assert "boom" not in msg


class TestLesEmetteursNExposentPlusLeBrut:
    """Verrouillage : les sites listés au design n'émettent plus str(e)."""

    def test_board_sse_sans_str_e(self):
        import inspect

        from app.routers import board as board_router

        source = inspect.getsource(board_router)
        assert '"content": str(' not in source, (
            "un chunk SSE du board émet encore str(e) brut vers l'écran"
        )

    def test_runtime_agent_event_sans_exception_brute(self):
        import inspect

        from app.services.agents import runtime

        source = inspect.getsource(runtime)
        assert 'content=f"Erreur LLM : {e}"' not in source

    def test_action_agents_task_error_sans_exception_brute(self):
        import inspect

        from app.services import action_agents

        source = inspect.getsource(action_agents)
        assert 'task.error = f"Erreur LLM : {e}"' not in source


class TestLaRouteImages:
    def test_cle_manquante_reste_un_message_intentionnel(self, client, monkeypatch):
        """Les messages écrits POUR l'utilisateur (clé API manquante)
        traversent la frontière tels quels - via TheresError."""
        for var in ("OPENAI_IMAGE_API_KEY", "OPENAI_API_KEY"):
            monkeypatch.delenv(var, raising=False)
        reponse = client.post(
            "/api/images/generate",
            json={"prompt": "un chat", "provider": "gpt-image-2"},
        )
        assert reponse.status_code == 400
        detail = reponse.json()["message"]
        assert "Clé API" in detail

    def test_erreur_technique_ne_fuit_pas(self, client, monkeypatch):
        """Une exception imprévue du générateur ne montre pas son texte brut."""
        from app.services.image_generator import get_image_service

        async def _explose(*a, **k):
            raise RuntimeError("stack interne x8_technique")

        monkeypatch.setattr(
            type(get_image_service()), "generate", _explose
        )
        reponse = client.post(
            "/api/images/generate",
            json={"prompt": "un chat", "provider": "gpt-image-2"},
        )
        assert reponse.status_code == 500
        assert "x8_technique" not in reponse.json()["message"]
