"""Tests du router dashboard (setup-status pour la vue Accueil)."""
import pytest
from httpx import AsyncClient

from app.models.entities import Calendar, EmailAccount


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
