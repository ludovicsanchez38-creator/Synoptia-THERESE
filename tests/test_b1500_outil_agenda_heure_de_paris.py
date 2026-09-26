"""B-1500 : l'outil agenda du chat rangeait l'heure du modèle sans la
ramener à l'heure de Paris.

L'agenda local range une heure murale de Paris sans fuseau (B-275). Un
modèle qui écrit « 2026-10-01T08:00:00Z » (10 h à Paris) voyait son
rendez-vous rangé à 8 h : SQLite jette le décalage. Même règle que
l'écran depuis B-1487.
"""

import os
import sys
import time
from datetime import datetime

import pytest
from sqlmodel import select


async def _creer(db_session, debut: str, fin: str) -> str:
    from app.services.workspace_tools import _create_calendar_event

    return await _create_calendar_event({"summary": "Point chantier", "start": debut, "end": fin}, db_session)


async def _stocke(db_session):
    from app.models.entities import CalendarEvent

    return (await db_session.execute(
        select(CalendarEvent).where(CalendarEvent.summary == "Point chantier")
    )).scalar_one()


@pytest.mark.asyncio
async def test_une_heure_datee_se_range_en_heure_de_paris(client, db_session):
    reponse = await _creer(db_session, "2026-10-01T08:00:00Z", "2026-10-01T09:00:00+00:00")
    assert not reponse.startswith("Erreur"), reponse
    evenement = await _stocke(db_session)
    assert evenement.start_datetime == datetime(2026, 10, 1, 10, 0)
    assert evenement.end_datetime == datetime(2026, 10, 1, 11, 0)


@pytest.mark.skipif(sys.platform == "win32", reason="time.tzset n'existe pas sous Windows")
@pytest.mark.asyncio
async def test_une_heure_sans_fuseau_reste_celle_de_paris(client, db_session, monkeypatch):
    # B-1669 : une heure sans fuseau est celle du POSTE ; ce cas vaut pour
    # un poste à Paris (la CI tourne en UTC).
    monkeypatch.setenv("TZ", "Europe/Paris")
    time.tzset()
    reponse = await _creer(db_session, "2026-10-01T10:00:00", "2026-10-01T11:00:00")
    assert not reponse.startswith("Erreur"), reponse
    assert (await _stocke(db_session)).start_datetime == datetime(2026, 10, 1, 10, 0)


@pytest.mark.skipif(sys.platform == "win32", reason="time.tzset n'existe pas sous Windows")
@pytest.mark.asyncio
async def test_un_debut_date_et_une_fin_sans_fuseau_ne_font_pas_planter(client, db_session, monkeypatch):
    monkeypatch.setenv("TZ", "Europe/Paris")
    time.tzset()
    reponse = await _creer(db_session, "2026-10-01T08:00:00Z", "2026-10-01T11:00:00")
    assert not reponse.startswith("Erreur"), reponse
    evenement = await _stocke(db_session)
    assert (evenement.start_datetime, evenement.end_datetime) == (datetime(2026, 10, 1, 10, 0), datetime(2026, 10, 1, 11, 0))


@pytest.fixture(autouse=True)
def _fuseau_rendu():
    # B-1692 : la fixture rétablit elle-même TZ. Elle se démontait avant
    # monkeypatch : tzset relisait encore Europe/Paris et le fuseau fuyait
    # dans les fichiers de test suivants (la CI tourne en UTC).
    avant = os.environ.get("TZ")
    yield
    if avant is None:
        os.environ.pop("TZ", None)
    else:
        os.environ["TZ"] = avant
    # B-1676 : time.tzset n'existe pas sous Windows ; l'appeler au démontage
    # mettait la suite Windows en erreur sur chaque test du fichier.
    if hasattr(time, "tzset"):
        time.tzset()
