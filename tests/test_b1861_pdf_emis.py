"""Le PDF déjà produit d'une pièce émise conserve l'identité de son émetteur."""

from pathlib import Path
from unittest.mock import AsyncMock

import pytest
from app.routers import invoices
from app.services.user_profile import UserProfile
from pypdf import PdfReader


@pytest.mark.asyncio
async def test_pdf_historique_non_atteste_est_refuse_sans_modifier_le_fichier(
    client, monkeypatch, tmp_path
):
    from datetime import UTC, datetime

    from app.models import database as db
    from app.models.entities import Invoice

    profil = UserProfile(name="Camille", address="Paris", siret="12345678900010", legal_form="EI")
    monkeypatch.setattr(invoices, "get_cached_profile", lambda: profil)
    monkeypatch.setattr(invoices, "_get_invoice_output_dir", AsyncMock(return_value=str(tmp_path)))
    contact = (await client.post("/api/memory/contacts", json={"first_name": "Alice", "address": "Lyon"})).json()
    piece = (await client.post("/api/invoices/", json={
        "contact_id": contact["id"],
        "lines": [{"description": "Prestation", "quantity": 1, "unit_price_ht": 10}],
    })).json()
    async with db.AsyncSessionLocal() as session:
        brouillon = await session.get(Invoice, piece["id"])
        brouillon.invoice_number = "FACT-HISTORIQUE-001"
        await session.commit()
    chemin = f"/api/invoices/{piece['id']}"
    apercu = await client.get(f"{chemin}/pdf")
    assert apercu.status_code == 200, apercu.text
    fichier = Path(apercu.json()["pdf_path"])
    original = fichier.read_bytes()
    assert "Brouillon" in PdfReader(fichier).pages[0].extract_text()

    # La pièce a été émise par une ancienne version, après cet aperçu.
    async with db.AsyncSessionLocal() as session:
        historique = await session.get(Invoice, piece["id"])
        historique.status = "sent"
        historique.sent_at = datetime.now(UTC)
        await session.commit()

    refus = await client.get(f"{chemin}/pdf")
    assert refus.status_code == 409, refus.text
    ouverture = await client.get(f"{chemin}/pdf-ouverture")
    assert ouverture.status_code == 409, ouverture.text
    assert fichier.read_bytes() == original


@pytest.mark.asyncio
async def test_pdf_archive_modifie_est_refuse_a_la_generation_et_a_l_ouverture(client, monkeypatch, tmp_path):
    profil = UserProfile(name="Camille", address="Paris", siret="12345678900010", legal_form="EI")
    monkeypatch.setattr(invoices, "get_cached_profile", lambda: profil)
    monkeypatch.setattr(invoices, "_get_invoice_output_dir", AsyncMock(return_value=str(tmp_path)))
    contact = (await client.post("/api/memory/contacts", json={"first_name": "Alice", "address": "Lyon"})).json()
    piece = (await client.post("/api/invoices/", json={
        "contact_id": contact["id"],
        "lines": [{"description": "Prestation", "quantity": 1, "unit_price_ht": 10}],
    })).json()
    chemin = f"/api/invoices/{piece['id']}"
    assert (await client.put(chemin, json={"status": "sent"})).status_code == 200
    genere = await client.get(f"{chemin}/pdf")
    assert genere.status_code == 200, genere.text
    fichier = Path(genere.json()["pdf_path"])
    preuve = fichier.with_name(f"{fichier.name}.therese.json")
    assert preuve.stat().st_mode & 0o777 == 0o600
    modifie = fichier.read_bytes() + b"\nmodification"
    fichier.write_bytes(modifie)

    assert (await client.get(f"{chemin}/pdf")).status_code == 409
    assert (await client.get(f"{chemin}/pdf-ouverture")).status_code == 409
    assert fichier.read_bytes() == modifie


@pytest.mark.asyncio
async def test_donnees_archive_alterees_ne_produisent_pas_une_nouvelle_identite(client, monkeypatch, tmp_path):
    import json

    profil = UserProfile(name="Camille Avant", address="Paris", siret="12345678900010", legal_form="EI")
    monkeypatch.setattr(invoices, "get_cached_profile", lambda: profil)
    monkeypatch.setattr(invoices, "_get_invoice_output_dir", AsyncMock(return_value=str(tmp_path)))
    contact = (await client.post("/api/memory/contacts", json={"first_name": "Alice", "address": "Lyon"})).json()
    piece = (await client.post("/api/invoices/", json={
        "contact_id": contact["id"],
        "lines": [{"description": "Prestation", "quantity": 1, "unit_price_ht": 10}],
    })).json()
    chemin = f"/api/invoices/{piece['id']}"
    assert (await client.put(chemin, json={"status": "sent"})).status_code == 200
    genere = await client.get(f"{chemin}/pdf")
    assert genere.status_code == 200, genere.text
    fichier = Path(genere.json()["pdf_path"])
    original = fichier.read_bytes()
    preuve = fichier.with_name(f"{fichier.name}.therese.json")
    donnees = json.loads(preuve.read_text(encoding="utf-8"))
    donnees["user_profile"]["name"] = "Identité altérée"
    preuve.write_text(json.dumps(donnees), encoding="utf-8")
    assert (await client.patch(f"{chemin}/mark-paid", json={})).status_code == 200

    refus = await client.get(f"{chemin}/pdf")
    assert refus.status_code == 409, refus.text
    assert (await client.get(f"{chemin}/pdf-ouverture")).status_code == 409
    assert fichier.read_bytes() == original


@pytest.mark.asyncio
async def test_collision_pendant_publication_ne_certifie_pas_un_fichier_etranger(client, monkeypatch, tmp_path):
    from app.services import invoice_pdf

    profil = UserProfile(name="Camille", address="Paris", siret="12345678900010", legal_form="EI")
    monkeypatch.setattr(invoices, "get_cached_profile", lambda: profil)
    monkeypatch.setattr(invoices, "_get_invoice_output_dir", AsyncMock(return_value=str(tmp_path)))
    contact = (await client.post("/api/memory/contacts", json={"first_name": "Alice", "address": "Lyon"})).json()
    piece = (await client.post("/api/invoices/", json={
        "contact_id": contact["id"],
        "lines": [{"description": "Prestation", "quantity": 1, "unit_price_ht": 10}],
    })).json()
    chemin = f"/api/invoices/{piece['id']}"
    emise = await client.put(chemin, json={"status": "sent"})
    assert emise.status_code == 200, emise.text
    fichier = tmp_path / f"{emise.json()['invoice_number']}.pdf"

    def collision(_provisoire, destination):
        Path(destination).write_bytes(b"fichier concurrent")
        raise FileExistsError

    with monkeypatch.context() as contexte:
        contexte.setattr(invoice_pdf.os, "link", collision)
        refus = await client.get(f"{chemin}/pdf")
    assert refus.status_code == 409, refus.text
    assert fichier.read_bytes() == b"fichier concurrent"
    assert not fichier.with_name(f"{fichier.name}.therese.json").exists()
    assert (await client.get(f"{chemin}/pdf")).status_code == 409


@pytest.mark.asyncio
@pytest.mark.parametrize(("transition", "statut"), [("paiement", "Payée"), ("echeance", "En retard")])
async def test_pdf_actualise_le_statut_sans_reecrire_l_original(
    client, monkeypatch, tmp_path, transition, statut
):
    from datetime import UTC, datetime, timedelta

    from app.services import invoice_status

    profil = UserProfile(name="Camille Avant", address="Paris", siret="12345678900010", legal_form="EI")
    monkeypatch.setattr(invoices, "get_cached_profile", lambda: profil)
    monkeypatch.setattr(invoices, "_get_invoice_output_dir", AsyncMock(return_value=str(tmp_path)))
    contact = (await client.post("/api/memory/contacts", json={"first_name": "Alice", "address": "Lyon"})).json()
    piece = (await client.post("/api/invoices/", json={
        "contact_id": contact["id"],
        "lines": [{"description": "Prestation", "quantity": 1, "unit_price_ht": 10}],
    })).json()
    chemin = f"/api/invoices/{piece['id']}"
    assert (await client.put(chemin, json={"status": "sent"})).status_code == 200
    premier = await client.get(f"{chemin}/pdf")
    assert premier.status_code == 200, premier.text
    original = Path(premier.json()["pdf_path"])
    contenu_original = original.read_bytes()
    assert "Envoyée" in PdfReader(original).pages[0].extract_text()

    profil.name = "Camille Après"
    if transition == "paiement":
        paiement = await client.patch(f"{chemin}/mark-paid", json={})
        assert paiement.status_code == 200, paiement.text
    else:
        class Horloge(datetime):
            @classmethod
            def now(cls, tz=None):
                futur = datetime.now(UTC) + timedelta(days=60)
                return futur.astimezone(tz) if tz else futur.replace(tzinfo=None)

        monkeypatch.setattr(invoice_status, "datetime", Horloge)

    actualise = await client.get(f"{chemin}/pdf")
    assert actualise.status_code == 200, actualise.text
    copie = Path(actualise.json()["pdf_path"])
    texte = " ".join(page.extract_text() for page in PdfReader(copie).pages)
    assert statut in texte
    assert "Camille Avant" in texte and "Camille Après" not in texte
    assert copie != original
    assert original.read_bytes() == contenu_original
    ouverture = await client.get(f"{chemin}/pdf-ouverture")
    assert ouverture.status_code == 200, ouverture.text
    assert ouverture.json()["pdf_path"] == str(copie)
    assert (await client.get(f"{chemin}/pdf")).json()["pdf_path"] == str(copie)


@pytest.mark.asyncio
async def test_pdf_emis_deja_genere_ne_change_pas_apres_modification_du_profil(
    client, monkeypatch, tmp_path
):
    profil = UserProfile(name="Camille Avant", address="Paris", siret="12345678900010", legal_form="EI")
    monkeypatch.setattr(invoices, "get_cached_profile", lambda: profil)
    monkeypatch.setattr(invoices, "_get_invoice_output_dir", AsyncMock(return_value=str(tmp_path)))
    contact = (await client.post("/api/memory/contacts", json={
        "first_name": "Alice", "address": "1 rue du Client, Lyon",
    })).json()
    piece = (await client.post("/api/invoices/", json={
        "contact_id": contact["id"],
        "lines": [{"description": "Prestation", "quantity": 1, "unit_price_ht": 10}],
    })).json()
    chemin = f"/api/invoices/{piece['id']}"
    assert (await client.put(chemin, json={"status": "sent"})).status_code == 200
    premier = await client.get(f"{chemin}/pdf")
    assert premier.status_code == 200, premier.text
    fichier = Path(premier.json()["pdf_path"])
    original = fichier.read_bytes()
    assert "Camille Avant" in PdfReader(fichier).pages[0].extract_text()

    profil.name = "Camille Après"
    second = await client.get(f"{chemin}/pdf")
    assert second.status_code == 200, second.text
    assert second.json()["pdf_path"] == str(fichier)
    assert fichier.read_bytes() == original
    assert "Camille Avant" in PdfReader(fichier).pages[0].extract_text()


@pytest.mark.asyncio
async def test_brouillon_ancien_ne_fait_pas_passer_son_pdf_pour_la_piece_emise(
    client, monkeypatch, tmp_path
):
    from datetime import UTC, datetime

    from app.models import database as db
    from app.models.entities import Invoice

    profil = UserProfile(name="Camille", address="Paris", siret="12345678900010", legal_form="EI")
    monkeypatch.setattr(invoices, "get_cached_profile", lambda: profil)
    monkeypatch.setattr(invoices, "_get_invoice_output_dir", AsyncMock(return_value=str(tmp_path)))
    contact = (await client.post("/api/memory/contacts", json={"first_name": "Alice", "address": "Lyon"})).json()
    piece = (await client.post("/api/invoices/", json={
        "contact_id": contact["id"],
        "lines": [{"description": "Prestation", "quantity": 1, "unit_price_ht": 10}],
    })).json()
    async with db.AsyncSessionLocal() as session:
        brouillon = await session.get(Invoice, piece["id"])
        brouillon.invoice_number = f"FACT-{datetime.now(UTC).year}-001"
        await session.commit()
    chemin = f"/api/invoices/{piece['id']}"
    apercu = await client.get(f"{chemin}/pdf")
    assert apercu.status_code == 200, apercu.text
    fichier = Path(apercu.json()["pdf_path"])
    original = fichier.read_bytes()
    assert "Brouillon" in PdfReader(fichier).pages[0].extract_text()

    refus = await client.put(chemin, json={"status": "sent"})
    assert refus.status_code == 409, refus.text
    assert "PDF" in refus.text and "déplace" in refus.text.lower()
    assert (await client.get(chemin)).json()["status"] == "draft"
    assert fichier.read_bytes() == original
    fichier.rename(tmp_path / "brouillon-conserve.pdf")
    assert (await client.put(chemin, json={"status": "sent"})).status_code == 200
    emis = await client.get(f"{chemin}/pdf")
    assert emis.status_code == 200, emis.text
    assert "Envoyée" in PdfReader(emis.json()["pdf_path"]).pages[0].extract_text()


@pytest.mark.asyncio
async def test_apercu_et_emission_concurrents_ne_melangent_pas_les_pieces(client, monkeypatch, tmp_path):
    import asyncio
    from contextvars import ContextVar
    from datetime import UTC, datetime

    from app.main import app
    from app.models import database as db
    from app.models.entities import Invoice
    from httpx import ASGITransport, AsyncClient

    profil = UserProfile(name="Camille", address="Paris", siret="12345678900010", legal_form="EI")
    monkeypatch.setattr(invoices, "get_cached_profile", lambda: profil)
    contact = (await client.post("/api/memory/contacts", json={"first_name": "Alice", "address": "Lyon"})).json()
    piece = (await client.post("/api/invoices/", json={
        "contact_id": contact["id"],
        "lines": [{"description": "Prestation", "quantity": 1, "unit_price_ht": 10}],
    })).json()
    async with db.AsyncSessionLocal() as session:
        brouillon = await session.get(Invoice, piece["id"])
        brouillon.invoice_number = f"FACT-{datetime.now(UTC).year}-001"
        await session.commit()

    apercu_charge, continuer = asyncio.Event(), asyncio.Event()
    operation = ContextVar("operation_pdf", default="autre")

    async def dossier(_session):
        if operation.get() == "apercu":
            apercu_charge.set()
            await continuer.wait()
        return str(tmp_path)

    monkeypatch.setattr(invoices, "_get_invoice_output_dir", dossier)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as http:
        chemin = f"/api/invoices/{piece['id']}"

        async def demander_apercu():
            jeton = operation.set("apercu")
            try:
                return await http.get(f"{chemin}/pdf")
            finally:
                operation.reset(jeton)

        apercu = asyncio.create_task(demander_apercu())
        try:
            await asyncio.wait_for(apercu_charge.wait(), timeout=5)
            emission = asyncio.create_task(http.put(chemin, json={"status": "sent"}))
            await asyncio.sleep(0.1)
            assert not emission.done(), "L'émission doit attendre la fin de l'aperçu."
        finally:
            continuer.set()
        assert (await asyncio.wait_for(apercu, timeout=10)).status_code == 200
        refus = await asyncio.wait_for(emission, timeout=10)
        assert refus.status_code == 409, refus.text
        assert (await http.get(chemin)).json()["status"] == "draft"
