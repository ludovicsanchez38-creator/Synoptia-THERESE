"""P-135 (persona Nathalie, cycle 13) : l'Accueil ne regardait qu'aujourd'hui.
Sa relance de jeudi n'apparaîtrait que jeudi, et ni l'encaissé ni le pipeline
n'y figuraient. `GET /api/dashboard/semaine` rend ce qui vient sur sept jours
(échéances de tâches, relances datées) et deux chiffres, chacun avec ce qu'il
compte."""

from datetime import date, datetime, time, timedelta

import pytest
from app.models.entities import Contact, Invoice, Task
from httpx import AsyncClient

JOUR = date(2026, 9, 24)  # jeudi


def _a(jours: int, heure: int = 9) -> datetime:
    return datetime.combine(JOUR + timedelta(days=jours), time(heure, 0))


def _facture(numero: str, *, statut: str, paiement: datetime | None, montant: float, type_: str = "facture", devise: str = "EUR") -> Invoice:
    return Invoice(
        contact_id="c-payeur", invoice_number=numero, status=statut, payment_date=paiement, document_type=type_, currency=devise,
        client_name="Client", issue_date=_a(-20), due_date=_a(10), subtotal_ht=montant, total_tax=0.0, total_ttc=montant,
    )


@pytest.mark.asyncio
async def test_la_semaine_a_venir(client: AsyncClient, db_session, monkeypatch):
    monkeypatch.setattr("app.routers.dashboard.date_civile_paris", lambda *_a, **_k: JOUR)
    db_session.add_all([
        Contact(id="c-karim", first_name="Karim", last_name="Benali", stage="discovery", next_follow_up=_a(1)),
        Contact(id="c-lointain", first_name="Loin", last_name="Tain", stage="proposition", next_follow_up=_a(12)),
        Contact(id="c-client", first_name="Déjà", last_name="Client", stage="active"),
        Contact(id="c-contact", first_name="Nouveau", last_name="Contact", stage="contact"),
        Task(id="t-lundi", title="Envoyer le devis", status="todo", due_date=_a(4)),
        Task(id="t-aujourdhui", title="Déjà au brief", status="todo", due_date=_a(0)),
        Task(id="t-faite", title="Faite", status="done", due_date=_a(2)),
        Task(id="t-loin", title="Plus tard", status="todo", due_date=_a(9)),
    ])
    await db_session.commit()

    corps = (await client.get("/api/dashboard/semaine")).json()
    assert [(e["kind"], e["titre"]) for e in corps["a_venir"]] == [
        ("relance", "Relancer Karim Benali"),
        ("tache", "Envoyer le devis"),
    ]
    assert corps["a_venir"][0]["contact_id"] == "c-karim"
    assert corps["prospects_par_etape"] == {"contact": 1, "discovery": 1, "proposition": 1}


@pytest.mark.asyncio
async def test_l_encaisse_du_mois(client: AsyncClient, db_session, monkeypatch):
    monkeypatch.setattr("app.routers.dashboard.date_civile_paris", lambda *_a, **_k: JOUR)
    db_session.add(Contact(id="c-payeur", first_name="Payeur", last_name="Client", stage="active"))
    await db_session.flush()
    db_session.add_all([
        _facture("FACT-1", statut="paid", paiement=_a(-3), montant=1440.0),
        _facture("FACT-2", statut="paid", paiement=datetime(2026, 8, 30, 10, 0), montant=500.0),
        _facture("FACT-3", statut="sent", paiement=None, montant=900.0),
        _facture("DEV-1", statut="paid", paiement=_a(-2), montant=300.0, type_="devis"),
        _facture("FACT-4", statut="paid", paiement=_a(-1), montant=200.0, devise="CHF"),
    ])
    await db_session.commit()

    corps = (await client.get("/api/dashboard/semaine")).json()
    assert corps["encaisse_du_mois"] == {"EUR": 1440.0, "CHF": 200.0}
    assert corps["mois"] == "2026-09"


@pytest.mark.asyncio
async def test_une_base_vide_rend_des_listes_vides(client: AsyncClient):
    corps = (await client.get("/api/dashboard/semaine")).json()
    assert corps["a_venir"] == [] and corps["encaisse_du_mois"] == {} and corps["prospects_par_etape"] == {}
    assert corps["indisponibles"] == []
