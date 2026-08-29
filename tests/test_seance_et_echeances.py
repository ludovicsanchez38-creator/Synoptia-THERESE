"""
E2, E3, E4 : la séance bloquée, le questionnaire à froid, l'encaissement.

Trois objets que les notes de Ludo décrivent et qu'aucune surface ne portait.
Chacun est traité avec la retenue que la revue impose : un état sur ce qui
existe déjà, jamais une table de plus.

- E2 : « l'OPCO écrit de ne pas maintenir la séance du 24 » n'est pas
  `cancelled`. C'est un état sur l'événement d'agenda, pas une table Séance
  à côté des 429 événements existants.
- E3 : le J+90 court depuis la FIN de formation. Sans date de fin posée, on
  ne calcule rien — on ne devine pas une échéance réglementaire.
- E4 : l'encaissement partiel attend une VRAIE facture. Étendre le statut sur
  zéro facture serait un moteur à vide.
"""
from datetime import date

import pytest
from app.models.entities import CalendarEvent
from app.services.echeances import echeance_du_questionnaire_a_froid
from sqlalchemy.ext.asyncio import AsyncSession

# --- E2 : une séance peut être bloquée ---------------------------------------

@pytest.mark.asyncio
async def test_un_evenement_peut_etre_bloque_sans_etre_annule(db_session: AsyncSession):
    """« Bloqué » et « annulé » ne disent pas la même chose.

    Annulé : ça n'aura pas lieu. Bloqué : ça ne peut pas avoir lieu EN L'ÉTAT,
    et il y a quelque chose à faire pour le débloquer.
    """
    e = CalendarEvent(
        id="ev-1", calendar_id="cal-1", summary="Séance 2 PROPULSER", status="confirmed",
        blocage="Attestation fiscale non transmise (Atlas, 20/08)",
    )
    db_session.add(e)
    await db_session.commit()

    assert e.status == "confirmed", "le blocage ne doit pas annuler l'événement"
    assert "Attestation" in e.blocage


async def _evenement(session: AsyncSession, **kw) -> CalendarEvent:
    e = CalendarEvent(id=kw.pop("id", "ev-test"), calendar_id="cal-1",
                      summary="Séance 2 PROPULSER", status="confirmed", **kw)
    session.add(e)
    await session.commit()
    return e


@pytest.mark.asyncio
async def test_un_blocage_dit_toujours_pourquoi(client, db_session: AsyncSession):
    """Un booléen « bloqué » sans motif obligerait Ludo à se souvenir."""
    await _evenement(db_session, id="ev-motif")

    reponse = await client.patch("/api/calendar/events/ev-motif/blocage", json={"blocage": "   "})

    assert reponse.status_code == 400, reponse.text
    assert (await client.patch(
        "/api/calendar/events/inexistant/blocage", json={"blocage": "x"}
    )).status_code == 404


@pytest.mark.asyncio
async def test_bloquer_ne_supprime_pas_la_seance(client, db_session: AsyncSession):
    """Le piège : traiter « bloqué » comme « annulé » ferait disparaître la
    séance de l'agenda, alors qu'elle doit rester à sa date le temps qu'on
    débloque."""
    await _evenement(db_session, id="ev-bloque")

    reponse = await client.patch("/api/calendar/events/ev-bloque/blocage",
                                 json={"blocage": "Attestation fiscale manquante (Atlas)"})

    assert reponse.status_code == 200, reponse.text
    assert reponse.json()["status"] == "confirmed", "bloqué n'est pas annulé"
    assert "Attestation" in reponse.json()["blocage"]


@pytest.mark.asyncio
async def test_lever_un_blocage(client, db_session: AsyncSession):
    await _evenement(db_session, id="ev-libere", blocage="Attestation manquante")

    reponse = await client.patch("/api/calendar/events/ev-libere/blocage",
                                 json={"blocage": None})

    assert reponse.status_code == 200, reponse.text
    assert reponse.json()["blocage"] is None


# --- E3 : le questionnaire à froid -------------------------------------------

def test_le_j90_court_depuis_la_fin_de_formation():
    fin = date(2026, 6, 1)
    assert echeance_du_questionnaire_a_froid(fin) == date(2026, 8, 30)


def test_sans_date_de_fin_on_ne_calcule_rien():
    """Deviner une échéance réglementaire serait l'inventer.

    Le J+90 est un indicateur Qualiopi : une date fausse est pire que pas de
    date.
    """
    assert echeance_du_questionnaire_a_froid(None) is None


@pytest.mark.asyncio
async def test_la_prestation_porte_sa_date_de_fin(client):
    fiche = (await client.post(
        "/api/memory/contacts", json={"first_name": "Fin", "last_name": "Formation"}
    )).json()
    p = (await client.post("/api/prestations", json={
        "contact_id": fiche["id"], "intitule": "PROPULSER", "phase": "en_cours",
    })).json()

    maj = await client.patch(f"/api/prestations/{p['id']}", json={"fin_le": "2026-06-01"})

    assert maj.status_code == 200, maj.text
    assert maj.json()["fin_le"] == "2026-06-01"
    assert maj.json()["questionnaire_a_froid_le"] == "2026-08-30", (
        "l'échéance se DÉDUIT de la date de fin, elle ne se saisit pas deux fois"
    )


@pytest.mark.asyncio
async def test_sans_fin_posee_la_prestation_n_annonce_pas_d_echeance(client):
    fiche = (await client.post(
        "/api/memory/contacts", json={"first_name": "Sans", "last_name": "Fin"}
    )).json()
    p = (await client.post("/api/prestations", json={
        "contact_id": fiche["id"], "intitule": "FORGER",
    })).json()

    assert p["fin_le"] is None
    assert p["questionnaire_a_froid_le"] is None
