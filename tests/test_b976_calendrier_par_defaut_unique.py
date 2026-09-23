"""B-976 (cycle 11, 23/09/2026, ronde B du ZERO_CHECK) : le calendrier local
par défaut était créé en N exemplaires, tous « principaux », par N lectures
simultanées de GET /api/calendar/calendars.

Le routeur se disait « idempotent » mais enchaînait « lire, puis créer si
vide » sans verrou : deux lectures concurrentes voyaient chacune une liste
vide et créaient chacune « Mon calendrier ». Constaté dans l'interface au
premier affichage de l'Agenda (double effet de StrictMode en développement).

Plusieurs tours, comme pour B-273 : au premier, le bassin de connexions est
froid et les requêtes ne s'entrelacent pas toujours.
"""

from __future__ import annotations

import asyncio

import httpx
import pytest


@pytest.mark.asyncio
async def test_des_lectures_simultanees_ne_creent_qu_un_calendrier(client):
    from app.main import app
    from app.models import database as db_module
    from app.models.entities import Calendar
    from sqlmodel import SQLModel

    transport = httpx.ASGITransport(app=app, raise_app_exceptions=True)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as concurrent:
        for tour in range(6):
            # Base sans calendrier au départ de chaque tour.
            SQLModel.metadata.drop_all(db_module.sync_engine, tables=[Calendar.__table__])
            SQLModel.metadata.create_all(db_module.sync_engine, tables=[Calendar.__table__])

            reponses = await asyncio.gather(
                *(concurrent.get("/api/calendar/calendars") for _ in range(5)),
                return_exceptions=True,
            )
            for reponse in reponses:
                assert not isinstance(reponse, BaseException), f"tour {tour} : {reponse!r}"
                assert reponse.status_code == 200, f"tour {tour} : {reponse.status_code} {reponse.text[:200]}"

            finale = await concurrent.get("/api/calendar/calendars?create_default=false")
            calendriers = finale.json()
            assert len(calendriers) == 1, f"tour {tour} : {len(calendriers)} calendriers « {calendriers[0]['summary']} »"
            assert calendriers[0]["primary"] is True
            for reponse in reponses:
                assert len(reponse.json()) == 1, f"tour {tour} : une lecture a vu {len(reponse.json())} calendriers"
