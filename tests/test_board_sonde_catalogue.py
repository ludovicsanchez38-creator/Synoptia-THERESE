"""Sonde de dérive du catalogue (lot A2, 0.48).

Le frontier de chaque fournisseur est un choix ÉDITORIAL ; la sonde
vérifie seulement qu'il existe ENCORE chez le fournisseur. Dérive =
le frontier du catalogue est ABSENT de la liste /models renvoyée.
Endpoint indisponible = PAS une dérive (drapeau inchangé). Jamais de
bascule de modèle : l'information remonte, la décision reste éditoriale.
"""

import json

import pytest


def _reponse(payload, status_code=200):
    class FauxeReponse:
        def __init__(self):
            self.status_code = status_code

        def raise_for_status(self):
            if status_code >= 400:
                raise RuntimeError(f"HTTP {status_code}")

        def json(self):
            return payload

    return FauxeReponse()


class FauxClient:
    """Client HTTP injecté : une réponse par URL (ou une exception)."""

    def __init__(self, reponses):
        self.reponses = reponses
        self.urls_appelees: list[str] = []

    async def get(self, url, headers=None, timeout=None, params=None):
        self.urls_appelees.append(url)
        for fragment, valeur in self.reponses.items():
            if fragment in url:
                if isinstance(valeur, Exception):
                    raise valeur
                return valeur
        raise AssertionError(f"URL non prévue : {url}")


@pytest.fixture
def etat_vierge(monkeypatch):
    """Remet l'état module-level de la sonde à zéro pour chaque test."""
    from app.services import board as board_module

    monkeypatch.setattr(board_module, "_etat_catalogue", {})
    monkeypatch.setattr(board_module, "_date_derniere_sonde", None)
    return board_module


class TestLaSonde:
    @pytest.mark.asyncio
    async def test_frontier_absent_est_une_derive(self, etat_vierge, monkeypatch):
        board_module = etat_vierge
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
        for var in ("ANTHROPIC_API_KEY", "XAI_API_KEY", "MISTRAL_API_KEY",
                    "GEMINI_API_KEY", "GOOGLE_API_KEY"):
            monkeypatch.delenv(var, raising=False)

        client = FauxClient({
            "api.openai.com": _reponse(
                {"data": [{"id": "gpt-6-nouveau"}, {"id": "gpt-5.5"}]}
            ),
        })
        await board_module.sonder_catalogue(client=client)
        assert board_module._etat_catalogue["openai"] is True

    @pytest.mark.asyncio
    async def test_frontier_present_est_verifie(self, etat_vierge, monkeypatch):
        board_module = etat_vierge
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
        for var in ("ANTHROPIC_API_KEY", "XAI_API_KEY", "MISTRAL_API_KEY",
                    "GEMINI_API_KEY", "GOOGLE_API_KEY"):
            monkeypatch.delenv(var, raising=False)

        client = FauxClient({
            "api.openai.com": _reponse(
                {"data": [{"id": "gpt-5.6-sol"}, {"id": "gpt-5.5"}]}
            ),
        })
        await board_module.sonder_catalogue(client=client)
        assert board_module._etat_catalogue["openai"] is False

    @pytest.mark.asyncio
    async def test_endpoint_indisponible_ne_change_rien(self, etat_vierge, monkeypatch):
        board_module = etat_vierge
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
        for var in ("ANTHROPIC_API_KEY", "XAI_API_KEY", "MISTRAL_API_KEY",
                    "GEMINI_API_KEY", "GOOGLE_API_KEY"):
            monkeypatch.delenv(var, raising=False)

        client = FauxClient({"api.openai.com": RuntimeError("réseau coupé")})
        await board_module.sonder_catalogue(client=client)
        assert board_module._etat_catalogue.get("openai") is None

    @pytest.mark.asyncio
    async def test_gemini_compare_sur_le_nom_court(self, etat_vierge, monkeypatch):
        board_module = etat_vierge
        monkeypatch.setenv("GEMINI_API_KEY", "g-test")
        for var in ("ANTHROPIC_API_KEY", "XAI_API_KEY", "MISTRAL_API_KEY",
                    "OPENAI_API_KEY"):
            monkeypatch.delenv(var, raising=False)

        client = FauxClient({
            "generativelanguage.googleapis.com": _reponse(
                {"models": [{"name": "models/gemini-3.7-flash"}]}
            ),
        })
        await board_module.sonder_catalogue(client=client)
        assert board_module._etat_catalogue["gemini"] is False

    @pytest.mark.asyncio
    async def test_au_plus_une_sonde_par_jour(self, etat_vierge, monkeypatch):
        board_module = etat_vierge
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
        for var in ("ANTHROPIC_API_KEY", "XAI_API_KEY", "MISTRAL_API_KEY",
                    "GEMINI_API_KEY", "GOOGLE_API_KEY"):
            monkeypatch.delenv(var, raising=False)

        client = FauxClient({
            "api.openai.com": _reponse({"data": [{"id": "gpt-5.6-sol"}]}),
        })
        await board_module.sonder_catalogue(client=client)
        await board_module.sonder_catalogue(client=client)
        assert len(client.urls_appelees) == 1

    @pytest.mark.asyncio
    async def test_sans_cle_aucun_appel(self, etat_vierge, monkeypatch):
        board_module = etat_vierge
        for var in ("OPENAI_API_KEY", "ANTHROPIC_API_KEY", "XAI_API_KEY",
                    "MISTRAL_API_KEY", "GEMINI_API_KEY", "GOOGLE_API_KEY"):
            monkeypatch.delenv(var, raising=False)

        client = FauxClient({})
        await board_module.sonder_catalogue(client=client)
        assert client.urls_appelees == []


class TestLeChunkCatalogueStatus:
    @pytest.mark.asyncio
    async def test_une_derive_connue_est_annoncee_en_tete(self, monkeypatch):
        """deliberate() émet catalogue_status quand une dérive est connue -
        et ne bascule JAMAIS de modèle (l'override frontier reste)."""
        from types import SimpleNamespace

        from app.models.board import AdvisorRole, BoardMode, BoardRequest
        from app.services import board as board_module
        from app.services.board import BoardService
        from app.services.llm import LLMProvider

        # Dérive connue posée dans l'état module (sonde déjà passée)
        monkeypatch.setattr(board_module, "_etat_catalogue", {"openai": True})
        import datetime as _dt
        monkeypatch.setattr(
            board_module, "_date_derniere_sonde",
            _dt.datetime.now(_dt.UTC).date().isoformat(),
        )

        synthesis = json.dumps({
            "consensus_points": ["OK"], "divergence_points": [],
            "recommendation": "Y aller.", "confidence": "high",
            "next_steps": ["Cadrer"],
        })

        class FakeLLM:
            def __init__(self, responses, provider=LLMProvider.OPENAI):
                self.responses = responses
                self.calls = 0
                self.config = SimpleNamespace(provider=provider, model="modele-test")

            def prepare_context(self, messages, system_prompt=None):
                return messages, system_prompt

            async def stream_response(self, context, usage_sink=None):
                response = self.responses[min(self.calls, len(self.responses) - 1)]
                self.calls += 1
                yield response

        class FakeSession:
            def add(self, _value):
                pass

            async def commit(self):
                pass

            async def rollback(self):
                pass

            async def refresh(self, _value):
                pass

        import contextlib

        @contextlib.asynccontextmanager
        async def _session_ok():
            yield FakeSession()

        async def _empty_context():
            return ""

        monkeypatch.setattr("app.models.database.get_session_context", _session_ok)
        monkeypatch.setattr(board_module, "get_llm_service", lambda: FakeLLM([synthesis]))
        monkeypatch.setattr(
            board_module, "get_llm_service_for_provider",
            lambda *a, **k: FakeLLM(["Avis mesuré."]),
        )
        monkeypatch.setattr(board_module, "_get_user_context", lambda: "")
        monkeypatch.setattr(BoardService, "_track_usage", lambda *a, **k: None)
        monkeypatch.setattr(
            BoardService, "_search_web_for_context", lambda *a, **k: _empty_context()
        )

        service = BoardService(FakeSession())
        request = BoardRequest(
            question="Faut-il lancer ce pilote maintenant ?",
            mode=BoardMode.CLOUD,
            advisors=[AdvisorRole.STRATEGIST],
        )
        chunks = [chunk async for chunk in service.deliberate(request)]

        statuts = [c for c in chunks if c.type == "catalogue_status"]
        assert len(statuts) == 1
        assert json.loads(statuts[0].content) == {"providers": {"openai": True}}

    @pytest.mark.asyncio
    async def test_sans_derive_aucun_chunk(self, monkeypatch):
        from app.services import board as board_module

        monkeypatch.setattr(board_module, "_etat_catalogue", {"openai": False})
        derives = board_module.derives_connues()
        assert derives == {}


class TestLaRouteAdvisors:
    def test_modele_deprecie_expose(self, client, monkeypatch):
        from app.services import board as board_module

        monkeypatch.setattr(
            board_module, "_etat_catalogue", {"openai": True, "anthropic": False}
        )
        reponse = client.get("/api/board/advisors")
        assert reponse.status_code == 200
        par_role = {a["role"]: a for a in reponse.json()}
        # strategist -> openai (déprécié), analyst -> anthropic (vérifié)
        assert par_role["strategist"]["modele_deprecie"] is True
        assert par_role["analyst"]["modele_deprecie"] is False
        # devil -> grok, non sondé : null
        assert par_role["devil"]["modele_deprecie"] is None
