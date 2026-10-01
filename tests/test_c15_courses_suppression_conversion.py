"""Courses entre suppression/émission et deux conversions du même devis."""

from __future__ import annotations

import asyncio
import json
from contextvars import ContextVar
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest
from app.main import app
from app.models import database as db
from app.models.entities import Invoice
from app.routers import invoices as factures
from httpx import ASGITransport, AsyncClient, Response
from sqlalchemy.ext.asyncio import AsyncSession

PREUVES = Path(__file__).resolve().parents[1] / ".app-loop/cycles/15/reprise/lot-c"


async def _piece(http: AsyncClient, type_document: str) -> dict[str, Any]:
    contact = await http.post("/api/memory/contacts", json={
        "first_name": "Client", "last_name": "Courses jetables",
    })
    assert contact.status_code == 200, contact.text
    creation = await http.post("/api/invoices/", json={
        "contact_id": contact.json()["id"], "document_type": type_document,
        "lines": [{"description": "Témoin", "quantity": 1, "unit_price_ht": 10}],
    })
    assert creation.status_code == 200, creation.text
    assert db._db_cipher_active
    assert db.db_is_encrypted(db.settings.db_path)
    return creation.json()


def _reponse(response: Response) -> dict[str, Any]:
    try:
        corps = response.json()
    except ValueError:
        corps = response.text
    return {"statut_http": response.status_code, "corps": corps}


def _preuve(nom: str, observation: dict[str, Any]) -> None:
    PREUVES.mkdir(parents=True, exist_ok=True)
    (PREUVES / f"concurrence-course-{nom}.txt").write_text(
        json.dumps(observation, ensure_ascii=False, indent=2, default=str),
    )


def _instant_utc(valeur: str | None) -> datetime | None:
    if valeur is None:
        return None
    instant = datetime.fromisoformat(valeur.replace("Z", "+00:00"))
    return instant.replace(tzinfo=UTC) if instant.tzinfo is None else instant.astimezone(UTC)


@pytest.mark.asyncio
async def test_suppression_chargee_avant_emission_ne_supprime_aucun_numero_emis(
    client: Any, monkeypatch: pytest.MonkeyPatch,
) -> None:
    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://testserver") as http:
        piece = await _piece(http, "facture")
        identifiant = piece["id"]
        assert piece["invoice_number"].startswith("PROV-")
        charger = factures._get_invoice_with_lines
        suppression_chargee = asyncio.Event()
        emission_terminee = asyncio.Event()
        operation: ContextVar[str] = ContextVar("operation_suppression", default="relecture")
        lectures: list[dict[str, Any]] = []

        async def charger_avec_temoin(
            session: AsyncSession, invoice_id: str,
        ) -> Invoice | None:
            chargee = await charger(session, invoice_id)
            if invoice_id == identifiant:
                lectures.append({
                    "operation": operation.get(),
                    "numero": chargee.invoice_number if chargee else None,
                    "statut": chargee.status if chargee else None,
                })
                if operation.get() == "delete" and not suppression_chargee.is_set():
                    suppression_chargee.set()
                    # Si DELETE réserve avant lecture, cette attente bornée
                    # le laisse terminer puis l'émission est refusée sur 404.
                    # Sinon on favorise le commit émis avant sa décision.
                    try:
                        await asyncio.wait_for(emission_terminee.wait(), timeout=0.5)
                    except TimeoutError:
                        pass
            return chargee

        monkeypatch.setattr(factures, "_get_invoice_with_lines", charger_avec_temoin)

        async def supprimer() -> Response:
            jeton = operation.set("delete")
            try:
                return await http.delete(f"/api/invoices/{identifiant}")
            finally:
                operation.reset(jeton)

        suppression = asyncio.create_task(supprimer())
        await asyncio.wait_for(suppression_chargee.wait(), timeout=5)
        jeton = operation.set("emission")
        try:
            emission = await asyncio.wait_for(http.put(
                f"/api/invoices/{identifiant}", json={"status": "sent"},
            ), timeout=10)
        finally:
            operation.reset(jeton)
            emission_terminee.set()
        effacee = await asyncio.wait_for(suppression, timeout=10)
        relue = await http.get(f"/api/invoices/{identifiant}")
        suivante = await http.post("/api/invoices/", json={
            "contact_id": piece["contact_id"], "document_type": "facture",
            "lines": [{"description": "Suite", "quantity": 1, "unit_price_ht": 10}],
        })
        assert suivante.status_code == 200, suivante.text
        suivante_emise = await http.put(
            f"/api/invoices/{suivante.json()['id']}", json={"status": "sent"},
        )
        observation = {
            "sqlcipher_actif": db._db_cipher_active,
            "initiale": piece, "lectures": lectures,
            "emission": _reponse(emission), "suppression": _reponse(effacee),
            "relue": _reponse(relue), "suivante_emise": _reponse(suivante_emise),
        }
        _preuve("suppression-emission", observation)
        assert suivante_emise.status_code == 200, observation
        if emission.status_code == 200:
            assert relue.status_code == 200, observation
            assert effacee.status_code == 409, observation
            assert relue.json()["invoice_number"] == emission.json()["invoice_number"], observation
            for champ in ("issue_date", "due_date", "sent_at"):
                assert _instant_utc(relue.json()[champ]) == _instant_utc(emission.json()[champ]), observation
            assert suivante_emise.json()["invoice_number"] != emission.json()["invoice_number"], observation
        else:
            # DELETE peut gagner avant toute émission, sans numéro délivré.
            assert emission.status_code in (404, 409), observation
            assert effacee.status_code == 200 and relue.status_code == 404, observation


@pytest.mark.asyncio
async def test_deux_conversions_concurrentes_du_meme_devis_ne_creent_qu_une_facture(
    client: Any, monkeypatch: pytest.MonkeyPatch,
) -> None:
    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://testserver") as http:
        devis = await _piece(http, "devis")
        identifiant = devis["id"]
        charger = factures._get_invoice_with_lines
        premier_charge = asyncio.Event()
        second_charge = asyncio.Event()
        premiere_terminee = asyncio.Event()
        sessions: dict[int, int] = {}
        lectures: list[dict[str, Any]] = []

        async def charger_avec_temoin(
            session: AsyncSession, invoice_id: str,
        ) -> Invoice | None:
            piece = await charger(session, invoice_id)
            if invoice_id == identifiant and id(session) not in sessions:
                ordre = len(sessions) + 1
                sessions[id(session)] = ordre
                lectures.append({
                    "ordre": ordre,
                    "numero": piece.invoice_number if piece else None,
                    "statut": piece.status if piece else None,
                })
                if ordre == 1:
                    premier_charge.set()
                    try:
                        await asyncio.wait_for(second_charge.wait(), timeout=0.5)
                    except TimeoutError:
                        pass
                elif ordre == 2:
                    second_charge.set()
                    await asyncio.wait_for(premiere_terminee.wait(), timeout=5)
            return piece

        monkeypatch.setattr(factures, "_get_invoice_with_lines", charger_avec_temoin)

        async def convertir(premiere: bool) -> Response:
            try:
                return await http.post(f"/api/invoices/{identifiant}/convert-to-invoice", json={})
            finally:
                if premiere:
                    premiere_terminee.set()

        premiere = asyncio.create_task(convertir(True))
        await asyncio.wait_for(premier_charge.wait(), timeout=5)
        seconde = asyncio.create_task(convertir(False))
        reponses = await asyncio.wait_for(asyncio.gather(premiere, seconde), timeout=15)
        source_relue = await http.get(f"/api/invoices/{identifiant}")
        liste = await http.get("/api/invoices/", params={
            "document_type": "facture", "contact_id": devis["contact_id"], "limit": 100,
        })
        assert liste.status_code == 200, liste.text
        copies = [piece for piece in liste.json() if piece["converted_from_id"] == identifiant]
        observation = {
            "sqlcipher_actif": db._db_cipher_active,
            "initiale": devis, "lectures": lectures,
            "reponses": [_reponse(r) for r in reponses],
            "source_relue": _reponse(source_relue), "factures_creees": copies,
        }
        _preuve("double-conversion", observation)
        assert source_relue.status_code == 200, observation
        assert source_relue.json()["invoice_number"] == devis["invoice_number"], observation
        assert source_relue.json()["status"] == "converted", observation
        assert len(copies) == 1, observation
        assert any(r.status_code == 200 for r in reponses), observation
        assert all(r.status_code in (200, 400, 409) for r in reponses), observation
        identifiants_retournes = {r.json()["id"] for r in reponses if r.status_code == 200}
        assert identifiants_retournes == {copies[0]["id"]}, observation
