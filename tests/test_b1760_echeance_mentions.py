"""B-1760 : une conversion différée imprimait deux échéances dans le PDF.

Les requêtes HTTP traversent le routeur et la base SQLCipher des fixtures.
Seules l'horloge et l'identité synthétique de l'émetteur sont substituées.
Les mentions particulières sont introduites en base comme données historiques,
car CreateInvoiceRequest et UpdateInvoiceRequest ne proposent pas ce champ.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pytest
from app.models import database as db
from app.models.entities import Invoice
from app.routers import invoices as factures
from app.services.user_profile import UserProfile
from httpx import AsyncClient
from pypdf import PdfReader
from sqlmodel import Session

_CONVERSION = datetime(2026, 10, 1, 9, tzinfo=UTC)
_EMISSION = datetime(2026, 10, 8, 9, tzinfo=UTC)
_CONDITIONS = "60 jours convenus"
_REGLEMENT = "Virement bancaire convenu"
_NOTES = "Conditions négociées conservées, référence synthétique B1760."
_LIGNE_INITIALE = "Date d'échéance : 30/11/2026."


def _dossier_preuve(identifiant: str, nature: str) -> Path | None:
    destination = os.environ.get("B1760_PREUVES")
    if not destination:
        return None
    dossier = Path(destination).expanduser().resolve() / f"{nature}-{identifiant}-{uuid4().hex}"
    dossier.mkdir(parents=True, exist_ok=False)
    return dossier


def _empreinte(chemin: Path) -> dict:
    return {
        "path": str(chemin.resolve()),
        "sha256": hashlib.sha256(chemin.read_bytes()).hexdigest(),
        "bytes": chemin.stat().st_size,
    }


def _date_json(valeur):
    if isinstance(valeur, datetime):
        return valeur.isoformat()
    raise TypeError(f"Type non sérialisable dans une preuve B1760 : {type(valeur).__name__}")


def _ecrire_json(chemin: Path, valeur: dict) -> None:
    chemin.write_text(
        json.dumps(valeur, ensure_ascii=False, indent=2, default=_date_json) + "\n",
        encoding="utf-8",
    )


@pytest.fixture
def horloge(monkeypatch: pytest.MonkeyPatch):
    class Horloge(datetime):
        instant = _CONVERSION

        @classmethod
        def now(cls, tz=None):  # type: ignore[override]
            if tz is None:
                return cls.instant.replace(tzinfo=None)
            return cls.instant.astimezone(tz)

    monkeypatch.setattr(factures, "datetime", Horloge)
    return Horloge


def _base_chiffree() -> None:
    assert db._db_cipher_active, "Le scénario doit exercer SQLCipher."
    assert db.db_is_encrypted(db.settings.db_path)
    assert db.sync_engine is not None


def _piece_en_base(identifiant: str) -> dict:
    _base_chiffree()
    with Session(db.sync_engine) as session:
        piece = session.get(Invoice, identifiant)
        assert piece is not None
        return piece.model_dump()


def _contenu_fige(identifiant: str) -> dict:
    return {
        champ: valeur for champ, valeur in _piece_en_base(identifiant).items()
        if champ not in {"status", "payment_date", "updated_at"}
    }


def _mentions_historiques(
    identifiant: str, mentions: str | None, taux: float | None = None,
) -> None:
    _base_chiffree()
    with Session(db.sync_engine) as session:
        piece = session.get(Invoice, identifiant)
        assert piece is not None
        piece.legal_mentions = mentions
        if taux is not None:
            piece.late_penalty_rate = taux
        session.add(piece)
        session.commit()


async def _brouillon_converti(client: AsyncClient, devise: str = "EUR") -> dict:
    _base_chiffree()
    contact = await client.post(
        "/api/memory/contacts",
        json={"first_name": "Client", "last_name": "Synthétique B1760"},
    )
    assert contact.status_code == 200, contact.text
    devis = await client.post("/api/invoices/", json={
        "contact_id": contact.json()["id"],
        "document_type": "devis",
        "currency": devise,
        "notes": _NOTES,
        "lines": [{
            "description": "Prestation synthétique",
            "quantity": 1,
            "unit_price_ht": 100,
            "tva_rate": 20,
        }],
    })
    assert devis.status_code == 200, devis.text
    conversion = await client.post(
        f"/api/invoices/{devis.json()['id']}/convert-to-invoice",
        json={"payment_terms": _CONDITIONS, "payment_method": _REGLEMENT},
    )
    assert conversion.status_code == 200, conversion.text
    corps = conversion.json()
    assert corps["status"] == "draft"
    assert corps["invoice_number"].startswith("PROV-")
    assert corps["due_date"].startswith("2026-11-30")
    assert corps["legal_mentions"].startswith(_LIGNE_INITIALE + "\n")
    assert _piece_en_base(corps["id"])["legal_mentions"] == corps["legal_mentions"]
    return corps


async def _emettre(
    client: AsyncClient, identifiant: str, porte: str, **champs,
) -> dict:
    if porte == "mark-paid":
        assert not champs, "mark-paid ne propose pas d'édition de l'échéance."
        reponse = await client.patch(f"/api/invoices/{identifiant}/mark-paid", json={})
    else:
        reponse = await client.put(
            f"/api/invoices/{identifiant}", json={"status": porte, **champs},
        )
    assert reponse.status_code == 200, reponse.text
    return reponse.json()


def _conditions_conservees(avant: dict, apres: dict) -> None:
    for champ in (
        "currency", "notes", "payment_terms", "payment_method", "late_penalty_rate",
        "converted_from_id", "contact_id", "subtotal_ht", "total_tax", "total_ttc", "lines",
    ):
        assert apres[champ] == avant[champ], champ


async def _texte_pdf(
    client: AsyncClient, identifiant: str, monkeypatch: pytest.MonkeyPatch,
) -> str:
    profil = UserProfile(
        name="Émetteur synthétique",
        company="Société Exemple",
        address="Adresse synthétique",
        siret="12345678900011",
    )
    assert profil.is_billing_complete()
    with monkeypatch.context() as contexte:
        contexte.setattr(factures, "get_cached_profile", lambda: profil)
        reponse = await client.get(f"/api/invoices/{identifiant}/pdf")
    assert reponse.status_code == 200, reponse.text
    chemin = Path(reponse.json()["pdf_path"]).resolve()
    assert chemin.is_relative_to(Path(db.settings.data_dir).resolve())
    assert chemin.is_file()
    pages = [page.extract_text() or "" for page in PdfReader(chemin).pages]
    assert pages
    dossier = _dossier_preuve(identifiant, "pdf")
    if dossier is not None:
        copie = dossier / "piece.pdf"
        shutil.copyfile(chemin, copie)
        texte = dossier / "texte-extrait.txt"
        texte.write_text("\n\f\n".join(pages), encoding="utf-8")
        _ecrire_json(dossier / "preuve-pdf.json", {
            "id": identifiant,
            "response_http": reponse.json(),
            "source_pdf": _empreinte(chemin),
            "pdf": _empreinte(copie),
            "texte_extrait": _empreinte(texte),
            "page_count": len(pages),
            "pages": pages,
        })
    return " ".join(page.replace("\n", " ") for page in pages)


def _echeance_coherente(avant: dict, apres: dict, iso: str, imprimee: str) -> None:
    en_base = _piece_en_base(apres["id"])
    dossier = _dossier_preuve(apres["id"], "echeance-http-base")
    if dossier is not None:
        avant_path = dossier / "brouillon-converti.json"
        emise_path = dossier / "reponse-emise.json"
        persistee_path = dossier / "relecture-persistee.json"
        _ecrire_json(avant_path, avant)
        _ecrire_json(emise_path, apres)
        _ecrire_json(persistee_path, en_base)
        _ecrire_json(dossier / "preuve-echeance.json", {
            "id": apres["id"],
            "expected_due_date_iso": iso,
            "expected_due_date_printed": imprimee,
            "brouillon_converti": _empreinte(avant_path),
            "reponse_emise": _empreinte(emise_path),
            "relecture_persistee": _empreinte(persistee_path),
        })
    assert apres["issue_date"].startswith("2026-10-08")
    assert apres["due_date"].startswith(iso)
    assert apres["invoice_number"] == "FACT-2026-001"
    suffixe = avant["legal_mentions"][len(_LIGNE_INITIALE):]
    assert apres["legal_mentions"] == f"Date d'échéance : {imprimee}." + suffixe
    _conditions_conservees(avant, apres)
    assert en_base["due_date"].date().isoformat() == iso
    assert en_base["legal_mentions"] == apres["legal_mentions"]
    for champ in ("notes", "payment_terms", "payment_method", "late_penalty_rate", "currency"):
        assert en_base[champ] == avant[champ]


@pytest.mark.asyncio
@pytest.mark.parametrize("devise", ["EUR", "USD"])
@pytest.mark.parametrize("porte", ["sent", "mark-paid"])
async def test_conversion_differee_une_seule_echeance_http_base_et_pdf(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch, horloge, devise: str, porte: str,
):
    brouillon = await _brouillon_converti(client, devise)
    horloge.instant = _EMISSION
    emise = await _emettre(client, brouillon["id"], porte)
    assert emise["status"] == ("paid" if porte == "mark-paid" else "sent")
    _echeance_coherente(brouillon, emise, "2026-12-07", "07/12/2026")
    relue = await client.get(f"/api/invoices/{emise['id']}")
    assert relue.status_code == 200, relue.text
    assert relue.json()["legal_mentions"] == emise["legal_mentions"]
    fige = _contenu_fige(emise["id"])
    texte = await _texte_pdf(client, emise["id"], monkeypatch)
    assert texte.count("07/12/2026") >= 2, "En-tête et mentions portent la même échéance."
    assert "30/11/2026" not in texte
    assert _CONDITIONS in texte
    assert _REGLEMENT in texte
    assert _NOTES in texte
    if devise == "EUR":
        assert "11,62 %" in texte
        assert "40 EUR" in texte
    else:
        assert "40 EUR" not in texte
        assert "11,62 %" not in texte
        assert "conditions convenues entre les parties" in texte
    assert _contenu_fige(emise["id"]) == fige, "La génération PDF ne réécrit pas la pièce."


@pytest.mark.asyncio
@pytest.mark.parametrize("moment,porte", [
    ("avant", "sent"),
    ("avant", "mark-paid"),
    ("pendant", "sent"),
    ("pendant", "paid"),
])
async def test_echeance_editee_sur_brouillon_avant_ou_pendant_emission(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch, horloge, moment: str, porte: str,
):
    brouillon = await _brouillon_converti(client)
    modification = {"due_date": "2026-12-15T09:00:00", "issue_date": brouillon["issue_date"]}
    if moment == "avant":
        horloge.instant = datetime(2026, 10, 3, 9, tzinfo=UTC)
        edition = await client.put(f"/api/invoices/{brouillon['id']}", json=modification)
        assert edition.status_code == 200, edition.text
        editee = edition.json()
        assert editee["status"] == "draft"
        assert editee["invoice_number"] == brouillon["invoice_number"]
        assert editee["due_date"].startswith("2026-12-15")
        assert editee["legal_mentions"] == (
            "Date d'échéance : 15/12/2026."
            + brouillon["legal_mentions"][len(_LIGNE_INITIALE):]
        )
        assert _piece_en_base(editee["id"])["legal_mentions"] == editee["legal_mentions"]
        _conditions_conservees(brouillon, editee)
        modification = {}
    horloge.instant = _EMISSION
    emise = await _emettre(client, brouillon["id"], porte, **modification)
    _echeance_coherente(brouillon, emise, "2026-12-22", "22/12/2026")
    texte = await _texte_pdf(client, emise["id"], monkeypatch)
    assert texte.count("22/12/2026") >= 2
    assert "30/11/2026" not in texte
    assert "15/12/2026" not in texte
    assert _CONDITIONS in texte


@pytest.mark.asyncio
@pytest.mark.parametrize("devise", ["EUR", "USD"])
async def test_seule_la_premiere_ligne_reconnue_change_suffixe_et_taux_conserves(
    client: AsyncClient, horloge, devise: str,
):
    brouillon = await _brouillon_converti(client, devise)
    suffixe = (
        "\nClause négociée : pénalité de 9,87 % selon accord.\n\n"
        "  Espaces convenus et accents : règlement.  \n"
        "Référence historique, à conserver :\n" + _LIGNE_INITIALE + "\n"
    )
    _mentions_historiques(brouillon["id"], _LIGNE_INITIALE + suffixe, taux=9.87)
    horloge.instant = _EMISSION
    emise = await _emettre(client, brouillon["id"], "sent")
    assert emise["legal_mentions"] == "Date d'échéance : 07/12/2026." + suffixe
    assert emise["legal_mentions"].partition("\n")[2].encode() == suffixe[1:].encode()
    assert emise["late_penalty_rate"] == 9.87
    assert emise["payment_terms"] == _CONDITIONS
    assert emise["payment_method"] == _REGLEMENT
    assert emise["notes"] == _NOTES
    en_base = _piece_en_base(emise["id"])
    assert en_base["legal_mentions"] == emise["legal_mentions"]
    assert en_base["late_penalty_rate"] == 9.87
    assert en_base["currency"] == devise


@pytest.mark.asyncio
@pytest.mark.parametrize("mentions", [
    pytest.param(None, id="absentes"),
    pytest.param("Clause particulière sans échéance automatique.", id="texte-libre"),
    pytest.param("Date d'échéance : 05/12/2026.\nClause convenue.", id="autre-date"),
    pytest.param("Date d’échéance : 30/11/2026.\nClause convenue.", id="apostrophe-personnalisee"),
    pytest.param(_LIGNE_INITIALE + " Clause convenue.", id="ajout-sur-meme-ligne"),
    pytest.param("Préambule négocié.\n" + _LIGNE_INITIALE, id="ligne-interieure"),
    pytest.param(_LIGNE_INITIALE + "\r\nClause convenue.", id="separateur-personnalise"),
])
async def test_mentions_non_reconnues_preservees_a_edition_et_emission(
    client: AsyncClient, horloge, mentions: str | None,
):
    brouillon = await _brouillon_converti(client)
    _mentions_historiques(brouillon["id"], mentions)
    edition = await client.put(
        f"/api/invoices/{brouillon['id']}", json={"due_date": "2026-12-15T09:00:00"},
    )
    assert edition.status_code == 200, edition.text
    assert edition.json()["legal_mentions"] == mentions
    assert _piece_en_base(brouillon["id"])["legal_mentions"] == mentions
    horloge.instant = _EMISSION
    emise = await _emettre(client, brouillon["id"], "sent")
    assert emise["due_date"].startswith("2026-12-22")
    assert emise["legal_mentions"] == mentions
    assert _piece_en_base(emise["id"])["legal_mentions"] == mentions
    _conditions_conservees(brouillon, emise)


@pytest.mark.asyncio
@pytest.mark.parametrize("porte", ["sent", "mark-paid"])
async def test_echeance_et_mentions_emises_immuables_aux_statuts_paiement_et_pdf(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch, horloge, porte: str,
):
    brouillon = await _brouillon_converti(client)
    horloge.instant = _EMISSION
    emise = await _emettre(client, brouillon["id"], porte)
    _echeance_coherente(brouillon, emise, "2026-12-07", "07/12/2026")
    fige = _contenu_fige(emise["id"])
    horloge.instant = datetime(2026, 10, 20, 9, tzinfo=UTC)
    for modification in (
        {"due_date": "2026-12-31"},
        {"issue_date": "2026-10-20"},
        {"notes": "Réécriture refusée"},
        {"currency": "USD"},
    ):
        reponse = await client.put(f"/api/invoices/{emise['id']}", json=modification)
        assert reponse.status_code == 409, reponse.text
        assert _contenu_fige(emise["id"]) == fige
    statut = await client.put(f"/api/invoices/{emise['id']}", json={"status": "paid"})
    assert statut.status_code == 200, statut.text
    paiement = await client.patch(
        f"/api/invoices/{emise['id']}/mark-paid", json={"payment_date": "2026-10-09"},
    )
    assert paiement.status_code == 200, paiement.text
    assert paiement.json()["due_date"].startswith("2026-12-07")
    assert paiement.json()["legal_mentions"] == emise["legal_mentions"]
    assert _contenu_fige(emise["id"]) == fige
    texte = await _texte_pdf(client, emise["id"], monkeypatch)
    assert texte.count("07/12/2026") >= 2
    assert "30/11/2026" not in texte
    assert _contenu_fige(emise["id"]) == fige
