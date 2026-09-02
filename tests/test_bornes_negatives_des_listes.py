"""B-183 (RB2-013) — un plafond que l'on contourne par un signe moins.

`GET /api/calendar/events` borne `max_results` par le haut (`le=250`) et pas
par le bas : SQLite lit `LIMIT -1` comme « sans limite », si bien que
`max_results=-1` rend la table entière. Le plafond existe, donc l'intention de
borner aussi. Même trou sur `GET /api/data/logs`, dont `limit` et `offset` sont
déclarés sans aucune borne.
"""

import pytest
from app.services.audit import ActivityLog
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


async def _calendrier_local_avec_deux_evenements(client: AsyncClient) -> str:
    """Un calendrier local et deux événements : de quoi voir un plafond sauter."""
    reponse = await client.post(
        "/api/calendar/calendars",
        params={
            "summary": "Agenda des bornes",
            "description": "Deux evenements",
            "timezone": "Europe/Paris",
            "provider_type": "local",
        },
    )
    assert reponse.status_code == 200, reponse.text
    calendrier_id = reponse.json()["id"]

    for indice, titre in enumerate(("Premier point", "Second point"), start=1):
        cree = await client.post(
            "/api/calendar/events",
            json={
                "calendar_id": calendrier_id,
                "summary": titre,
                "start_datetime": f"2026-09-0{indice}T10:00:00",
                "end_datetime": f"2026-09-0{indice}T11:00:00",
            },
        )
        assert cree.status_code == 200, cree.text

    return calendrier_id


class TestB183PlafondAgendaNonContournable:
    @pytest.mark.asyncio
    async def test_max_results_positif_respecte_le_plafond(self, client: AsyncClient) -> None:
        """Contrôle de l'instrument : le plafond haut fonctionne, lui."""
        calendrier_id = await _calendrier_local_avec_deux_evenements(client)

        un_seul = await client.get(
            f"/api/calendar/events?calendar_id={calendrier_id}&max_results=1"
        )
        assert un_seul.status_code == 200, un_seul.text
        assert len(un_seul.json()) == 1

        trop = await client.get(
            f"/api/calendar/events?calendar_id={calendrier_id}&max_results=251"
        )
        assert trop.status_code == 422, trop.text

    @pytest.mark.asyncio
    async def test_max_results_negatif_refuse(self, client: AsyncClient) -> None:
        """-1 ne demande pas « moins d'un élément » : il demande TOUT."""
        calendrier_id = await _calendrier_local_avec_deux_evenements(client)

        reponse = await client.get(
            f"/api/calendar/events?calendar_id={calendrier_id}&max_results=-1"
        )

        assert reponse.status_code == 422, (
            f"max_results=-1 accepte : {reponse.status_code} avec "
            f"{len(reponse.json())} evenement(s)"
        )
        assert "max_results" in reponse.text

    @pytest.mark.asyncio
    async def test_max_results_tres_negatif_refuse(self, client: AsyncClient) -> None:
        calendrier_id = await _calendrier_local_avec_deux_evenements(client)

        reponse = await client.get(
            f"/api/calendar/events?calendar_id={calendrier_id}&max_results=-99999"
        )

        assert reponse.status_code == 422, reponse.text


class TestB183BornesDuJournalDActivite:
    """Mesure jumelle : GET /api/data/logs déclare `limit`/`offset` nus."""

    @pytest.mark.asyncio
    async def test_limite_negative_refusee(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        for indice in range(3):
            db_session.add(
                ActivityLog(action="api_key_set", resource_type="config", resource_id=f"r{indice}")
            )
        await db_session.commit()

        borne = await client.get("/api/data/logs?limit=2")
        assert borne.status_code == 200, borne.text
        assert len(borne.json()["logs"]) == 2

        reponse = await client.get("/api/data/logs?limit=-1")

        assert reponse.status_code == 422, (
            f"limit=-1 accepte : {reponse.status_code}, "
            f"{len(reponse.json().get('logs', []))} ligne(s) rendues"
        )
        assert "limit" in reponse.text

    @pytest.mark.asyncio
    async def test_decalage_negatif_refuse(self, client: AsyncClient) -> None:
        reponse = await client.get("/api/data/logs?offset=-1")

        assert reponse.status_code == 422, reponse.text
        assert "offset" in reponse.text
