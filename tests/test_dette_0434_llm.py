"""Dette 0.43.4 - le parcours utilisateur des quatre fournisseurs (24/08/2026).

Leçon du 24/08 : dix-neuf tests verts n'avaient pas empêché quatre fournisseurs
d'être inutilisables, parce qu'aucun test ne parcourait le chemin réel. Ceux-ci
le font : configuration par l'API, adresse effectivement appelée, catalogue
servi par le backend, routage des agents par identifiant de modèle.
"""

import pytest

from app.services.providers.base import LLMConfig, LLMProvider
from app.services.providers.qwen import QwenProvider

ADRESSE_ESPACE = "https://ws-1234.ap-southeast-1.maas.aliyuncs.com/compatible-mode/v1"


class TestQwenSeConfigureDeBoutEnBout:
    """L'adresse d'espace de travail : saisie, persistée, réellement appelée."""

    @pytest.mark.asyncio
    async def test_post_base_url_puis_get_la_restitue(self, client):
        resp = await client.post(
            "/api/config/llm",
            json={
                "provider": "qwen",
                "model": "qwen3.8-max",
                "base_url": ADRESSE_ESPACE,
            },
        )
        assert resp.status_code == 200
        assert resp.json()["base_url"] == ADRESSE_ESPACE

        resp = await client.get("/api/config/llm")
        assert resp.json()["base_url"] == ADRESSE_ESPACE

    @pytest.mark.asyncio
    async def test_la_base_url_survit_a_un_post_sans_elle(self, client):
        """Changer de modèle ne doit pas effacer l'adresse déjà enregistrée."""
        await client.post(
            "/api/config/llm",
            json={"provider": "qwen", "model": "qwen3.8-max", "base_url": ADRESSE_ESPACE},
        )
        resp = await client.post(
            "/api/config/llm",
            json={"provider": "qwen", "model": "qwen3.7-flash"},
        )
        assert resp.json()["base_url"] == ADRESSE_ESPACE

    @pytest.mark.asyncio
    async def test_le_service_construit_porte_la_base_url(self, client):
        import app.services.llm as llm_module

        await client.post(
            "/api/config/llm",
            json={"provider": "qwen", "model": "qwen3.8-max", "base_url": ADRESSE_ESPACE},
        )
        assert llm_module._llm_service.config.base_url == ADRESSE_ESPACE

    def test_l_adresse_configuree_est_celle_appelee(self):
        """url_effective() n'était appelé NULLE PART : le défaut avec le
        marqueur {EspaceDeTravail} partait tel quel sur le réseau."""
        config = LLMConfig(
            provider=LLMProvider.QWEN, model="qwen3.8-max",
            api_key="k", base_url=ADRESSE_ESPACE,
        )
        fournisseur = QwenProvider(config, client=None)

        assert fournisseur.url_effective() == ADRESSE_ESPACE + "/chat/completions"

    def test_stream_appelle_url_effective(self):
        """Le contrat de câblage : stream() doit passer par url_effective(),
        sinon la configuration reste décorative."""
        import inspect

        from app.services.providers.openai import OpenAIProvider

        source = inspect.getsource(OpenAIProvider.stream)
        assert "url_effective()" in source, (
            "OpenAIProvider.stream doit appeler self.url_effective() : "
            "API_URL en dur rend base_url décoratif pour tous les héritiers"
        )


class TestLeCatalogueEstServiParLeBackend:
    """Quatre copies frontend divergeaient (l'onboarding proposait encore
    gpt-5.3-codex, retiré partout ailleurs). Le backend devient LA source."""

    @pytest.mark.asyncio
    async def test_la_route_sert_chaque_fournisseur(self, client):
        for fournisseur, attendu in [
            ("qwen", "qwen3.8-max"),
            ("glm", "glm-5.3"),
            ("kimi", "kimi-k3"),
            ("minimax", "MiniMax-M3"),
            ("openai", "gpt-5.6-sol"),
        ]:
            resp = await client.get(f"/api/config/llm/models/{fournisseur}")
            assert resp.status_code == 200, fournisseur
            assert attendu in resp.json()["models"], fournisseur

    @pytest.mark.asyncio
    async def test_un_fournisseur_inconnu_est_refuse(self, client):
        resp = await client.get("/api/config/llm/models/skynet")
        assert resp.status_code == 400


class TestLesAgentsRoutentLesNouveauxFournisseurs:
    """Le runtime des agents route par préfixe de modèle : glm-5.3 ou
    MiniMax-M3 retombaient silencieusement sur le service principal."""

    def _fournisseur_demande(self, monkeypatch, model_id: str) -> str | None:
        from app.services.agents import runtime

        demandes: list[str] = []

        def espion(provider_name, model_override=None):
            demandes.append(provider_name)
            return object()  # n'importe quoi de non-None : le routage s'arrête là

        monkeypatch.setattr(
            "app.services.llm.get_llm_service_for_provider", espion
        )
        runtime._get_llm_for_model(model_id)
        return demandes[0] if demandes else None

    def test_glm(self, monkeypatch):
        assert self._fournisseur_demande(monkeypatch, "glm-5.3") == "glm"

    def test_kimi(self, monkeypatch):
        assert self._fournisseur_demande(monkeypatch, "kimi-k3") == "kimi"

    def test_qwen(self, monkeypatch):
        assert self._fournisseur_demande(monkeypatch, "qwen3.8-max") == "qwen"

    def test_minimax_avec_sa_casse(self, monkeypatch):
        assert self._fournisseur_demande(monkeypatch, "MiniMax-M3") == "minimax"

    def test_ollama_garde_la_priorite_sur_qwen(self, monkeypatch):
        """qwen3:32b est un modèle LOCAL : les deux-points doivent router vers
        Ollama avant que le préfixe qwen ne s'en mêle."""
        assert self._fournisseur_demande(monkeypatch, "qwen3:32b") == "ollama"
