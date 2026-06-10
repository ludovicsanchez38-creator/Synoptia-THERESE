"""Tests du router dashboard (setup-status pour la vue Accueil)."""
import pytest
from app.models.entities import Calendar, Contact, EmailAccount
from httpx import AsyncClient


class TestToday:
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


class TestSetupStatus:
    @pytest.mark.asyncio
    async def test_setup_status_all_empty(self, client: AsyncClient):
        resp = await client.get("/api/dashboard/setup-status")
        assert resp.status_code == 200
        assert resp.json() == {
            "has_calendar": False,
            "has_email": False,
            "billing_complete": False,
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
