"""Passe 3 : alias Google, sélection SQL et cache, avec SQLite en mémoire."""

import json
from copy import deepcopy
from unittest.mock import AsyncMock

import httpx
import pytest
from app.models.database import get_session
from app.models.entities import Calendar, CalendarEvent, EmailAccount, Project
from app.routers import calendar as agenda
from app.services import calendar_service
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlmodel import SQLModel, select


@pytest.fixture
async def agenda_memoire(monkeypatch):
    moteur = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with moteur.begin() as connexion:
        await connexion.run_sync(SQLModel.metadata.create_all)
    async with AsyncSession(moteur, expire_on_commit=False) as session:
        compte = EmailAccount(id="compte", email="agenda@example.test", provider="gmail")
        autre = EmailAccount(id="autre", email="autre@example.test", provider="gmail")
        historique = Calendar(id="primary", summary="Historique", provider="inconnu", account_id=compte.id)
        dossier = Project(id="dossier", name="Dossier historique")
        session.add_all([compte, autre, historique, dossier])
        await session.commit()
        distant = {
            "id": "rendez-vous", "summary": "Titre Google", "status": "confirmed",
            "start": {"date": "2026-12-01"}, "end": {"date": "2026-12-02"},
        }
        appels = []

        def google(requete):
            chemin = requete.url.path
            appels.append((requete.method, chemin))
            if requete.method == "GET" and chemin.endswith("/calendars/primary"):
                return httpx.Response(200, json={"id": compte.email, "summary": "Principal Google"})
            prefixe = "/calendar/v3/calendars/"
            for destination in ("primary", compte.email):
                collection = f"{prefixe}{destination}/events"
                if chemin == collection:
                    if requete.method == "POST":
                        distant.update(json.loads(requete.content))
                        return httpx.Response(200, json=distant)
                    if requete.method == "GET":
                        return httpx.Response(200, json={"items": [distant]})
                if chemin == f"{collection}/{distant['id']}":
                    if requete.method == "GET":
                        return httpx.Response(200, json=distant)
                    if requete.method == "PUT":
                        distant.update(json.loads(requete.content))
                        return httpx.Response(200, json=distant)
                    if requete.method == "DELETE":
                        return httpx.Response(204)
            raise AssertionError(f"Appel inattendu : {requete.method} {chemin}")

        api = FastAPI()
        api.include_router(agenda.router, prefix="/api/calendar")

        async def session_de_test():
            yield session

        api.dependency_overrides[get_session] = session_de_test
        monkeypatch.setattr(agenda, "ensure_valid_access_token", AsyncMock(return_value="jeton-factice"))
        async with httpx.AsyncClient(transport=httpx.MockTransport(google)) as transport:
            monkeypatch.setattr(calendar_service, "get_http_client", AsyncMock(return_value=transport))
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=api), base_url="http://test") as client:
                yield client, session, compte, historique, distant, appels
    await moteur.dispose()


async def test_r3_historique_primary_relu_sans_changer_de_dossier(agenda_memoire):
    client, session, compte, historique, distant, _ = agenda_memoire
    evenement = CalendarEvent(
        id=distant["id"], calendar_id="primary", project_id="dossier", summary="Ancien titre",
        reminders="[15]", blocage="Attendre la confirmation",
    )
    session.add(evenement)
    await session.commit()

    for destination in ("primary", compte.email):
        reponse = await client.get("/api/calendar/events", params={
            "calendar_id": destination, "account_id": compte.id,
        })
        assert reponse.status_code == 200, reponse.text
        assert [evt["id"] for evt in reponse.json()] == [evenement.id]
        assert reponse.json()[0]["calendar_id"] == compte.email
    await session.refresh(evenement)
    assert (evenement.calendar_id, evenement.summary) == (compte.email, "Titre Google")
    assert (evenement.project_id, evenement.reminders, evenement.blocage) == (
        "dossier", "[15]", "Attendre la confirmation",
    )
    assert len((await session.execute(select(CalendarEvent))).scalars().all()) == 1
    await session.refresh(historique)
    assert (historique.provider, historique.account_id, historique.summary) == ("inconnu", compte.id, "Historique")


@pytest.mark.parametrize("source,compte_source", [
    ("primary", "autre"), ("primary", None), ("agenda-voisin", "compte"),
])
async def test_r3_reconciliation_ne_deplace_pas_un_evenement_ambigu(
    agenda_memoire, source, compte_source,
):
    client, session, compte, historique, distant, _ = agenda_memoire
    historique.account_id = compte_source
    if source != "primary":
        session.add(Calendar(id=source, summary="Voisin", provider="google", account_id=compte_source))
    evenement = CalendarEvent(id=distant["id"], calendar_id=source, summary="À conserver", project_id="dossier")
    session.add(evenement)
    await session.commit()
    await session.refresh(evenement)
    avant = deepcopy(evenement.model_dump())

    reponse = await client.get("/api/calendar/events", params={"account_id": compte.id})

    assert reponse.status_code == 200, reponse.text
    assert reponse.json() == []
    await session.refresh(evenement)
    assert evenement.model_dump() == avant


@pytest.mark.parametrize("methode,chemin", [
    ("GET", "/events"), ("GET", "/events/rendez-vous"),
    ("PUT", "/events/rendez-vous"), ("DELETE", "/events/rendez-vous"),
])
@pytest.mark.parametrize("avec_compte", [False, True])
async def test_r3_selection_primary_inconnue_refusee_sur_toutes_les_operations(
    agenda_memoire, methode, chemin, avec_compte,
):
    client, session, compte, _, distant, appels = agenda_memoire
    session.add(Calendar(id=compte.email, summary="Google", provider="google", account_id=compte.id))
    evenement = CalendarEvent(id=distant["id"], calendar_id=compte.email, summary="À conserver")
    session.add(evenement)
    await session.commit()
    params = {"calendar_id": "primary", "calendar_id_is_stored": True}
    if avec_compte:
        params["account_id"] = compte.id

    reponse = await client.request(methode, f"/api/calendar{chemin}", params=params,
                                   **({"json": {"summary": "Modifié"}} if methode == "PUT" else {}))

    assert reponse.status_code == 400, reponse.text
    assert reponse.json()["detail"] == "Ce fournisseur d’agenda n’est pas pris en charge."
    assert appels == []
    await session.refresh(evenement)
    assert (evenement.calendar_id, evenement.summary) == (compte.email, "À conserver")


@pytest.mark.parametrize("methode,chemin", [
    ("GET", "/events"), ("GET", "/events/rendez-vous"),
    ("PUT", "/events/rendez-vous"), ("DELETE", "/events/rendez-vous"),
])
async def test_r3_selection_absente_ne_devient_pas_google(agenda_memoire, methode, chemin):
    client, _, compte, _, _, appels = agenda_memoire
    reponse = await client.request(methode, f"/api/calendar{chemin}", params={
        "calendar_id": "absent", "calendar_id_is_stored": True, "account_id": compte.id,
    }, **({"json": {"summary": "Modifié"}} if methode == "PUT" else {}))
    assert reponse.status_code == 404, reponse.text
    assert reponse.json()["detail"] == "Calendrier introuvable : absent"
    assert appels == []


@pytest.mark.parametrize("alias", [{}, {"calendar_id": "primary"}])
async def test_r3_cycle_alias_google_met_a_jour_puis_supprime_le_cache(agenda_memoire, alias):
    client, session, compte, historique, _, appels = agenda_memoire
    params = {"account_id": compte.id, **alias}
    creation = await client.post("/api/calendar/events", params={"account_id": compte.id}, json={
        "summary": "Titre initial", "start_date": "2026-12-01", "end_date": "2026-12-01",
    })
    assert creation.status_code == 200, creation.text
    assert creation.json()["calendar_id"] == compte.email
    evenement = await session.get(CalendarEvent, creation.json()["id"])
    evenement.project_id = "dossier"
    session.add(evenement)
    await session.commit()
    chemin = f"/api/calendar/events/{evenement.id}"

    modification = await client.put(chemin, params=params, json={"summary": "Titre modifié"})

    assert modification.status_code == 200, modification.text
    await session.refresh(evenement)
    assert evenement.summary == "Titre modifié"
    assert modification.json()["calendar_id"] == compte.email
    assert (evenement.calendar_id, evenement.project_id) == (compte.email, "dossier")
    lecture = await client.get(chemin, params=params)
    assert lecture.status_code == 200, lecture.text
    assert (lecture.json()["summary"], lecture.json()["calendar_id"]) == ("Titre modifié", compte.email)

    suppression = await client.delete(chemin, params=params)

    assert suppression.status_code == 200, suppression.text
    assert (await session.execute(select(CalendarEvent))).scalars().all() == []
    assert (await client.get(chemin, params=params)).status_code == 404
    await session.refresh(historique)
    assert (historique.provider, historique.account_id) == ("inconnu", compte.id)
    ecritures = [(methode, url) for methode, url in appels if methode in ("PUT", "DELETE")]
    assert ecritures == [
        (methode, f"/calendar/v3/calendars/{compte.email}/events/{evenement.id}")
        for methode in ("PUT", "DELETE")
    ]


async def test_r3_suppression_par_alias_retire_la_ligne_du_cache(agenda_memoire):
    client, session, compte, _, _, _ = agenda_memoire
    creation = await client.post("/api/calendar/events", params={"account_id": compte.id}, json={
        "summary": "À supprimer", "start_date": "2026-12-01", "end_date": "2026-12-01",
    })
    assert creation.status_code == 200, creation.text
    suppression = await client.delete(f"/api/calendar/events/{creation.json()['id']}", params={
        "calendar_id": "primary", "account_id": compte.id,
    })
    assert suppression.status_code == 200, suppression.text
    assert (await session.execute(select(CalendarEvent))).scalars().all() == []


@pytest.mark.parametrize("methode,chemin", [
    ("GET", "/events"), ("GET", "/events/rendez-vous"),
    ("PUT", "/events/rendez-vous"), ("DELETE", "/events/rendez-vous"),
])
async def test_r3_destination_google_refuse_un_autre_compte(agenda_memoire, methode, chemin):
    client, session, compte, _, distant, appels = agenda_memoire
    session.add(Calendar(id=compte.email, summary="Principal", provider="google", account_id=compte.id))
    evenement = CalendarEvent(id=distant["id"], calendar_id=compte.email, summary="À conserver")
    session.add(evenement)
    await session.commit()

    reponse = await client.request(methode, f"/api/calendar{chemin}", params={
        "calendar_id": compte.email, "account_id": "autre",
    }, **({"json": {"summary": "Modifié"}} if methode == "PUT" else {}))

    assert reponse.status_code == 404, reponse.text
    assert appels == []
    await session.refresh(evenement)
    assert evenement.summary == "À conserver"


async def test_r3_lecture_par_alias_ne_designe_pas_un_agenda_voisin_du_meme_compte(agenda_memoire):
    client, session, compte, _, distant, appels = agenda_memoire
    session.add(Calendar(id="voisin", summary="Voisin", provider="google", account_id=compte.id))
    session.add(CalendarEvent(id=distant["id"], calendar_id="voisin", summary="À conserver"))
    await session.commit()
    reponse = await client.get(f"/api/calendar/events/{distant['id']}", params={"account_id": compte.id})
    assert reponse.status_code == 404, reponse.text
    assert all(methode == "GET" for methode, _ in appels)


@pytest.mark.parametrize("methode", ["PUT", "DELETE"])
@pytest.mark.parametrize("compte_source", ["compte", "autre", None])
async def test_r3_mutation_historique_sans_lecture_prealable(agenda_memoire, methode, compte_source):
    client, session, compte, historique, distant, _ = agenda_memoire
    historique.account_id = compte_source
    evenement = CalendarEvent(id=distant["id"], calendar_id="primary", summary="Historique", project_id="dossier")
    session.add(evenement)
    await session.commit()
    await session.refresh(evenement)
    avant = deepcopy(evenement.model_dump())
    reponse = await client.request(methode, f"/api/calendar/events/{evenement.id}", params={
        "account_id": compte.id,
    }, **({"json": {"summary": "Modifié"}} if methode == "PUT" else {}))
    assert reponse.status_code == 200, reponse.text
    if compte_source != compte.id:
        await session.refresh(evenement)
        assert evenement.model_dump() == avant
    elif methode == "PUT":
        await session.refresh(evenement)
        assert (evenement.calendar_id, evenement.summary, evenement.project_id) == (compte.email, "Modifié", "dossier")
    else:
        assert (await session.execute(select(CalendarEvent))).scalars().all() == []
