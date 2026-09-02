"""B-026 — le rappel par défaut de 30 minutes n'était lu par aucun fournisseur.

02/09/2026. `CreateEventRequest.reminders` (base_provider.py:98) vaut `[30]`
par défaut, et les trois fournisseurs annoncent `supports_reminders = True`.
Le champ était pourtant mort de bout en bout : `local_provider.create_event`
construisait `CalendarEvent` sans jamais le lire (recurrence et attendees, eux,
étaient repris), l'entité n'avait aucune colonne, et `_event_to_dto` rendait
donc toujours `reminders == []`.

Chaque rendez-vous créé depuis le chat (`workspace_tools.py`, seul
constructeur de la requête) portait ce défaut `[30]` et le perdait en silence.

Ce lot ferme le fournisseur LOCAL, celui que la reproduction désigne comme
cause racine. Google et CalDAV continuent d'annoncer `supports_reminders`
sans rien écrire : c'est noté comme dette, pas corrigé ici.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest


async def _agenda_local(db_session):
    from app.models.entities import Calendar
    from app.services.calendar.local_provider import LocalCalendarProvider

    agenda = Calendar(
        id="cal-b026",
        summary="Agenda B-026",
        provider="local",
        primary=True,
    )
    db_session.add(agenda)
    await db_session.commit()
    return LocalCalendarProvider(db_session), agenda.id


@pytest.mark.asyncio
async def test_le_rappel_par_defaut_survit_a_la_creation(db_session):
    """Le défaut posé par la dataclass doit se retrouver à la relecture."""
    from app.services.calendar.base_provider import CreateEventRequest

    fournisseur, agenda_id = await _agenda_local(db_session)
    debut = datetime.now(UTC).replace(tzinfo=None) + timedelta(days=1)

    cree = await fournisseur.create_event(
        CreateEventRequest(
            calendar_id=agenda_id,
            summary="Point client",
            start=debut,
            end=debut + timedelta(hours=1),
        )
    )
    assert cree.reminders == [30], (
        f"le rappel par défaut disparaît à la création : {cree.reminders!r}"
    )

    relu = await fournisseur.get_event(agenda_id, cree.id)
    assert relu.reminders == [30], (
        f"le rappel n'est pas relu depuis la base : {relu.reminders!r}"
    )


@pytest.mark.asyncio
async def test_un_rappel_explicite_est_conserve(db_session):
    from app.services.calendar.base_provider import CreateEventRequest

    fournisseur, agenda_id = await _agenda_local(db_session)
    debut = datetime.now(UTC).replace(tzinfo=None) + timedelta(days=2)

    cree = await fournisseur.create_event(
        CreateEventRequest(
            calendar_id=agenda_id,
            summary="Atelier",
            start=debut,
            end=debut + timedelta(hours=2),
            reminders=[10, 60],
        )
    )
    relu = await fournisseur.get_event(agenda_id, cree.id)
    assert relu.reminders == [10, 60], relu.reminders


@pytest.mark.asyncio
async def test_une_absence_de_rappel_voulue_est_conservee(db_session):
    """`[]` est un choix, pas une absence de choix : il ne doit pas repasser à [30]."""
    from app.services.calendar.base_provider import CreateEventRequest

    fournisseur, agenda_id = await _agenda_local(db_session)
    debut = datetime.now(UTC).replace(tzinfo=None) + timedelta(days=3)

    cree = await fournisseur.create_event(
        CreateEventRequest(
            calendar_id=agenda_id,
            summary="Sans rappel",
            start=debut,
            end=debut + timedelta(hours=1),
            reminders=[],
        )
    )
    relu = await fournisseur.get_event(agenda_id, cree.id)
    assert relu.reminders == [], relu.reminders


@pytest.mark.asyncio
async def test_la_mise_a_jour_ecrit_le_rappel(db_session):
    from app.services.calendar.base_provider import CreateEventRequest, UpdateEventRequest

    fournisseur, agenda_id = await _agenda_local(db_session)
    debut = datetime.now(UTC).replace(tzinfo=None) + timedelta(days=4)

    cree = await fournisseur.create_event(
        CreateEventRequest(
            calendar_id=agenda_id,
            summary="Révision",
            start=debut,
            end=debut + timedelta(hours=1),
        )
    )
    modifie = await fournisseur.update_event(
        agenda_id, cree.id, UpdateEventRequest(reminders=[5])
    )
    assert modifie.reminders == [5], modifie.reminders

    relu = await fournisseur.get_event(agenda_id, cree.id)
    assert relu.reminders == [5], relu.reminders


@pytest.mark.asyncio
async def test_une_mise_a_jour_qui_ne_parle_pas_du_rappel_le_laisse(db_session):
    """`None` sur `UpdateEventRequest` veut dire « je n'y touche pas »."""
    from app.services.calendar.base_provider import CreateEventRequest, UpdateEventRequest

    fournisseur, agenda_id = await _agenda_local(db_session)
    debut = datetime.now(UTC).replace(tzinfo=None) + timedelta(days=5)

    cree = await fournisseur.create_event(
        CreateEventRequest(
            calendar_id=agenda_id,
            summary="Inchangé",
            start=debut,
            end=debut + timedelta(hours=1),
            reminders=[15],
        )
    )
    await fournisseur.update_event(
        agenda_id, cree.id, UpdateEventRequest(summary="Renommé")
    )
    relu = await fournisseur.get_event(agenda_id, cree.id)
    assert relu.reminders == [15], relu.reminders
