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
from app.services.echeances import DELAI_PAR_DEFAUT_JOURS, echeance_de_suivi
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

def test_le_suivi_court_depuis_la_fin_de_la_prestation():
    fin = date(2026, 6, 1)
    assert echeance_de_suivi(fin) == date(2026, 8, 30)


def test_le_delai_est_parametrable():
    """90 jours est le J+90 Qualiopi d'un organisme de formation. Un garagiste
    rappelle peut-être à 30 jours, un architecte à un an. Le délai est un
    réglage, pas une loi de l'application."""
    fin = date(2026, 6, 1)

    assert echeance_de_suivi(fin, jours=30) == date(2026, 7, 1)
    assert DELAI_PAR_DEFAUT_JOURS == 90


def test_un_delai_absurde_est_refuse():
    with pytest.raises(ValueError):
        echeance_de_suivi(date(2026, 6, 1), jours=0)


def test_sans_date_de_fin_on_ne_calcule_rien():
    """Deviner une échéance serait l'inventer, et pour un organisme de
    formation c'est un indicateur réglementaire : une date fausse est pire
    qu'une date absente."""
    assert echeance_de_suivi(None) is None


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
    assert maj.json()["suivi_apres_fin_le"] == "2026-08-30", (
        "l'échéance se DÉDUIT de la date de fin, elle ne se saisit pas deux fois"
    )


@pytest.mark.asyncio
async def test_sans_fin_posee_la_prestation_n_annonce_pas_d_echeance(client):
    fiche = (await client.post(
        "/api/memory/contacts", json={"first_name": "Sans", "last_name": "Fin"}
    )).json()
    p = (await client.post("/api/prestations", json={
        "contact_id": fiche["id"], "intitule": "FORGER", "phase": "piste",
    })).json()

    assert p["fin_le"] is None
    assert p["suivi_apres_fin_le"] is None


@pytest.mark.asyncio
async def test_le_delai_de_suivi_se_regle_vraiment(client):
    """Un réglage qu'on ne peut pas régler n'est pas un réglage.

    Trouvé par un persona artisan sur la 0.59.0 : « 90 jours, ça ne veut rien
    dire pour moi, et ce n'est pas réglable depuis ce que j'ai sous la main ».
    Après une fuite il rappelle à 8 jours, après une chaudière à un an.

    C'est le défaut de `next_follow_up` corrigé le matin même, réintroduit le
    soir : un bouton qui existe dans le code et que personne ne peut tourner.
    """
    fiche = (await client.post(
        "/api/memory/contacts", json={"first_name": "Sylvie", "last_name": "Morel"}
    )).json()

    p = (await client.post("/api/prestations", json={
        "contact_id": fiche["id"], "intitule": "Fuite lavabo", "phase": "en_cours",
        "fin_le": "2026-09-13", "suivi_apres_jours": 8,
    })).json()

    assert p["suivi_apres_jours"] == 8
    assert p["suivi_apres_fin_le"] == "2026-09-21", "8 jours après le 13/09"

    maj = await client.patch(f"/api/prestations/{p['id']}", json={"suivi_apres_jours": 365})
    assert maj.json()["suivi_apres_fin_le"] == "2027-09-13", "un an après"


@pytest.mark.asyncio
async def test_le_delai_utilise_est_toujours_dit(client):
    """Si l'application applique 90 jours par défaut, elle doit le MONTRER.

    Un défaut invisible est une affirmation cachée.
    """
    fiche = (await client.post(
        "/api/memory/contacts", json={"first_name": "Defaut", "last_name": "Visible"}
    )).json()

    p = (await client.post("/api/prestations", json={
        "contact_id": fiche["id"], "intitule": "Chaudiere", "phase": "en_cours",
        "fin_le": "2026-09-13",
    })).json()

    assert p["suivi_apres_jours"] == 90, "le délai appliqué doit être lisible"


@pytest.mark.asyncio
async def test_l_application_ne_choisit_pas_la_phase_a_ta_place(client):
    """« Une fuite sous un lavabo n'est pas une piste. C'est un client qui a de
    l'eau par terre et qui m'appelle. »

    Sans phase fournie, l'application posait `piste` toute seule : elle
    affirmait une étape commerciale que personne n'avait choisie.
    """
    fiche = (await client.post(
        "/api/memory/contacts", json={"first_name": "Sans", "last_name": "Phase"}
    )).json()

    reponse = await client.post("/api/prestations", json={
        "contact_id": fiche["id"], "intitule": "Depannage",
    })

    assert reponse.status_code in (400, 422), reponse.text


@pytest.mark.asyncio
async def test_un_blocage_survit_a_la_relecture(client, db_session: AsyncSession):
    """La chaîne, pas une surface.

    Trouvé par un persona avocate : « le serveur a répondu avec le motif, puis
    j'ai relu l'événement et la liste : le blocage a disparu. L'audience est
    toujours confirmée. Si je m'en remets à l'agenda demain matin, je me
    présente au tribunal pour une audience qui n'existe plus. »

    Le champ était posé sur la route d'écriture et absent du schéma de lecture.
    C'est le motif des jumeaux : une règle sur un chemin, pas balayée sur les
    autres.
    """
    await _evenement(db_session, id="ev-audience")

    pose = await client.patch("/api/calendar/events/ev-audience/blocage",
                              json={"blocage": "Greffe : audience renvoyée, date non communiquée"})
    assert pose.status_code == 200, pose.text

    relu = await client.get(
        "/api/calendar/events/ev-audience?calendar_id=cal-1&account_id=local"
    )
    assert relu.status_code == 200, relu.text
    assert "Greffe" in (relu.json().get("blocage") or ""), (
        "un blocage qui disparaît à la relecture est pire que pas de blocage"
    )
