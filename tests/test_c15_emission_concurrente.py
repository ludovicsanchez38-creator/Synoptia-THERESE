"""Deux demandes concurrentes doivent émettre une même pièce une seule fois."""

from __future__ import annotations

import asyncio
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest
from app.main import app
from app.models import database as db
from app.models.entities import Invoice
from app.routers import invoices as factures
from httpx import ASGITransport, AsyncClient, Response
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


def _instant_utc(valeur: str | None) -> datetime | None:
    if valeur is None:
        return None
    instant = datetime.fromisoformat(valeur.replace("Z", "+00:00"))
    return instant.replace(tzinfo=UTC) if instant.tzinfo is None else instant.astimezone(UTC)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("mode", "operations"),
    (
        ("provisoire-deux-envois", ("sent", "sent")),
        ("provisoire-envoi-paiement", ("sent", "paid")),
        ("provisoire-deux-paiements", ("paid", "paid")),
        ("historique-emise", ("sent", "paid")),
    ),
)
async def test_deux_emissions_concurrentes_conservent_un_numero_unique(
    client: Any, monkeypatch: pytest.MonkeyPatch,
    mode: str, operations: tuple[str, str],
) -> None:
    # La fixture client initialise la base et son lifespan. Les requêtes
    # concurrentes ci-dessous empruntent réellement l'ASGI, sur cette base.
    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://testserver") as http:
        contact = await http.post(
            "/api/memory/contacts",
            json={"first_name": "Client", "last_name": "Concurrence jetable"},
        )
        assert contact.status_code == 200, contact.text
        contact_id = contact.json()["id"]
        corps = {
            "contact_id": contact_id,
            "document_type": "facture",
            "lines": [{"description": "Témoin", "quantity": 1, "unit_price_ht": 10}],
        }
        maintenant = datetime.now(UTC)
        historique = mode == "historique-emise"
        if historique:
            async with db.AsyncSessionLocal() as session:
                piece = Invoice(
                    contact_id=contact_id, document_type="facture",
                    invoice_number=f"FACT-{maintenant.year}-007", status="cancelled",
                    issue_date=maintenant - timedelta(days=60),
                    due_date=maintenant - timedelta(days=30),
                    sent_at=maintenant - timedelta(days=60),
                )
                session.add(piece)
                session.add(Invoice(
                    contact_id=contact_id, document_type="facture",
                    invoice_number=f"FACT-{maintenant.year}-008", status="sent",
                    issue_date=maintenant - timedelta(days=30),
                    due_date=maintenant, sent_at=maintenant - timedelta(days=30),
                ))
                await session.commit()
                identifiant = piece.id
            initial = (await http.get(f"/api/invoices/{identifiant}")).json()
        else:
            creation = await http.post("/api/invoices/", json=corps)
            assert creation.status_code == 200, creation.text
            initial = creation.json()
            identifiant = initial["id"]

        charger = factures._get_invoice_with_lines
        attribuer = factures._attribuer_numero_definitif
        premier_charge = asyncio.Event()
        second_charge = asyncio.Event()
        premiere_reponse = asyncio.Event()
        ordres_sessions: dict[int, int] = {}
        lectures: list[dict[str, Any]] = []

        async def charger_avec_temoin(
            session: AsyncSession, invoice_id: str,
        ) -> Invoice | None:
            piece = await charger(session, invoice_id)
            cle = id(session)
            if invoice_id == identifiant and cle not in ordres_sessions:
                ordre = len(ordres_sessions) + 1
                ordres_sessions[cle] = ordre
                lectures.append({
                    "ordre": ordre,
                    "numero": piece.invoice_number if piece else None,
                    "statut": piece.status if piece else None,
                })
                if ordre == 1:
                    premier_charge.set()
                elif ordre == 2:
                    second_charge.set()
            return piece

        async def attribuer_avec_temoin(
            session: AsyncSession, piece: Invoice, statut: str | None,
        ) -> Invoice:
            if piece.id == identifiant:
                ordre = ordres_sessions[id(session)]
                if ordre == 1:
                    # Favorise le chevauchement des deux lectures. Si un
                    # correctif verrouille avant lecture, on laisse quand
                    # même le premier terminer après cette attente bornée.
                    try:
                        await asyncio.wait_for(second_charge.wait(), timeout=0.5)
                    except TimeoutError:
                        pass
                elif ordre == 2:
                    # La seconde requête a lu la pièce, puis l'allocation
                    # attend le commit ET la réponse complète de la première.
                    await asyncio.wait_for(premiere_reponse.wait(), timeout=5)
            return await attribuer(session, piece, statut)

        monkeypatch.setattr(factures, "_get_invoice_with_lines", charger_avec_temoin)
        monkeypatch.setattr(factures, "_attribuer_numero_definitif", attribuer_avec_temoin)

        async def emettre(operation: str, premiere: bool) -> Response:
            try:
                if operation == "paid":
                    return await http.patch(f"/api/invoices/{identifiant}/mark-paid", json={})
                return await http.put(f"/api/invoices/{identifiant}", json={"status": "sent"})
            finally:
                if premiere:
                    premiere_reponse.set()

        premiere = asyncio.create_task(emettre(operations[0], True))
        await asyncio.wait_for(premier_charge.wait(), timeout=5)
        seconde = asyncio.create_task(emettre(operations[1], False))
        reponses = await asyncio.wait_for(asyncio.gather(premiere, seconde), timeout=15)
        relue = await http.get(f"/api/invoices/{identifiant}")
        suivante = await http.post("/api/invoices/", json=corps)
        assert suivante.status_code == 200, suivante.text
        suivante_emise = await http.put(
            f"/api/invoices/{suivante.json()['id']}", json={"status": "sent"},
        )

        def contenu(reponse: Response) -> Any:
            try:
                return reponse.json()
            except ValueError:
                return reponse.text

        observation = {
            "mode": mode,
            "initial": initial,
            "lectures": lectures,
            "reponses": [
                {"statut_http": r.status_code, "corps": contenu(r)} for r in reponses
            ],
            "relue": {"statut_http": relue.status_code, "corps": contenu(relue)},
            "suivante": {"statut_http": suivante_emise.status_code, "corps": contenu(suivante_emise)},
        }
        preuves = Path(__file__).resolve().parents[1] / ".app-loop/cycles/15/reprise/lot-c"
        preuves.mkdir(parents=True, exist_ok=True)
        (preuves / f"concurrence-observation-{mode}.txt").write_text(
            json.dumps(observation, ensure_ascii=False, indent=2, default=str),
        )
        assert all(r.status_code == 200 for r in reponses), observation
        assert relue.status_code == 200, observation
        assert suivante_emise.status_code == 200, observation
        numeros = [r.json()["invoice_number"] for r in reponses]
        assert numeros[0] == numeros[1] == relue.json()["invoice_number"], observation

        # SQLite peut relire une date UTC sans suffixe ; on compare l'instant,
        # afin de détecter une nouvelle première émission sans faux écart de format.
        for champ in ("issue_date", "due_date", "sent_at"):
            assert _instant_utc(reponses[0].json()[champ]) == (
                _instant_utc(reponses[1].json()[champ])
            ) == _instant_utc(relue.json()[champ]), observation
        if historique:
            for champ in ("invoice_number", "issue_date", "due_date", "sent_at"):
                assert all(r.json()[champ] == initial[champ] for r in reponses), observation
                assert relue.json()[champ] == initial[champ], observation
        rang_suivant = 9 if historique else 2
        assert suivante_emise.json()["invoice_number"] == (
            f"FACT-{maintenant.year}-{rang_suivant:03d}"
        ), observation


@pytest.mark.asyncio
async def test_deux_pieces_distinctes_emises_en_concurrence_suivent_la_serie(
    client: Any,
) -> None:
    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://testserver") as http:
        contact = await http.post(
            "/api/memory/contacts",
            json={"first_name": "Client", "last_name": "Deux pièces jetables"},
        )
        assert contact.status_code == 200, contact.text
        corps = {
            "contact_id": contact.json()["id"], "document_type": "facture",
            "lines": [{"description": "Témoin", "quantity": 1, "unit_price_ht": 10}],
        }
        premieres = [await http.post("/api/invoices/", json=corps) for _ in range(2)]
        assert all(r.status_code == 200 for r in premieres), [r.text for r in premieres]
        reponses = await asyncio.gather(
            http.put(f"/api/invoices/{premieres[0].json()['id']}", json={"status": "sent"}),
            http.patch(f"/api/invoices/{premieres[1].json()['id']}/mark-paid", json={}),
        )
        assert all(r.status_code == 200 for r in reponses), [r.text for r in reponses]
        annee = datetime.now(UTC).year
        numeros = {r.json()["invoice_number"] for r in reponses}
        assert numeros == {f"FACT-{annee}-001", f"FACT-{annee}-002"}, numeros
        for reponse in reponses:
            piece = reponse.json()
            relue = await http.get(f"/api/invoices/{piece['id']}")
            assert relue.status_code == 200, relue.text
            assert relue.json()["invoice_number"] == piece["invoice_number"]
            for champ in ("issue_date", "due_date", "sent_at"):
                assert _instant_utc(relue.json()[champ]) == _instant_utc(piece[champ])
        suivante = await http.post("/api/invoices/", json=corps)
        assert suivante.status_code == 200, suivante.text
        suivante_emise = await http.put(
            f"/api/invoices/{suivante.json()['id']}", json={"status": "sent"},
        )
        assert suivante_emise.status_code == 200, suivante_emise.text
        assert suivante_emise.json()["invoice_number"] == f"FACT-{annee}-003"
        preuves = Path(__file__).resolve().parents[1] / ".app-loop/cycles/15/reprise/lot-c"
        preuves.mkdir(parents=True, exist_ok=True)
        (preuves / "concurrence-pieces-distinctes.txt").write_text(
            json.dumps({
                "numeros": sorted(numeros),
                "suivante": suivante_emise.json()["invoice_number"],
            }, ensure_ascii=False, indent=2),
        )


@pytest.mark.asyncio
async def test_base_occupee_refuse_emission_sans_erreur_inattendue(
    client: Any, monkeypatch: pytest.MonkeyPatch,
) -> None:
    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://testserver") as http:
        contact = await http.post(
            "/api/memory/contacts",
            json={"first_name": "Client", "last_name": "Base occupée jetable"},
        )
        assert contact.status_code == 200, contact.text
        creation = await http.post("/api/invoices/", json={
            "contact_id": contact.json()["id"], "document_type": "facture",
            "lines": [{"description": "Témoin", "quantity": 1, "unit_price_ht": 10}],
        })
        assert creation.status_code == 200, creation.text
        identifiant = creation.json()["id"]
        initiale = await http.get(f"/api/invoices/{identifiant}")
        assert initiale.status_code == 200, initiale.text
        assert initiale.json()["invoice_number"].startswith("PROV-")
        assert db._db_cipher_active
        assert db.db_is_encrypted(db.settings.db_path)

        verrouiller = factures._verrouiller_emission
        delai_requete: list[int] = []

        async def verrouiller_avec_delai_court(session: AsyncSession) -> None:
            # Seul le délai réel du pilote change. Le BEGIN de la route et
            # l'OperationalError éventuelle sont ceux de SQLCipher.
            await session.execute(text("PRAGMA busy_timeout=30"))
            delai_requete.append((await session.execute(text("PRAGMA busy_timeout"))).scalar_one())
            await verrouiller(session)

        monkeypatch.setattr(factures, "_verrouiller_emission", verrouiller_avec_delai_court)
        async with db.AsyncSessionLocal() as reservation:
            await reservation.execute(text("BEGIN IMMEDIATE"))
            try:
                reponse = await asyncio.wait_for(http.put(
                    f"/api/invoices/{identifiant}", json={"status": "sent"},
                ), timeout=5)
            finally:
                await reservation.rollback()

        relue = await http.get(f"/api/invoices/{identifiant}")
        observation = {
            "sqlcipher_actif": db._db_cipher_active,
            "base_chiffree": db.db_is_encrypted(db.settings.db_path),
            "delai_requete_ms": delai_requete,
            "initiale": initiale.json(),
            "reponse": {"statut_http": reponse.status_code, "corps": reponse.json()},
            "relue": {"statut_http": relue.status_code, "corps": relue.json()},
        }
        preuves = Path(__file__).resolve().parents[1] / ".app-loop/cycles/15/reprise/lot-c"
        preuves.mkdir(parents=True, exist_ok=True)
        (preuves / "concurrence-base-occupee.txt").write_text(
            json.dumps(observation, ensure_ascii=False, indent=2, default=str),
        )
        assert delai_requete == [30], observation
        assert relue.status_code == 200, observation
        assert relue.json() == initiale.json(), observation
        assert reponse.status_code in (409, 503), observation
        message = reponse.json().get("message", "").casefold()
        assert "base" in message and "occup" in message, observation
        assert "réessa" in message or "reessa" in message, observation
