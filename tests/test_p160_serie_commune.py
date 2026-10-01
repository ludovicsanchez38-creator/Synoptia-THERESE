"""P160 : prochaines factures et avoirs dans une séquence FACT commune."""

from __future__ import annotations

import asyncio
import json
import os
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest
from app.main import app
from app.models import database as db
from app.models.entities import Invoice
from app.routers import invoices as factures
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


def _trace(nom: str, observation: dict[str, Any]) -> None:
    if destination := os.environ.get("P160_PREUVES"):
        (Path(destination) / f"{nom}.json").write_text(
            json.dumps(observation, ensure_ascii=False, indent=2, default=str) + "\n",
        )


def _instant_utc(valeur: str | None) -> datetime | None:
    if valeur is None:
        return None
    instant = datetime.fromisoformat(valeur.replace("Z", "+00:00"))
    return instant.replace(tzinfo=UTC) if instant.tzinfo is None else instant.astimezone(UTC)


async def _contact(client: Any) -> str:
    response = await client.post("/api/memory/contacts", json={
        "first_name": "Client", "last_name": "Série commune jetable",
    })
    assert response.status_code == 200, response.text
    return response.json()["id"]


async def _cree(client: Any, contact_id: str, document_type: str = "facture",
                origine: str | None = None) -> dict[str, Any]:
    response = await client.post("/api/invoices/", json={
        "contact_id": contact_id, "document_type": document_type,
        "converted_from_id": origine,
        "lines": [{"description": "Témoin", "quantity": 1, "unit_price_ht": 10}],
    })
    assert response.status_code == 200, response.text
    assert response.json()["invoice_number"].startswith("PROV-")
    assert db._db_cipher_active and db.db_is_encrypted(db.settings.db_path)
    return response.json()


async def _emet(client: Any, piece: dict[str, Any], paiement: bool = False) -> dict[str, Any]:
    if paiement:
        response = await client.patch(f"/api/invoices/{piece['id']}/mark-paid", json={})
    else:
        response = await client.put(f"/api/invoices/{piece['id']}", json={"status": "sent"})
    assert response.status_code == 200, response.text
    return response.json()


@pytest.mark.asyncio
async def test_facture_avoir_facture_suivent_une_seule_serie(client: Any) -> None:
    contact_id = await _contact(client)
    origine = await _emet(client, await _cree(client, contact_id))
    avoir = await _emet(client, await _cree(client, contact_id, "avoir", origine["id"]), paiement=True)
    suivante = await _emet(client, await _cree(client, contact_id))
    numeros = [piece["invoice_number"] for piece in (origine, avoir, suivante)]
    _trace("suite-commune", {"origine": origine, "avoir": avoir, "suivante": suivante})
    annee = datetime.now(UTC).year
    assert numeros == [f"FACT-{annee}-{rang:03d}" for rang in (1, 2, 3)], numeros
    assert avoir["document_type"] == "avoir" and avoir["converted_from_id"] == origine["id"]


@pytest.mark.asyncio
@pytest.mark.parametrize("convention", [
    "AV-courant", "FACT-ancien", "import", "FACT-zero", "FACT-alias", "FACT-courant",
])
async def test_brouillon_herite_rejoint_la_serie_sans_modifier_les_pieces_emises(
    client: Any, convention: str,
) -> None:
    contact_id = await _contact(client)
    annee = datetime.now(UTC).year
    numeros = {
        "AV-courant": f"AV-{annee}-007", "FACT-ancien": f"FACT-{annee - 1}-007",
        "import": f"IMPORT-{annee}-007", "FACT-zero": f"FACT-{annee}-000",
        "FACT-alias": f"FACT-{annee}-7",
        "FACT-courant": f"FACT-{annee}-007",
    }
    async with db.AsyncSessionLocal() as session:
        historique = Invoice(
            invoice_number=f"FACT-{annee}-007" if convention == "FACT-alias" else f"AV-{annee}-006",
            document_type="facture" if convention == "FACT-alias" else "avoir", contact_id=contact_id,
            status="sent", issue_date=datetime(annee, 1, 2, tzinfo=UTC),
            due_date=datetime(annee, 2, 2, tzinfo=UTC), sent_at=datetime(annee, 1, 2, tzinfo=UTC),
        )
        brouillon = Invoice(
            invoice_number=numeros[convention], document_type="facture", contact_id=contact_id,
            status="draft", issue_date=datetime(annee - 1, 1, 2, tzinfo=UTC),
            due_date=datetime.now(UTC) + timedelta(days=30),
        )
        session.add_all([historique, brouillon])
        await session.commit()
        historique_id, brouillon_id = historique.id, brouillon.id
    avant = (await client.get(f"/api/invoices/{historique_id}")).json()
    # Une simple modification de notes ne migre pas un brouillon.
    notes = await client.put(f"/api/invoices/{brouillon_id}", json={"notes": "Avant émission"})
    assert notes.status_code == 200, notes.text
    assert notes.json()["invoice_number"] == numeros[convention]
    emis = await _emet(client, notes.json())
    suivante = await _emet(client, await _cree(client, contact_id))
    apres = (await client.get(f"/api/invoices/{historique_id}")).json()
    _trace(f"heritage-{convention}", {
        "avant": avant, "apres": apres, "brouillon": notes.json(), "emis": emis, "suivante": suivante,
    })
    assert apres == avant
    premier_rang = 8 if convention == "FACT-alias" else 7 if convention == "FACT-courant" else 1
    assert emis["invoice_number"] == f"FACT-{annee}-{premier_rang:03d}", emis
    assert suivante["invoice_number"] == f"FACT-{annee}-{premier_rang + 1:03d}", suivante


@pytest.mark.asyncio
async def test_facture_et_avoir_emis_en_concurrence_partagent_la_reservation(client: Any) -> None:
    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://testserver") as http:
        contact_id = await _contact(http)
        origine = await _emet(http, await _cree(http, contact_id))
        facture = await _cree(http, contact_id)
        avoir = await _cree(http, contact_id, "avoir", origine["id"])
        reponses = await asyncio.wait_for(asyncio.gather(
            http.put(f"/api/invoices/{facture['id']}", json={"status": "sent"}),
            http.patch(f"/api/invoices/{avoir['id']}/mark-paid", json={}),
        ), timeout=15)
        observation = [{"status": r.status_code, "corps": r.json()} for r in reponses]
        _trace("concurrence-mixte", {"reponses": observation})
        assert all(r.status_code == 200 for r in reponses), observation
        annee = datetime.now(UTC).year
        assert {r.json()["invoice_number"] for r in reponses} == {
            f"FACT-{annee}-002", f"FACT-{annee}-003",
        }, observation
        for response in reponses:
            relue = await http.get(f"/api/invoices/{response.json()['id']}")
            assert relue.status_code == 200, relue.text
            for champ in ("invoice_number", "issue_date", "due_date", "sent_at"):
                if champ == "invoice_number":
                    assert relue.json()[champ] == response.json()[champ]
                else:
                    assert _instant_utc(relue.json()[champ]) == _instant_utc(response.json()[champ])
        suivante = await _emet(http, await _cree(http, contact_id))
        assert suivante["invoice_number"] == f"FACT-{annee}-004"


@pytest.mark.asyncio
async def test_refus_apres_allocation_ne_consomme_pas_de_numero(client: Any) -> None:
    contact_id = await _contact(client)
    origine = await _emet(client, await _cree(client, contact_id))
    avoir = await _cree(client, contact_id, "avoir", origine["id"])
    response = await client.put(f"/api/invoices/{avoir['id']}", json={
        "status": "sent", "due_date": "2026-02-30",
    })
    relue = (await client.get(f"/api/invoices/{avoir['id']}")).json()
    emis = await _emet(client, avoir)
    _trace("rollback-allocation", {"refus": response.json(), "relue": relue, "emis": emis})
    assert response.status_code == 422, response.text
    assert relue["invoice_number"] == avoir["invoice_number"] and relue["status"] == "draft"
    assert emis["invoice_number"] == f"FACT-{datetime.now(UTC).year}-002", emis


@pytest.mark.asyncio
async def test_avoir_partage_le_maximum_numerique_meme_occupe_par_un_autre_type(client: Any) -> None:
    contact_id = await _contact(client)
    annee = datetime.now(UTC).year
    async with db.AsyncSessionLocal() as session:
        for rang in (999, 1000):
            session.add(Invoice(
                invoice_number=f"FACT-{annee}-{rang}", document_type="devis", contact_id=contact_id,
                due_date=datetime.now(UTC) + timedelta(days=30),
            ))
        await session.commit()
    origine = await _emet(client, await _cree(client, contact_id))
    avoir = await _emet(client, await _cree(client, contact_id, "avoir", origine["id"]))
    _trace("maximum-numerique", {"origine": origine, "avoir": avoir})
    assert origine["invoice_number"] == f"FACT-{annee}-1001", origine
    assert avoir["invoice_number"] == f"FACT-{annee}-1002", avoir


@pytest.mark.asyncio
@pytest.mark.parametrize("operation", ["sent", "mark-paid"])
async def test_frontiere_annee_garde_numero_et_date_dans_la_meme_annee(
    client: Any, monkeypatch: pytest.MonkeyPatch, operation: str,
) -> None:
    contact_id = await _contact(client)
    brouillon = await _cree(client, contact_id)
    avant = datetime(2026, 12, 31, 23, 59, 59, 999999, tzinfo=UTC)
    apres = datetime(2027, 1, 1, 0, 0, 0, tzinfo=UTC)
    phase = {"apres_allocation": False}
    lectures: list[dict[str, Any]] = []

    class Horloge(datetime):
        @classmethod
        def now(cls, tz: Any = None) -> datetime:
            instant = apres if phase["apres_allocation"] else avant
            lectures.append({"apres_allocation": phase["apres_allocation"], "instant": instant.isoformat()})
            return instant.astimezone(tz) if tz is not None else instant.replace(tzinfo=None)

    generateur = factures._generate_invoice_number

    async def allouer_puis_passer_minuit(
        session: AsyncSession, document_type: str = "facture", **kwargs: Any,
    ) -> str:
        numero = await generateur(session, document_type, **kwargs)
        phase["apres_allocation"] = True
        return numero

    monkeypatch.setattr(factures, "datetime", Horloge)
    monkeypatch.setattr(factures, "_generate_invoice_number", allouer_puis_passer_minuit)
    if operation == "mark-paid":
        response = await client.patch(f"/api/invoices/{brouillon['id']}/mark-paid", json={})
    else:
        response = await client.put(f"/api/invoices/{brouillon['id']}", json={"status": "sent"})
    corps = response.json()
    _trace(f"frontiere-annee-{operation}", {
        "status": response.status_code, "reponse": corps, "lectures_horloge": lectures,
        "regle_temoin": "horloge du seul module invoices avancée après retour du vrai allocateur",
    })
    assert response.status_code == 200, response.text
    assert phase["apres_allocation"], "l'allocateur réel n'a pas été appelé"
    annee_numero = int(corps["invoice_number"].split("-")[1])
    annee_date = datetime.fromisoformat(corps["issue_date"].replace("Z", "+00:00")).year
    assert annee_numero == annee_date, corps
    assert datetime.fromisoformat(corps["issue_date"].replace("Z", "+00:00")) == avant, corps
    if operation == "sent":
        assert datetime.fromisoformat(corps["sent_at"].replace("Z", "+00:00")) == avant, corps
    ancienne_date = datetime.fromisoformat(brouillon["issue_date"].replace("Z", "+00:00"))
    ancienne_echeance = datetime.fromisoformat(brouillon["due_date"].replace("Z", "+00:00"))
    nouvelle_echeance = datetime.fromisoformat(corps["due_date"].replace("Z", "+00:00"))
    assert nouvelle_echeance.date() == ancienne_echeance.date() + timedelta(
        days=(avant.date() - ancienne_date.date()).days,
    ), corps
