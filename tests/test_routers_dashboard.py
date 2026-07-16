"""Tests du router dashboard (setup-status pour la vue Accueil)."""
from datetime import date, datetime, time, timedelta

import pytest
from app.models.entities import (
    Calendar,
    CalendarEvent,
    Contact,
    EmailAccount,
    EmailFollowUp,
    EmailMessage,
    Task,
)
from httpx import AsyncClient


class TestToday:
    @pytest.mark.asyncio
    async def test_today_agrege_relances_et_enjeu_des_evenements(
        self, client: AsyncClient, db_session
    ):
        now = datetime.now()
        contact = Contact(
            id="ct-brief-client",
            first_name="Camille",
            last_name="Martin",
            email="camille@example.test",
            stage="client",
        )
        account = EmailAccount(id="acc-brief", email="ludo@example.test")
        message = EmailMessage(
            id="msg-brief",
            thread_id="thread-brief",
            account_id=account.id,
            subject="Proposition à relancer",
            from_email="camille@example.test",
            from_name="Camille Martin",
            to_emails='["ludo@example.test"]',
            date=now,
            internal_date=now,
            labels='["INBOX"]',
        )
        calendar = Calendar(id="cal-brief", summary="Agenda", provider="local")
        meeting = CalendarEvent(
            id="event-brief",
            calendar_id=calendar.id,
            summary="Point client",
            start_datetime=datetime.combine(date.today(), time(10, 0)),
            end_datetime=datetime.combine(date.today(), time(11, 0)),
            attendees='[{"email":"Camille@Example.Test"}]',
        )
        follow_up = EmailFollowUp(
            id="follow-up-brief",
            email_message_id=message.id,
            contact_id=contact.id,
            due_date=date.today().isoformat() + "T12:00:00",
            note="Rappeler après lecture",
        )
        db_session.add_all([contact, account, message, calendar, meeting, follow_up])
        await db_session.commit()

        resp = await client.get("/api/dashboard/today")

        assert resp.status_code == 200
        data = resp.json()
        assert data["events"][0]["attendees_count"] == 1
        assert data["events"][0]["crm_contact_ids"] == [contact.id]
        assert data["due_follow_ups"] == [{
            "id": follow_up.id,
            "due_date": follow_up.due_date,
            "note": follow_up.note,
            "email_subject": message.subject,
            "email_from": message.from_name,
            "contact_id": contact.id,
            "contact_name": "Camille Martin",
        }]
        assert data["summary"]["follow_ups_count"] == 1

    @pytest.mark.asyncio
    async def test_today_tache_en_retard_priorisee_en_tete(
        self, client: AsyncClient, db_session
    ):
        """BUG-125 : une tâche en retard doit apparaître dans le dashboard, même
        avec d'autres tâches urgentes. Sans ORDER BY, l'ordre était arbitraire :
        la tâche en retard pouvait passer après les tâches dues aujourd'hui et
        sortir du top-3 affiché. On trie par échéance croissante (retard d'abord).

        NB : échéances posées en dates CIVILES fixes (aujourd'hui 23:59 / J-5),
        jamais `now + N heures` - un run après 22h faisait déborder les tâches
        « du jour » sur demain et le test changeait de sens selon l'heure."""
        today_evening = datetime.combine(date.today(), time(23, 59))
        # Tâches dues aujourd'hui créées EN PREMIER, tâche en retard EN DERNIER.
        for i in range(4):
            db_session.add(
                Task(id=f"tk-today-{i}", title=f"Aujourd'hui {i}", status="todo",
                     due_date=today_evening)
            )
        db_session.add(
            Task(id="tk-overdue", title="Tâche en retard", status="todo",
                 due_date=today_evening - timedelta(days=5))
        )
        await db_session.commit()

        resp = await client.get("/api/dashboard/today")
        assert resp.status_code == 200
        titles = [t["title"] for t in resp.json()["urgent_tasks"]]
        # La plus en retard est en tête, donc dans le top-3 affiché par le front.
        assert titles[0] == "Tâche en retard"
        assert "Tâche en retard" in titles[:3]

    @pytest.mark.asyncio
    async def test_today_tache_due_demain_minuit_pas_urgente(
        self, client: AsyncClient, db_session
    ):
        """BUG-125 (revue) : off-by-one - une tâche due DEMAIN à 00:00 pile
        n'est pas urgente aujourd'hui. Le filtre `due_date <= demain minuit`
        l'incluait à tort ; il faut une borne stricte `< demain minuit`."""
        tomorrow_midnight = datetime.combine(date.today() + timedelta(days=1), time(0, 0))
        db_session.add(
            Task(id="tk-tomorrow", title="Tâche de demain", status="todo",
                 due_date=tomorrow_midnight)
        )
        await db_session.commit()

        resp = await client.get("/api/dashboard/today")
        assert resp.status_code == 200
        titles = [t["title"] for t in resp.json()["urgent_tasks"]]
        assert "Tâche de demain" not in titles

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
