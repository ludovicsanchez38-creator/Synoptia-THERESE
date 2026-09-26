"""B-1669 (suite de B-1528) : le modèle reçoit l'heure du poste avec son
décalage, mais l'outil d'agenda rangeait une heure sans fuseau comme heure
de Paris. En Martinique, « 10 h » devenait 10 h à Paris, soit 4 h sur place.
Une heure sans fuseau est désormais celle du poste, ramenée à l'heure murale
de Paris (B-275) ; à Paris, rien ne change.
"""

import os
import sys
import time
from datetime import datetime

import pytest
from sqlmodel import select

pytestmark = pytest.mark.skipif(sys.platform == "win32", reason="time.tzset n'existe pas sous Windows")


@pytest.fixture
def fuseau_du_poste():
    avant = os.environ.get("TZ")

    def poser(nom: str) -> None:
        os.environ["TZ"] = nom
        time.tzset()

    yield poser
    if avant is None:
        os.environ.pop("TZ", None)
    else:
        os.environ["TZ"] = avant
    time.tzset()


async def _creer_puis_lire(db_session) -> datetime:
    from app.models.entities import CalendarEvent
    from app.services.workspace_tools import _create_calendar_event

    reponse = await _create_calendar_event(
        {"summary": "Point B-1669", "start": "2026-10-01T10:00:00", "end": "2026-10-01T11:00:00"}, db_session,
    )
    assert not reponse.startswith("Erreur"), reponse
    return (await db_session.execute(
        select(CalendarEvent).where(CalendarEvent.summary == "Point B-1669")
    )).scalar_one().start_datetime


@pytest.mark.asyncio
async def test_en_martinique_10h_se_range_16h_a_paris(client, db_session, fuseau_du_poste):
    fuseau_du_poste("America/Martinique")
    assert await _creer_puis_lire(db_session) == datetime(2026, 10, 1, 16, 0)


@pytest.mark.asyncio
async def test_a_paris_10h_reste_10h(client, db_session, fuseau_du_poste):
    fuseau_du_poste("Europe/Paris")
    assert await _creer_puis_lire(db_session) == datetime(2026, 10, 1, 10, 0)
