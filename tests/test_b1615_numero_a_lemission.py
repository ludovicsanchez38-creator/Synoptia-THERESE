"""B-1615 : le numéro définitif d'une facture naît à l'émission.

Le 7° du I de l'article 242 nonies A de l'annexe II au CGI et le § 90 du
BOI-TVA-DECLA-30-20-20-10 veulent une séquence chronologique et continue,
posée au fur et à mesure de l'émission. Un brouillon qui prend FACT-… puis
se supprime laisse un trou. Le devis n'est pas visé par ces textes.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from app.services.invoice_pdf import InvoicePDFGenerator
from httpx import AsyncClient
from pypdf import PdfReader


def _annee() -> int:
    return datetime.now(UTC).year


async def _contact(client: AsyncClient) -> str:
    reponse = await client.post(
        "/api/memory/contacts",
        json={"first_name": "Hélène", "last_name": "Ménard", "email": "helene@test.fr"},
    )
    assert reponse.status_code == 200, reponse.text
    return reponse.json()["id"]


def _corps(contact_id: str, document_type: str = "facture") -> dict:
    return {
        "contact_id": contact_id,
        "document_type": document_type,
        "lines": [{"description": "Table en chêne", "quantity": 1, "unit_price_ht": 900.0, "tva_rate": 20.0}],
    }


async def _cree(client: AsyncClient, contact_id: str, document_type: str = "facture") -> dict:
    reponse = await client.post("/api/invoices/", json=_corps(contact_id, document_type))
    assert reponse.status_code == 200, reponse.text
    return reponse.json()


async def _emet(client: AsyncClient, identifiant: str) -> dict:
    reponse = await client.put(f"/api/invoices/{identifiant}", json={"status": "sent"})
    assert reponse.status_code == 200, reponse.text
    return reponse.json()


@pytest.mark.asyncio
async def test_un_brouillon_ne_prend_pas_de_numero_et_sa_suppression_ne_troue_pas(client: AsyncClient):
    contact = await _contact(client)
    premier = await _cree(client, contact)
    second = await _cree(client, contact)

    assert premier["status"] == "draft"
    assert premier["invoice_number"].startswith("PROV-")
    assert second["invoice_number"].startswith("PROV-")
    assert "FACT-" not in premier["invoice_number"]

    assert (await client.delete(f"/api/invoices/{premier['id']}")).status_code == 200

    emis = await _emet(client, second["id"])
    assert emis["invoice_number"] == f"FACT-{_annee()}-001"


@pytest.mark.asyncio
async def test_supprimer_le_premier_brouillon_ne_laisse_pas_de_trou(client: AsyncClient):
    """Deux brouillons, on efface le premier : l'émission du second est 001.

    Aujourd'hui le second est déjà FACT-…-002, et l'effacement du premier
    laisse ce 002 en place.
    """
    contact = await _contact(client)
    premier = await _cree(client, contact)
    second = await _cree(client, contact)
    assert (await client.delete(f"/api/invoices/{premier['id']}")).status_code == 200

    emis = await _emet(client, second["id"])
    assert emis["invoice_number"] == f"FACT-{_annee()}-001"


@pytest.mark.asyncio
async def test_un_brouillon_deja_numerote_garde_son_numero(client: AsyncClient):
    """Migration : le dernier numéro déjà en base, encore brouillon, est gardé.

    Il est le dernier de la série, l'émettre ne casse pas l'ordre. Un numéro
    plus petit, émis après un plus grand, est couvert par le test suivant.
    """
    from app.models import database as db_module
    from app.models.entities import Invoice

    contact = await _contact(client)
    annee = _annee()
    numero = f"FACT-{annee}-007"
    async with db_module.AsyncSessionLocal() as session:
        session.add(
            Invoice(
                invoice_number=numero,
                contact_id=contact,
                document_type="facture",
                status="draft",
                due_date=datetime.now(UTC) + timedelta(days=30),
            )
        )
        await session.commit()

    liste = await client.get("/api/invoices/")
    assert liste.status_code == 200, liste.text
    trouvee = next(piece for piece in liste.json() if piece["invoice_number"] == numero)
    assert trouvee["status"] == "draft"

    notes = await client.put(f"/api/invoices/{trouvee['id']}", json={"notes": "Toujours le même numéro"})
    assert notes.status_code == 200, notes.text
    assert notes.json()["invoice_number"] == numero

    emise = await _emet(client, trouvee["id"])
    assert emise["invoice_number"] == numero

    suivante_brouillon = await _cree(client, contact)
    assert suivante_brouillon["invoice_number"].startswith("PROV-"), (
        "un brouillon neuf ne doit pas prendre le numéro qui suit 007"
    )
    suivante = await _emet(client, suivante_brouillon["id"])
    assert suivante["invoice_number"] == f"FACT-{annee}-008"
    relue = await client.get(f"/api/invoices/{trouvee['id']}")
    assert relue.json()["invoice_number"] == numero


async def _brouillon_historique(contact_id: str, numero: str, statut: str = "draft") -> str:
    from app.models import database as db_module
    from app.models.entities import Invoice

    async with db_module.AsyncSessionLocal() as session:
        piece = Invoice(
            invoice_number=numero,
            contact_id=contact_id,
            document_type="facture",
            status=statut,
            issue_date=datetime(2026, 1, 7, tzinfo=UTC),
            due_date=datetime(2026, 2, 6, tzinfo=UTC),
        )
        session.add(piece)
        await session.commit()
        return piece.id


@pytest.mark.asyncio
async def test_un_brouillon_historique_hors_ordre_prend_un_nouveau_numero(client: AsyncClient):
    """FACT-…-007 encore brouillon, émis après FACT-…-008, ne garde pas 007.

    Le § 90 veut la numérotation au fil des émissions. L'ancien numéro,
    qui n'est plus le dernier de la série, n'est pas réattribué.
    """
    contact = await _contact(client)
    annee = _annee()
    ancien = await _brouillon_historique(contact, f"FACT-{annee}-007")
    await _brouillon_historique(contact, f"FACT-{annee}-008", statut="sent")

    emis = await _emet(client, ancien)
    assert emis["invoice_number"] == f"FACT-{annee}-009"
    liste = (await client.get("/api/invoices/")).json()
    numeros = {piece["invoice_number"] for piece in liste}
    assert f"FACT-{annee}-007" not in numeros
    assert f"FACT-{annee}-008" in numeros

    suivant = await _emet(client, (await _cree(client, contact))["id"])
    assert suivant["invoice_number"] == f"FACT-{annee}-010"


@pytest.mark.asyncio
async def test_un_devis_prend_son_numero_des_la_creation(client: AsyncClient):
    contact = await _contact(client)
    devis = await _cree(client, contact, "devis")
    annee = _annee()
    assert devis["invoice_number"] == f"DEV-{annee}-001"
    second = await _cree(client, contact, "devis")
    assert second["invoice_number"] == f"DEV-{annee}-002"


@pytest.mark.asyncio
async def test_un_avoir_brouillon_prend_AV_a_lemission(client: AsyncClient):
    contact = await _contact(client)
    avoir = await _cree(client, contact, "avoir")
    assert avoir["invoice_number"].startswith("PROV-")
    emis = await _emet(client, avoir["id"])
    assert emis["invoice_number"] == f"AV-{_annee()}-001"


@pytest.mark.asyncio
async def test_un_brouillon_annule_ne_prend_pas_de_numero_mais_son_emission_oui(client: AsyncClient):
    """Annuler un brouillon ne l'émet pas. L'émettre ensuite, par envoi ou
    par paiement, est la première sortie vers un statut émis : le PROV-
    devient le prochain numéro de la série."""
    contact = await _contact(client)
    annee = _annee()

    envoye = await _cree(client, contact)
    annule = await client.put(f"/api/invoices/{envoye['id']}", json={"status": "cancelled"})
    assert annule.status_code == 200, annule.text
    assert annule.json()["status"] == "cancelled"
    assert annule.json()["invoice_number"].startswith("PROV-")

    emis = await client.put(f"/api/invoices/{envoye['id']}", json={"status": "sent"})
    assert emis.status_code == 200, emis.text
    assert emis.json()["invoice_number"] == f"FACT-{annee}-001"
    assert not emis.json()["invoice_number"].startswith("PROV-")

    paye = await _cree(client, contact)
    refuse = await client.put(f"/api/invoices/{paye['id']}", json={"status": "cancelled"})
    assert refuse.status_code == 200, refuse.text
    reglement = await client.patch(f"/api/invoices/{paye['id']}/mark-paid", json={})
    assert reglement.status_code == 200, reglement.text
    assert reglement.json()["status"] == "paid"
    assert reglement.json()["invoice_number"] == f"FACT-{annee}-002"


@pytest.mark.asyncio
async def test_emettre_l_annee_suivante_date_au_jour_et_decale_l_echeance(client: AsyncClient, monkeypatch):
    """Un brouillon de 2026 émis en 2027 prend FACT-2027 et la date du jour.

    Le BOFiP § 140 rattache la date imprimée à la délivrance. L'échéance
    avance du même nombre de jours, même si la requête renvoie l'ancienne date.
    """
    from app.routers import invoices as module_factures

    contact = await _contact(client)
    brouillon = await _cree(client, contact)

    class Horloge(datetime):
        @classmethod
        def now(cls, tz=None):  # type: ignore[override]
            return datetime(2027, 3, 15, 9, 0, tzinfo=UTC)

    monkeypatch.setattr(module_factures, "datetime", Horloge)
    emise = await client.put(
        f"/api/invoices/{brouillon['id']}",
        json={
            "status": "sent",
            "issue_date": "2026-06-01T00:00:00",
            "due_date": "2026-07-01T00:00:00",
        },
    )
    assert emise.status_code == 200, emise.text
    corps = emise.json()
    assert corps["invoice_number"] == "FACT-2027-001"
    assert corps["issue_date"].startswith("2027-03-15")
    jours = (datetime(2027, 3, 15, tzinfo=UTC).date() - datetime(2026, 6, 1).date()).days
    echeance = datetime.fromisoformat(corps["due_date"].replace("Z", "+00:00"))
    assert echeance.date() == (datetime(2026, 7, 1) + timedelta(days=jours)).date()


@pytest.mark.asyncio
async def test_marquer_payee_un_brouillon_lui_donne_son_numero(client: AsyncClient):
    contact = await _contact(client)
    brouillon = await _cree(client, contact)
    assert brouillon["invoice_number"].startswith("PROV-")
    reponse = await client.patch(f"/api/invoices/{brouillon['id']}/mark-paid", json={})
    assert reponse.status_code == 200, reponse.text
    corps = reponse.json()
    assert corps["status"] == "paid"
    assert corps["invoice_number"] == f"FACT-{_annee()}-001"


def test_le_pdf_dun_brouillon_affiche_la_mention_provisoire(tmp_path: Path):
    chemin = InvoicePDFGenerator(output_dir=str(tmp_path)).generate_invoice_pdf(
        invoice_data={
            "invoice_number": "PROV-abc123",
            "document_type": "facture",
            "tva_applicable": True,
            "issue_date": "2026-09-29T00:00:00",
            "due_date": "2026-10-29T00:00:00",
            "status": "draft",
            "subtotal_ht": 100.0,
            "total_tax": 20.0,
            "total_ttc": 120.0,
            "notes": "",
            "lines": [{
                "description": "Conseil",
                "quantity": 1.0,
                "unit_price_ht": 100.0,
                "tva_rate": 20.0,
                "total_ht": 100.0,
                "total_ttc": 120.0,
            }],
        },
        contact_data={"name": "Paul Durand", "company": "", "email": "", "phone": "", "address": "Manosque"},
        user_profile={"name": "Marie Exemple", "company": "Atelier", "address": "Manosque", "siret": "12345678900011"},
    )
    texte = " ".join((page.extract_text() or "").replace("\n", " ") for page in PdfReader(chemin).pages)
    assert "Brouillon, numéro à l'émission" in texte
    assert "PROV-abc123" not in texte
