"""Tests du router dashboard (setup-status pour la vue Accueil)."""
from datetime import datetime, timedelta

import pytest
from app.models.entities import Calendar, Contact, EmailAccount, Task
from httpx import AsyncClient


class TestToday:
    @pytest.mark.asyncio
    async def test_today_tache_en_retard_priorisee_en_tete(
        self, client: AsyncClient, db_session
    ):
        """BUG-125 : une tâche en retard doit apparaître dans le dashboard, même
        avec d'autres tâches urgentes. Sans ORDER BY, l'ordre était arbitraire :
        la tâche en retard pouvait passer après les tâches dues aujourd'hui et
        sortir du top-3 affiché. On trie par échéance croissante (retard d'abord)."""
        now = datetime.now()
        # Tâches dues aujourd'hui créées EN PREMIER, tâche en retard EN DERNIER.
        for i in range(4):
            db_session.add(
                Task(id=f"tk-today-{i}", title=f"Aujourd'hui {i}", status="todo",
                     due_date=now + timedelta(hours=2))
            )
        db_session.add(
            Task(id="tk-overdue", title="Tâche en retard", status="todo",
                 due_date=now - timedelta(days=5))
        )
        await db_session.commit()

        resp = await client.get("/api/dashboard/today")
        assert resp.status_code == 200
        titles = [t["title"] for t in resp.json()["urgent_tasks"]]
        # La plus en retard est en tête, donc dans le top-3 affiché par le front.
        assert titles[0] == "Tâche en retard"
        assert "Tâche en retard" in titles[:3]

    @pytest.mark.asyncio
    async def test_today_stale_prospect_remonte_avec_son_nom(
        self, client: AsyncClient, db_session
    ):
        """Régression : un prospect sans interaction doit apparaître dans
        stale_prospects avec son nom. Contact n'a pas d'attribut `name`
        (lève AttributeError, avalé en liste vide) — il faut display_name."""
        db_session.add(
            Contact(
                id="ct-stale-1",
                first_name="Jean",
                last_name="Test",
                stage="contact",
                last_interaction=None,
            )
        )
        await db_session.commit()

        resp = await client.get("/api/dashboard/today")
        assert resp.status_code == 200
        prospects = resp.json()["stale_prospects"]
        assert [p["name"] for p in prospects] == ["Jean Test"]


_LLM_ENV_KEYS = [
    "ANTHROPIC_API_KEY", "MISTRAL_API_KEY", "OPENAI_API_KEY", "GEMINI_API_KEY",
    "GOOGLE_API_KEY", "GROQ_API_KEY", "XAI_API_KEY", "OPENROUTER_API_KEY",
]


def _clear_llm_env(monkeypatch):
    """Neutralise TOUTES les sources LLM : env, .env (settings) et le ping
    Ollama (la machine de dev/CI peut avoir un Ollama qui tourne)."""
    from app.config import settings

    for key in _LLM_ENV_KEYS:
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setattr(settings, "anthropic_api_key", None, raising=False)
    monkeypatch.setattr(settings, "mistral_api_key", None, raising=False)
    # Port 9 (discard) : connexion refusée immédiate, ping toujours négatif
    monkeypatch.setattr(settings, "ollama_base_url", "http://127.0.0.1:9", raising=False)


class TestSetupStatus:
    @pytest.mark.asyncio
    async def test_setup_status_all_empty(self, client: AsyncClient, monkeypatch):
        _clear_llm_env(monkeypatch)
        resp = await client.get("/api/dashboard/setup-status")
        assert resp.status_code == 200
        assert resp.json() == {
            "has_calendar": False,
            "has_email": False,
            "billing_complete": False,
            "has_llm_key": False,
        }

    @pytest.mark.asyncio
    async def test_setup_status_with_calendar_and_email(
        self, client: AsyncClient, db_session
    ):
        db_session.add(
            Calendar(
                id="cal-test-1",
                summary="Perso",
                provider="local",
                timezone="Europe/Paris",
            )
        )
        db_session.add(
            EmailAccount(
                id="acc-test-1",
                email="x@y.com",
                provider="gmail",
            )
        )
        await db_session.commit()

        resp = await client.get("/api/dashboard/setup-status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["has_calendar"] is True
        assert data["has_email"] is True

    @pytest.mark.asyncio
    async def test_setup_status_sans_cle_llm_le_signale(
        self, client: AsyncClient, monkeypatch
    ):
        """US-012 : sans aucune clé LLM, la checklist doit pouvoir le rappeler."""
        _clear_llm_env(monkeypatch)
        resp = await client.get("/api/dashboard/setup-status")
        assert resp.status_code == 200
        assert resp.json()["has_llm_key"] is False

    @pytest.mark.asyncio
    async def test_setup_status_avec_cle_env_llm(
        self, client: AsyncClient, monkeypatch
    ):
        """US-012 : une clé en variable d'environnement suffit (n'importe quel provider)."""
        _clear_llm_env(monkeypatch)
        monkeypatch.setenv("MISTRAL_API_KEY", "k-test")
        resp = await client.get("/api/dashboard/setup-status")
        assert resp.status_code == 200
        assert resp.json()["has_llm_key"] is True

    @pytest.mark.asyncio
    async def test_setup_status_avec_cle_db_llm(
        self, client: AsyncClient, db_session, monkeypatch
    ):
        """US-012 : une clé stockée en DB (Preference) compte aussi."""
        from app.models.entities import Preference

        _clear_llm_env(monkeypatch)
        db_session.add(Preference(key="anthropic_api_key", value="sk-ant-test"))
        await db_session.commit()

        resp = await client.get("/api/dashboard/setup-status")
        assert resp.status_code == 200
        assert resp.json()["has_llm_key"] is True

    @pytest.mark.asyncio
    async def test_setup_status_provider_ollama_compte(
        self, client: AsyncClient, db_session, monkeypatch
    ):
        """Revue adversariale US-012 : l'utilisateur 100 % Ollama (persona
        souveraineté) ne doit PAS voir la carte « Configurer une clé IA »
        en permanence."""
        from app.models.entities import Preference

        _clear_llm_env(monkeypatch)
        db_session.add(Preference(key="llm_provider", value="ollama"))
        await db_session.commit()

        resp = await client.get("/api/dashboard/setup-status")
        assert resp.status_code == 200
        assert resp.json()["has_llm_key"] is True
