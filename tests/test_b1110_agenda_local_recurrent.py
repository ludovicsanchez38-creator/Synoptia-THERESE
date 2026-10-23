"""B-1110 : le chat doit retrouver les occurrences du calendrier local."""

import json
from datetime import datetime
from unittest.mock import AsyncMock

import pytest
from app.models.entities import Calendar, CalendarEvent, EmailAccount
from app.services.workspace_tools import _list_calendar_events, poser_ecran


@pytest.fixture(autouse=True)
def ecran_neutre():
    poser_ecran()
    yield
    poser_ecran()


async def _agenda(session, compte="imap"):
    if compte:
        session.add(EmailAccount(id="courrier", email="test@exemple.test", provider=compte))
    session.add(Calendar(id="local", summary="Mon calendrier", provider="local", primary=False))
    await session.commit()


def _periode():
    # Semaine civile suivant le retour du jeudi 22/10, après le changement d'heure.
    return {"time_min": "2026-10-26T00:00:00+01:00", "time_max": "2026-11-02T00:00:00+01:00"}


@pytest.mark.asyncio
@pytest.mark.parametrize("compte", ["imap", "gmail", None])
async def test_occurrence_creee_par_api_independante_du_courrier(client, db_session, monkeypatch, compte):
    await _agenda(db_session, compte)
    distant = AsyncMock(side_effect=AssertionError("Le local ne contacte aucun fournisseur"))
    monkeypatch.setattr("app.routers.email.ensure_valid_access_token", distant)
    cree = await client.post("/api/calendar/events", json={
        "calendar_id": "local", "summary": "Revue veille subventions",
        "start_datetime": "2026-10-19T10:00:00+02:00",
        "end_datetime": "2026-10-19T11:00:00+02:00",
        "recurrence": ["RRULE:FREQ=WEEKLY;BYDAY=MO"],
    })
    assert cree.status_code == 200, cree.text
    resultat = await _list_calendar_events(_periode(), db_session)
    assert "26/10 10:00-11:00" in resultat, resultat
    assert "Revue veille subventions" in resultat
    assert "19/10" not in resultat
    assert "02/11" not in resultat
    distant.assert_not_awaited()


@pytest.mark.asyncio
async def test_selection_non_principale_et_bornes_exclusives(db_session):
    await _agenda(db_session)
    db_session.add(Calendar(id="autre", summary="Principal", provider="local", primary=True))
    for ident, agenda, debut in [
        ("avant", "local", datetime(2026, 10, 25, 23, 59)),
        ("dedans", "local", datetime(2026, 10, 26)),
        ("fin", "local", datetime(2026, 11, 2)),
        ("ailleurs", "autre", datetime(2026, 10, 27)),
    ]:
        db_session.add(CalendarEvent(id=ident, calendar_id=agenda, summary=ident, start_datetime=debut))
    await db_session.commit()
    poser_ecran(email_account_id="courrier", calendar_id="local")
    resultat = await _list_calendar_events(_periode(), db_session)
    assert "dedans" in resultat, resultat
    assert all(nom not in resultat for nom in ("avant", "ailleurs", "— fin")), resultat


@pytest.mark.asyncio
async def test_periode_locale_vide_ne_suggere_aucune_synchro(db_session):
    await _agenda(db_session)
    resultat = await _list_calendar_events(_periode(), db_session)
    assert "local" in resultat.lower(), resultat
    assert "synchro" not in resultat.lower(), resultat
    assert "caldav" not in resultat.lower()


@pytest.mark.asyncio
async def test_erreur_locale_ne_suggere_aucune_synchro(db_session, monkeypatch):
    await _agenda(db_session)
    monkeypatch.setattr("app.services.calendar.local_provider.LocalCalendarProvider.list_events", AsyncMock(side_effect=ValueError("lecture impossible")))
    resultat = await _list_calendar_events(_periode(), db_session)
    assert "local" in resultat.lower(), resultat
    assert "synchro" not in resultat.lower(), resultat


@pytest.mark.asyncio
async def test_periode_inversee_est_expliquee(db_session):
    await _agenda(db_session)
    resultat = await _list_calendar_events({"time_min": "2026-11-02T00:00:00Z", "time_max": "2026-10-26T00:00:00Z"}, db_session)
    assert "période invalide" in resultat.lower(), resultat


# Entrées inventées après le correctif : règles, exclusions et fuseaux variés.
@pytest.mark.asyncio
@pytest.mark.parametrize("souche,regles,debut,fin,attendus,journee", [
    ("2026-10-19T10:00", ["FREQ=WEEKLY;BYDAY=MO"], "2026-10-26T00:00+01:00", "2026-11-02T00:00+01:00", ["2026-10-26T10:00:00"], False),
    ("2026-10-19T10:00", ["RRULE:FREQ=DAILY;COUNT=3"], "2026-10-20T00:00Z", "2026-10-23T00:00Z", ["2026-10-20T10:00:00", "2026-10-21T10:00:00"], False),
    ("2026-10-19T10:00", ["RRULE:FREQ=WEEKLY;INTERVAL=2;BYDAY=MO"], "2026-10-20T00:00Z", "2026-11-03T00:00Z", ["2026-11-02T10:00:00"], False),
    ("2026-08-31T10:00", ["RRULE:FREQ=MONTHLY;BYMONTHDAY=31"], "2026-10-20T00:00Z", "2027-01-02T00:00Z", ["2026-10-31T10:00:00", "2026-12-31T10:00:00"], False),
    ("2024-02-29T10:00", ["RRULE:FREQ=YEARLY"], "2028-02-28T00:00Z", "2028-03-01T00:00Z", ["2028-02-29T10:00:00"], False),
    ("2026-10-19T10:00", ["RRULE:FREQ=WEEKLY;UNTIL=20261026T090000Z"], "2026-10-20T00:00Z", "2026-11-03T00:00Z", ["2026-10-26T10:00:00"], False),
    ("2026-10-19T10:00", ["RRULE:FREQ=WEEKLY", "EXDATE;TZID=Europe/Paris:20261026T100000"], "2026-10-20T00:00Z", "2026-11-03T00:00Z", ["2026-11-02T10:00:00"], False),
    ("2026-10-19T10:00", ["RRULE:FREQ=WEEKLY", "RDATE;TZID=Europe/Paris:20261027T100000"], "2026-10-26T00:00Z", "2026-10-28T00:00Z", ["2026-10-26T10:00:00", "2026-10-27T10:00:00"], False),
    ("2026-10-19T00:00", ["RRULE:FREQ=DAILY;COUNT=3"], "2026-10-20T00:00+02:00", "2026-10-22T00:00+02:00", ["2026-10-20", "2026-10-21"], True),
    ("2026-10-19T10:00", ["RRULE:FREQ=WEEKLY"], "2026-10-26T05:00-04:00", "2026-10-26T06:00-04:00", ["2026-10-26T10:00:00"], False),
])
async def test_rejeu_dix_entrees(db_session, souche, regles, debut, fin, attendus, journee):
    from app.services.calendar.local_provider import LocalCalendarProvider

    await _agenda(db_session)
    depart = datetime.fromisoformat(souche)
    db_session.add(CalendarEvent(
        id="serie", calendar_id="local", summary="Série de rejeu", all_day=journee,
        start_datetime=None if journee else depart,
        start_date=depart.date().isoformat() if journee else None,
        recurrence=json.dumps(regles),
    ))
    await db_session.commit()
    events, _ = await LocalCalendarProvider(db_session).list_events(
        "local", datetime.fromisoformat(debut), datetime.fromisoformat(fin), expand_recurring=True,
    )
    assert [e.start.isoformat() for e in events] == attendus


@pytest.mark.asyncio
async def test_occurrences_paginees_et_cloisonnees(db_session):
    from app.services.calendar.local_provider import LocalCalendarProvider

    await _agenda(db_session)
    # Un projet absent ne doit pas être requis : les événements anciens sans
    # dossier restent visibles, ceux d'un autre dossier restent exclus.
    from app.models.entities import Project

    db_session.add(Project(id="autre-projet", name="Autre dossier"))
    for ident, projet in [("visible", None), ("cache", "autre-projet")]:
        db_session.add(CalendarEvent(
            id=ident, calendar_id="local", summary=ident, project_id=projet,
            start_datetime=datetime(2026, 10, 19, 10),
            recurrence='["RRULE:FREQ=DAILY;COUNT=20"]',
        ))
    await db_session.commit()
    provider = LocalCalendarProvider(db_session)
    vus, jeton = [], None
    while True:
        events, jeton = await provider.list_events(
            "local", datetime(2026, 10, 26), datetime(2026, 11, 2),
            max_results=2, page_token=jeton, project_id="courant", expand_recurring=True,
        )
        vus.extend(events)
        if jeton is None:
            break
    assert len(vus) == 7
    assert all(e.id == "visible" for e in vus)
    assert len({e.start for e in vus}) == 7


@pytest.mark.asyncio
@pytest.mark.parametrize("regles", [None, '["RRULE:FREQ=DAILY"]'])
async def test_journee_entiere_visible_meme_apres_minuit(db_session, regles):
    from app.services.calendar.local_provider import LocalCalendarProvider

    await _agenda(db_session)
    db_session.add(CalendarEvent(
        id="journee", calendar_id="local", summary="Salon", all_day=True,
        start_date="2026-10-26", end_date="2026-10-26", recurrence=regles,
    ))
    await db_session.commit()
    events, _ = await LocalCalendarProvider(db_session).list_events(
        "local", datetime(2026, 10, 26, 14), datetime(2026, 10, 27), expand_recurring=True,
    )
    assert [e.start.isoformat() for e in events] == ["2026-10-26"]


@pytest.mark.asyncio
@pytest.mark.parametrize("regles,jours", [
    (["RRULE:FREQ=DAILY;UNTIL=20261028"], [26, 27, 28]),
    (["RRULE:FREQ=DAILY;COUNT=10", "EXDATE;VALUE=DATE:20261026"], [27, 28]),
])
async def test_dates_ics_creees_par_api_restent_lisibles(client, db_session, regles, jours):
    await _agenda(db_session)
    for evenement in [
        {"summary": "Séjour", "start_date": "2026-10-19", "end_date": "2026-10-19", "recurrence": regles},
        {"summary": "Rendez-vous indépendant", "start_datetime": "2026-10-27T15:00:00+01:00", "end_datetime": "2026-10-27T16:00:00+01:00"},
    ]:
        cree = await client.post("/api/calendar/events", json={"calendar_id": "local", **evenement})
        assert cree.status_code == 200, cree.text
    resultat = await _list_calendar_events(_periode(), db_session)
    assert "Rendez-vous indépendant" in resultat, resultat
    assert "27/10 15:00-16:00" in resultat
    for jour in range(26, 32):
        assert (f"{jour}/10 (journee)" in resultat) == (jour in jours), resultat


@pytest.mark.asyncio
@pytest.mark.parametrize("independant", [True, False])
async def test_serie_illisible_signalee_sans_masquer_les_autres(client, db_session, independant):
    await _agenda(db_session)
    for evenement in [
        {"summary": "Série illisible", "start_date": "2026-10-19", "end_date": "2026-10-19", "recurrence": ["RRULE:FREQ=INCONNUE"]},
        {"summary": "Rendez-vous indépendant", "start_datetime": "2026-10-27T15:00:00+01:00", "end_datetime": "2026-10-27T16:00:00+01:00"},
    ]:
        if evenement["summary"] == "Rendez-vous indépendant" and not independant:
            continue
        cree = await client.post("/api/calendar/events", json={"calendar_id": "local", **evenement})
        assert cree.status_code == 200, cree.text
    resultat = await _list_calendar_events(_periode(), db_session)
    assert ("Rendez-vous indépendant" in resultat) == independant, resultat
    assert "Série illisible" in resultat
    assert "ignoré" in resultat.lower()
    assert "période est vide" not in resultat


@pytest.mark.asyncio
@pytest.mark.parametrize("journee", [False, True])
@pytest.mark.parametrize("exclure_depart", [False, True])
async def test_rdate_seul_inclut_dtstart_avant_exclusions(client, db_session, journee, exclure_depart):
    await _agenda(db_session)
    if journee:
        dates = {"start_date": "2026-10-26", "end_date": "2026-10-26"}
        regles = ["RDATE;VALUE=DATE:20261027"]
        exclusion = "EXDATE;VALUE=DATE:20261026"
    else:
        dates = {"start_datetime": "2026-10-26T10:00:00+01:00", "end_datetime": "2026-10-26T11:00:00+01:00"}
        regles = ["RDATE;TZID=Europe/Paris:20261027T100000"]
        exclusion = "EXDATE:20261026T100000"
    if exclure_depart:
        regles.append(exclusion)
    cree = await client.post("/api/calendar/events", json={
        "calendar_id": "local", "summary": "RDATE seul", **dates, "recurrence": regles,
    })
    assert cree.status_code == 200, cree.text
    resultat = await _list_calendar_events(_periode(), db_session)
    assert ("26/10" in resultat) == (not exclure_depart), resultat
    assert "27/10" in resultat, resultat
    assert resultat.count("RDATE seul") == (1 if exclure_depart else 2)


@pytest.mark.asyncio
@pytest.mark.parametrize(("journee", "exclusion"), [
    (False, "EXDATE;VALUE=DATE:20261027"),
    (True, "EXDATE;VALUE=DATE:20261027"),
    (False, "EXDATE;VALUE=DATE:20261026"),
])
async def test_exclusion_date_seule_garde_dtstart(client, db_session, journee, exclusion):
    # Réserve d'Astra (c19 v3) : une série faite d'une seule exclusion DATE
    # laissait la liste de règles vide, et le départ devenait illisible.
    await _agenda(db_session)
    if journee:
        dates = {"start_date": "2026-10-26", "end_date": "2026-10-26"}
    else:
        dates = {"start_datetime": "2026-10-26T10:00:00+01:00", "end_datetime": "2026-10-26T11:00:00+01:00"}
    cree = await client.post("/api/calendar/events", json={
        "calendar_id": "local", "summary": "Exclusion seule", **dates, "recurrence": [exclusion],
    })
    assert cree.status_code == 200, cree.text
    resultat = await _list_calendar_events(_periode(), db_session)
    assert "illisible" not in resultat.lower(), resultat
    depart_exclu = exclusion.endswith("20261026")
    assert ("26/10" in resultat) == (not depart_exclu), resultat
    assert resultat.count("Exclusion seule") == (0 if depart_exclu else 1), resultat


@pytest.mark.parametrize("regles", [
    ["RRULE:FREQ=MINUTELY"],
    ["RRULE:FREQ=MINUTELY;BYMONTH=2;BYMONTHDAY=30"],
    ["RRULE:FREQ=DAILY", "EXRULE:FREQ=DAILY"],
])
def test_ancienne_serie_dense_ou_sans_resultat_a_un_cout_borne(regles):
    # Le sous-processus protège aussi l'exécution rouge d'un calcul qui ne
    # rendrait jamais la main ; aucun fournisseur externe n'est appelé.
    import subprocess
    import sys
    import textwrap

    code = textwrap.dedent(f"""
        import sys
        from datetime import datetime
        sys.path.insert(0, 'src/backend')
        from app.services.calendar.base_provider import CalendarEventDTO
        from app.services.calendar.local_provider import _occurrences_locales
        evenement = CalendarEventDTO(id='dense', calendar_id='local', summary='dense',
            start=datetime(2020, 1, 1, 9), recurrence={regles!r})
        try:
            _occurrences_locales(evenement, datetime(2026, 10, 26, 9), datetime(2026, 10, 26, 10), 1)
        except ValueError as exc:
            print(str(exc))
    """)
    resultat = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=15)
    assert resultat.returncode == 0, resultat.stderr
    assert "limite de calcul" in resultat.stdout.lower(), resultat.stdout


@pytest.mark.asyncio
async def test_developpement_local_hors_de_la_boucle_du_moteur(db_session, monkeypatch):
    import threading

    from app.services.calendar import local_provider

    await _agenda(db_session)
    db_session.add(CalendarEvent(
        id="serie", calendar_id="local", summary="Série", start_datetime=datetime(2026, 10, 26, 9),
        recurrence='["RRULE:FREQ=DAILY;COUNT=2"]',
    ))
    await db_session.commit()
    fil_moteur = threading.get_ident()
    fils_calcul = []
    original = local_provider._occurrences_locales

    def observer(*args):
        fils_calcul.append(threading.get_ident())
        return original(*args)

    monkeypatch.setattr(local_provider, "_occurrences_locales", observer)
    evenements, _ = await local_provider.LocalCalendarProvider(db_session).list_events(
        "local", datetime(2026, 10, 26), datetime(2026, 10, 28), expand_recurring=True,
    )
    assert len(evenements) == 2
    assert fils_calcul and all(fil != fil_moteur for fil in fils_calcul)


@pytest.mark.asyncio
async def test_ancienne_serie_dense_signalee_et_rendez_vous_independant_rendu(client, db_session):
    await _agenda(db_session)
    for evenement in [
        {"summary": "Ancienne série dense", "start_datetime": "2020-01-01T09:00:00+01:00", "end_datetime": "2020-01-01T09:01:00+01:00", "recurrence": ["RRULE:FREQ=MINUTELY"]},
        {"summary": "Rendez-vous indépendant", "start_datetime": "2026-10-27T15:00:00+01:00", "end_datetime": "2026-10-27T16:00:00+01:00"},
    ]:
        cree = await client.post("/api/calendar/events", json={"calendar_id": "local", **evenement})
        assert cree.status_code == 200, cree.text
    resultat = await _list_calendar_events(_periode(), db_session)
    assert "27/10 15:00-16:00" in resultat, resultat
    assert "Rendez-vous indépendant" in resultat
    assert "Ancienne série dense" in resultat
    assert "limite de calcul" in resultat.lower()
    assert "1 evenement(s)" in resultat
