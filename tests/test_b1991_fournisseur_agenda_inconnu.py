"""B-1991 : un fournisseur inconnu ne doit pas être présenté comme Google."""

from datetime import UTC, datetime, timedelta

from app.models.entities import Calendar


async def test_b1991_creer_sur_un_fournisseur_inconnu_explique_le_refus(client, db_session):
    agenda = Calendar(summary="Agenda de test", provider="inconnu")
    db_session.add(agenda)
    await db_session.commit()
    debut = datetime.now(UTC) + timedelta(days=1)

    reponse = await client.post(
        "/api/calendar/events",
        json={
            "calendar_id": agenda.id,
            "summary": "Rendez-vous de test",
            "start_datetime": debut.isoformat(),
            "end_datetime": (debut + timedelta(hours=1)).isoformat(),
        },
    )

    assert reponse.status_code == 400
    assert reponse.json()["message"] == "Ce fournisseur d’agenda n’est pas pris en charge."
