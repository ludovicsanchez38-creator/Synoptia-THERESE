"""B-196 - import du MEME fichier .ics dans deux calendriers differents.

La garde anti-doublon de `import_ics_file` filtre par calendrier
(`calendar_id == cal.id ET id == uid`), mais l'UID du fichier devenait la
CLE PRIMAIRE GLOBALE de `calendar_events` : ranger la meme invitation dans
deux agendas - ou dupliquer un agenda - sortait en 500 sur un
`UNIQUE constraint failed: calendar_events.id`. Corollaire : l'export .ics
de l'application n'etait pas reimportable par sa propre route, puisqu'il
ecrit l'identifiant interne de chaque evenement en UID.
"""

import pytest
from httpx import AsyncClient

_ICS = (
    "BEGIN:VCALENDAR\r\n"
    "VERSION:2.0\r\n"
    "PRODID:-//Therese//Test//FR\r\n"
    "BEGIN:VEVENT\r\n"
    "UID:rb2-uid-unique-001\r\n"
    "DTSTART:20260910T090000Z\r\n"
    "DTEND:20260910T100000Z\r\n"
    "SUMMARY:Reunion partagee\r\n"
    "END:VEVENT\r\n"
    "END:VCALENDAR\r\n"
)


async def _creer_calendrier(client: AsyncClient, nom: str) -> str:
    reponse = await client.post(
        "/api/calendar/calendars",
        json={"summary": nom, "provider_type": "local"},
    )
    assert reponse.status_code == 200, reponse.text
    return reponse.json()["id"]


async def _importer(client: AsyncClient, calendar_id: str) -> dict:
    reponse = await client.post(
        f"/api/calendar/import-ics?calendar_id={calendar_id}",
        files={"file": ("one.ics", _ICS.encode(), "text/calendar")},
    )
    assert reponse.status_code == 200, reponse.text
    return reponse.json()


class TestB196ImportIcsDansDeuxCalendriers:
    @pytest.mark.asyncio
    async def test_meme_fichier_dans_deux_calendriers(self, client: AsyncClient):
        cal_a = await _creer_calendrier(client, "Agenda A")
        cal_b = await _creer_calendrier(client, "Agenda B")

        assert (await _importer(client, cal_a))["imported"] == 1
        # Le geste courant : la meme invitation rangee dans un second agenda.
        assert (await _importer(client, cal_b))["imported"] == 1

        for cal in (cal_a, cal_b):
            liste = await client.get(f"/api/calendar/events?calendar_id={cal}")
            assert liste.status_code == 200, liste.text
            evenements = liste.json()
            assert len(evenements) == 1, f"{cal} : {evenements}"
            assert evenements[0]["summary"] == "Reunion partagee"

    @pytest.mark.asyncio
    async def test_la_garde_anti_doublon_tient_dans_chaque_calendrier(
        self, client: AsyncClient
    ):
        cal_a = await _creer_calendrier(client, "Agenda A")
        cal_b = await _creer_calendrier(client, "Agenda B")

        await _importer(client, cal_a)
        await _importer(client, cal_b)

        # Re-import du MEME fichier : rien de nouveau, dans l'un comme dans l'autre.
        assert (await _importer(client, cal_a))["skipped"] == 1
        assert (await _importer(client, cal_b))["skipped"] == 1

        for cal in (cal_a, cal_b):
            liste = await client.get(f"/api/calendar/events?calendar_id={cal}")
            assert len(liste.json()) == 1

    @pytest.mark.asyncio
    async def test_export_ics_est_reimportable_ailleurs(self, client: AsyncClient):
        """L'export de l'application ecrit l'id interne en UID : sa propre
        route d'import doit savoir l'accueillir dans un autre agenda."""
        cal_a = await _creer_calendrier(client, "Agenda A")
        cal_b = await _creer_calendrier(client, "Agenda B")
        await _importer(client, cal_a)

        export = await client.get(f"/api/calendar/export-ics?calendar_id={cal_a}")
        assert export.status_code == 200, export.text

        reponse = await client.post(
            f"/api/calendar/import-ics?calendar_id={cal_b}",
            files={"file": ("export.ics", export.content, "text/calendar")},
        )
        assert reponse.status_code == 200, reponse.text
        assert reponse.json()["imported"] == 1

    @pytest.mark.asyncio
    async def test_les_deux_identifiants_candidats_coexistants_ne_font_pas_tomber_la_garde(
        self, client: AsyncClient, db_session
    ):
        """La garde cherche DEUX identifiants : elle doit encaisser les deux.

        Elargir la recherche sans elargir la lecture du resultat aurait fait
        lever `MultipleResultsFound` a une garde dont le seul travail est de
        dire « ca existe deja » - la regression que la remediation aurait
        introduite elle-meme. Aucune route ne fabrique cette paire (l'id derive
        n'est pose que si l'UID nu est deja pris ailleurs), d'ou l'ecriture
        directe en base, seul moyen de construire le cas.
        """
        from datetime import UTC, datetime

        from app.models.entities import CalendarEvent
        from app.routers.calendar import _id_evenement_importe

        cal_a = await _creer_calendrier(client, "Agenda A")
        uid = "rb2-uid-unique-001"

        for identifiant in (uid, _id_evenement_importe(cal_a, uid)):
            db_session.add(
                CalendarEvent(
                    id=identifiant,
                    calendar_id=cal_a,
                    summary="Reunion partagee",
                    start_datetime=datetime(2026, 9, 10, 9, 0, tzinfo=UTC),
                    end_datetime=datetime(2026, 9, 10, 10, 0, tzinfo=UTC),
                )
            )
        await db_session.commit()

        assert (await _importer(client, cal_a))["skipped"] == 1
