"""P-116 (persona Claire, cycle 13) : « pour une coach, la fiche cliente sans
ses séances n'a pas de sens ». Une séance posée avec l'e-mail d'Hélène en
participant n'apparaissait nulle part sur sa fiche. La route rend les
prochaines séances d'un contact, rapprochées par son adresse (même règle que
Préparer et le brief)."""

from datetime import date, datetime, time, timedelta

import pytest
from app.models.entities import Calendar, CalendarEvent, Contact
from httpx import AsyncClient

JOUR = date(2026, 9, 25)


@pytest.mark.asyncio
async def test_les_prochaines_seances_d_un_contact(client: AsyncClient, db_session, monkeypatch):
    monkeypatch.setattr("app.routers.memory.date_civile_paris", lambda *_a, **_k: JOUR)
    db_session.add(Contact(id="c-helene", first_name="Hélène", last_name="Ménard", email="helene@example.test"))
    db_session.add(Calendar(id="cal-p116", summary="Agenda", provider="local"))
    seance = lambda jours, h: datetime.combine(JOUR + timedelta(days=jours), time(h, 0))  # noqa: E731
    db_session.add_all([
        CalendarEvent(id="ev-demain", calendar_id="cal-p116", summary="Séance 3", start_datetime=seance(1, 14),
                      end_datetime=seance(1, 15), attendees='[{"email":"Helene@Example.Test"}]'),
        CalendarEvent(id="ev-apres", calendar_id="cal-p116", summary="Séance 4", start_datetime=seance(8, 14),
                      end_datetime=seance(8, 15), attendees='["helene@example.test"]'),
        CalendarEvent(id="ev-passee", calendar_id="cal-p116", summary="Séance 2", start_datetime=seance(-6, 14),
                      end_datetime=seance(-6, 15), attendees='["helene@example.test"]'),
        CalendarEvent(id="ev-autre", calendar_id="cal-p116", summary="Autre cliente", start_datetime=seance(2, 9),
                      end_datetime=seance(2, 10), attendees='["julien@example.test"]'),
        CalendarEvent(id="ev-annulee", calendar_id="cal-p116", summary="Annulée", start_datetime=seance(3, 9),
                      end_datetime=seance(3, 10), attendees='["helene@example.test"]', status="cancelled"),
        CalendarEvent(id="ev-voisine", calendar_id="cal-p116", summary="Homonyme d'adresse", start_datetime=seance(4, 9),
                      end_datetime=seance(4, 10), attendees='["marie.helene@example.test"]'),
    ])
    await db_session.commit()

    reponse = await client.get("/api/memory/contacts/c-helene/seances")
    assert reponse.status_code == 200
    assert [s["summary"] for s in reponse.json()] == ["Séance 3", "Séance 4"]


@pytest.mark.asyncio
async def test_sans_adresse_aucune_seance_n_est_inventee(client: AsyncClient, db_session):
    db_session.add(Contact(id="c-sans", first_name="Sans", last_name="Adresse"))
    await db_session.commit()
    reponse = await client.get("/api/memory/contacts/c-sans/seances")
    assert reponse.status_code == 200
    assert reponse.json() == []


@pytest.mark.asyncio
async def test_contact_inconnu(client: AsyncClient):
    assert (await client.get("/api/memory/contacts/inconnu/seances")).status_code == 404
