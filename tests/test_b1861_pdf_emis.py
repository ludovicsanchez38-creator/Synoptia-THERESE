"""Le PDF déjà produit d'une pièce émise conserve l'identité de son émetteur."""

from pathlib import Path
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from app.routers import invoices
from app.services.user_profile import UserProfile
from pypdf import PdfReader


@pytest.mark.asyncio
async def test_brouillons_historiques_isoles_preservent_archive_partagee(client, monkeypatch, tmp_path):
    from sqlalchemy.orm.attributes import set_committed_value

    profil = UserProfile(name="Camille", address="Paris", siret="12345678900010", legal_form="EI")
    monkeypatch.setattr(invoices, "get_cached_profile", lambda: profil)
    monkeypatch.setattr(invoices, "_get_invoice_output_dir", AsyncMock(return_value=str(tmp_path)))
    contact = (await client.post("/api/memory/contacts", json={"first_name": "Alice", "address": "Lyon"})).json()

    async def creer_piece():
        return (await client.post("/api/invoices/", json={
            "contact_id": contact["id"],
            "lines": [{"description": "Prestation", "quantity": 1, "unit_price_ht": 10}],
        })).json()

    emise, premier_brouillon, second_brouillon = [await creer_piece() for _ in range(3)]
    chemin_emis = f"/api/invoices/{emise['id']}"
    transition = await client.put(chemin_emis, json={"status": "sent"})
    assert transition.status_code == 200, transition.text
    numero_partage = transition.json()["invoice_number"]
    archive = await client.get(f"{chemin_emis}/pdf")
    assert archive.status_code == 200, archive.text
    fichier_archive = Path(archive.json()["pdf_path"])
    contenu_archive = fichier_archive.read_bytes()
    preuve = fichier_archive.with_name(f"{fichier_archive.name}.therese.json")
    contenu_preuve = preuve.read_bytes()

    # Deux bases/profils peuvent porter le même numéro dans un dossier partagé.
    charger = invoices._get_invoice_with_lines
    brouillons = {premier_brouillon["id"], second_brouillon["id"]}

    async def charger_profil(session, invoice_id):
        piece = await charger(session, invoice_id)
        if invoice_id in brouillons:
            set_committed_value(piece, "invoice_number", numero_partage)
        return piece

    monkeypatch.setattr(invoices, "_get_invoice_with_lines", charger_profil)
    chemins_apercus = []
    for piece in (premier_brouillon, second_brouillon):
        chemin = f"/api/invoices/{piece['id']}"
        reponse = await client.get(f"{chemin}/pdf")
        assert reponse.status_code == 200, reponse.text
        assert fichier_archive.read_bytes() == contenu_archive, "Archive émise modifiée par un brouillon"
        assert preuve.read_bytes() == contenu_preuve
        apercu = Path(reponse.json()["pdf_path"])
        assert apercu != fichier_archive
        assert "Brouillon" in PdfReader(apercu).pages[0].extract_text()
        ouverture = await client.get(f"{chemin}/pdf-ouverture")
        assert ouverture.status_code == 200, ouverture.text
        assert ouverture.json()["pdf_path"] == str(apercu)
        chemins_apercus.append(apercu)

    assert chemins_apercus[0] != chemins_apercus[1]
    premier_contenu = chemins_apercus[0].read_bytes()
    reponse = await client.get(f"/api/invoices/{premier_brouillon['id']}/pdf")
    assert reponse.status_code == 200, reponse.text
    nouvel_apercu = Path(reponse.json()["pdf_path"])
    assert nouvel_apercu != chemins_apercus[0]
    assert chemins_apercus[0].read_bytes() == premier_contenu
    ouverture = await client.get(f"/api/invoices/{premier_brouillon['id']}/pdf-ouverture")
    assert ouverture.json()["pdf_path"] == str(nouvel_apercu)

    devis = (await client.post("/api/invoices/", json={
        "contact_id": contact["id"], "document_type": "devis",
        "lines": [{"description": "Prestation", "quantity": 1, "unit_price_ht": 10}],
    })).json()
    brouillons.add(devis["id"])
    chemin_devis = f"/api/invoices/{devis['id']}"
    apercu_devis = await client.get(f"{chemin_devis}/pdf")
    assert apercu_devis.status_code == 200, apercu_devis.text
    fichier_devis = Path(apercu_devis.json()["pdf_path"])
    assert (await client.delete(chemin_devis)).status_code == 200
    assert not fichier_devis.exists()
    assert fichier_archive.read_bytes() == contenu_archive
    assert preuve.read_bytes() == contenu_preuve
    assert (await client.get(f"{chemin_emis}/pdf")).status_code == 200
    assert (await client.get(f"{chemin_emis}/pdf-ouverture")).status_code == 200


@pytest.mark.asyncio
async def test_ouverture_retrouve_le_dernier_apercu_sur_un_disque_aux_dates_identiques(
    client, monkeypatch, tmp_path
):
    import os
    from types import SimpleNamespace

    profil = UserProfile(name="Camille", address="Paris", siret="12345678900010", legal_form="EI")
    monkeypatch.setattr(invoices, "get_cached_profile", lambda: profil)
    monkeypatch.setattr(invoices, "_get_invoice_output_dir", AsyncMock(return_value=str(tmp_path)))
    contact = (await client.post("/api/memory/contacts", json={"first_name": "Alice", "address": "Lyon"})).json()
    piece = (await client.post("/api/invoices/", json={
        "contact_id": contact["id"],
        "lines": [{"description": "Prestation", "quantity": 1, "unit_price_ht": 10}],
    })).json()
    chemin = f"/api/invoices/{piece['id']}"
    identifiants = iter([SimpleNamespace(hex="f" * 32), SimpleNamespace(hex="0" * 32)])
    with monkeypatch.context() as contexte:
        contexte.setattr(invoices, "uuid", SimpleNamespace(uuid4=lambda: next(identifiants)))
        premier = await client.get(f"{chemin}/pdf")
        second = await client.get(f"{chemin}/pdf")
    assert premier.status_code == second.status_code == 200
    ancien = Path(premier.json()["pdf_path"])
    recent = Path(second.json()["pdf_path"])
    for fichier in (ancien, recent):
        os.utime(fichier, ns=(1_700_000_000_000_000_000, 1_700_000_000_000_000_000))

    ouverture = await client.get(f"{chemin}/pdf-ouverture")
    assert ouverture.status_code == 200, ouverture.text
    assert ouverture.json()["pdf_path"] == str(recent)


@pytest.mark.asyncio
async def test_preuve_intermittente_ne_bloque_pas_la_reprise_du_pdf(client, monkeypatch, tmp_path):
    profil = UserProfile(name="Camille", address="Paris", siret="12345678900010", legal_form="EI")
    monkeypatch.setattr(invoices, "get_cached_profile", lambda: profil)
    monkeypatch.setattr(invoices, "_get_invoice_output_dir", AsyncMock(return_value=str(tmp_path)))
    contact = (await client.post("/api/memory/contacts", json={"first_name": "Alice", "address": "Lyon"})).json()
    piece = (await client.post("/api/invoices/", json={
        "contact_id": contact["id"],
        "lines": [{"description": "Prestation", "quantity": 1, "unit_price_ht": 10}],
    })).json()
    chemin = f"/api/invoices/{piece['id']}"
    emission = await client.put(chemin, json={"status": "sent"})
    assert emission.status_code == 200, emission.text
    fichier = tmp_path / f"{emission.json()['invoice_number']}.pdf"

    def echec_ecriture(chemin_provisoire, *_args, **_kwargs):
        invoices._preuve_pdf(chemin_provisoire).write_text('{"preuve":', encoding="utf-8")
        raise OSError("incident d'écriture simulé")

    with monkeypatch.context() as contexte:
        contexte.setattr(invoices, "_enregistrer_preuve_pdf", echec_ecriture)
        premier = await client.get(f"{chemin}/pdf")
    assert premier.status_code == 500, premier.text
    publie_avant_reprise = fichier.exists()

    reprise = await client.get(f"{chemin}/pdf")
    assert reprise.status_code == 200, reprise.text
    assert not publie_avant_reprise
    assert Path(reprise.json()["pdf_path"]) == fichier
    assert fichier.with_name(f"{fichier.name}.therese.json").exists()
    assert "Envoyée" in PdfReader(fichier).pages[0].extract_text()
    assert (await client.get(f"{chemin}/pdf-ouverture")).status_code == 200


@pytest.mark.asyncio
@pytest.mark.parametrize("edition", [False, True])
@pytest.mark.parametrize("voie", ["pdf", "pdf-ouverture"])
async def test_interruption_apres_publication_du_pdf_est_reprise(
    client, monkeypatch, tmp_path, edition, voie
):
    profil = UserProfile(name="Camille Avant", address="Paris", siret="12345678900010", legal_form="EI")
    monkeypatch.setattr(invoices, "get_cached_profile", lambda: profil)
    monkeypatch.setattr(invoices, "_get_invoice_output_dir", AsyncMock(return_value=str(tmp_path)))
    contact = (await client.post("/api/memory/contacts", json={"first_name": "Alice", "address": "Lyon"})).json()
    piece = (await client.post("/api/invoices/", json={
        "contact_id": contact["id"],
        "lines": [{"description": "Prestation", "quantity": 1, "unit_price_ht": 10}],
    })).json()
    chemin = f"/api/invoices/{piece['id']}"
    emission = await client.put(chemin, json={"status": "sent"})
    assert emission.status_code == 200, emission.text
    numero = emission.json()["invoice_number"]
    original = tmp_path / f"{numero}.pdf"
    if edition:
        assert (await client.get(f"{chemin}/pdf")).status_code == 200
        contenu_original = original.read_bytes()
        assert (await client.patch(f"{chemin}/mark-paid", json={})).status_code == 200

    lien_reel = invoices.os.link

    def interrompre_compagnon(source, destination, *args, **kwargs):
        if str(destination).endswith(".pdf.therese.json"):
            raise OSError("interruption de publication simulée")
        return lien_reel(source, destination, *args, **kwargs)

    with monkeypatch.context() as contexte:
        contexte.setattr(invoices.os, "link", interrompre_compagnon)
        interrompu = await client.get(f"{chemin}/pdf")
    assert interrompu.status_code == 500, interrompu.text
    fichier = next(tmp_path.glob(f"{numero}--etat-*.pdf")) if edition else original
    contenu = fichier.read_bytes()
    preuve = fichier.with_name(f"{fichier.name}.therese.json")
    assert not preuve.exists()
    profil.name = "Camille Après"

    reprise = await client.get(f"{chemin}/{voie}")
    assert reprise.status_code == 200, reprise.text
    assert reprise.json()["pdf_path"] == str(fichier)
    assert fichier.read_bytes() == contenu
    assert preuve.stat().st_mode & 0o777 == 0o600
    texte = PdfReader(fichier).pages[0].extract_text()
    assert "Camille Avant" in texte and "Camille Après" not in texte
    assert ("Payée" if edition else "Envoyée") in texte
    assert (await client.get(f"{chemin}/pdf")).status_code == 200
    if edition:
        assert original.read_bytes() == contenu_original


@pytest.mark.asyncio
@pytest.mark.parametrize("edition", [False, True])
@pytest.mark.parametrize("voie", ["pdf", "pdf-ouverture"])
async def test_restauration_reprend_la_publication_interrompue(client, monkeypatch, tmp_path, edition, voie):
    from app.config import settings

    dossier = Path(settings.data_dir) / "invoices" / f"{tmp_path.name}-{uuid4().hex}"
    profil = UserProfile(name="Camille Avant", address="Paris", siret="12345678900010", legal_form="EI")
    monkeypatch.setattr(invoices, "get_cached_profile", lambda: profil)
    monkeypatch.setattr(invoices, "_get_invoice_output_dir", AsyncMock(return_value=str(dossier)))
    contact = (await client.post("/api/memory/contacts", json={"first_name": "Alice", "address": "Lyon"})).json()
    piece = (await client.post("/api/invoices/", json={
        "contact_id": contact["id"],
        "lines": [{"description": "Prestation", "quantity": 1, "unit_price_ht": 10}],
    })).json()
    chemin = f"/api/invoices/{piece['id']}"
    emission = await client.put(chemin, json={"status": "sent"})
    assert emission.status_code == 200, emission.text
    numero = emission.json()["invoice_number"]
    original = dossier / f"{numero}.pdf"
    if edition:
        assert (await client.get(f"{chemin}/pdf")).status_code == 200
        contenu_original = original.read_bytes()
        assert (await client.patch(f"{chemin}/mark-paid", json={})).status_code == 200

    lien_reel = invoices.os.link

    def interrompre_compagnon(source, destination, *args, **kwargs):
        if str(destination).endswith(".pdf.therese.json"):
            raise OSError("interruption de publication simulée")
        return lien_reel(source, destination, *args, **kwargs)

    with monkeypatch.context() as contexte:
        contexte.setattr(invoices.os, "link", interrompre_compagnon)
        assert (await client.get(f"{chemin}/pdf")).status_code == 500
    fichier = next(dossier.glob(f"{numero}--etat-*.pdf")) if edition else original
    contenu = fichier.read_bytes()
    provisoire = next(dossier.glob(".therese-publication-*.pdf"))
    assert invoices._meme_fichier(provisoire, fichier)
    assert not invoices._preuve_pdf(fichier).exists()

    passe = "Passphrase-test-publication"
    sauvegarde = await client.post("/api/data/backup", json={"password": passe})
    assert sauvegarde.status_code == 200, sauvegarde.text
    profil.name = "Camille Après"
    restauration = await client.post(
        f"/api/data/restore/{sauvegarde.json()['backup_name']}?confirm=true", json={"password": passe},
    )
    assert restauration.status_code == 200, restauration.text
    assert fichier.exists(), "Le PDF publié a disparu après restauration"
    assert invoices._meme_fichier(provisoire, fichier)

    reprise = await client.get(f"{chemin}/{voie}")
    assert reprise.status_code == 200, reprise.text
    assert reprise.json()["pdf_path"] == str(fichier)
    assert fichier.read_bytes() == contenu
    assert invoices._preuve_pdf(fichier).stat().st_mode & 0o777 == 0o600
    texte = PdfReader(fichier).pages[0].extract_text()
    assert "Camille Avant" in texte and "Camille Après" not in texte
    assert ("Payée" if edition else "Envoyée") in texte
    assert (await client.get(f"{chemin}/pdf")).status_code == 200
    if edition:
        assert original.read_bytes() == contenu_original


@pytest.mark.asyncio
@pytest.mark.parametrize("edition", [False, True])
@pytest.mark.parametrize("voie", ["pdf", "pdf-ouverture"])
async def test_restauration_apres_echec_du_nettoyage_du_compagnon(
    client, monkeypatch, tmp_path, edition, voie
):
    import tarfile

    from app.config import settings
    from app.services.encryption import decrypt_backup_archive

    dossier = Path(settings.data_dir) / "invoices" / f"{tmp_path.name}-{uuid4().hex}"
    profil = UserProfile(name="Camille Avant", address="Paris", siret="12345678900010", legal_form="EI")
    monkeypatch.setattr(invoices, "get_cached_profile", lambda: profil)
    monkeypatch.setattr(invoices, "_get_invoice_output_dir", AsyncMock(return_value=str(dossier)))
    contact = (await client.post("/api/memory/contacts", json={"first_name": "Alice", "address": "Lyon"})).json()
    piece = (await client.post("/api/invoices/", json={
        "contact_id": contact["id"],
        "lines": [{"description": "Prestation", "quantity": 1, "unit_price_ht": 10}],
    })).json()
    chemin = f"/api/invoices/{piece['id']}"
    emission = await client.put(chemin, json={"status": "sent"})
    assert emission.status_code == 200, emission.text
    original = dossier / f"{emission.json()['invoice_number']}.pdf"
    if edition:
        assert (await client.get(f"{chemin}/pdf")).status_code == 200
        contenu_original = original.read_bytes()
        assert (await client.patch(f"{chemin}/mark-paid", json={})).status_code == 200

    unlink_reel = Path.unlink
    echecs = []

    def echec_compagnon_provisoire(self, *args, **kwargs):
        if self.name.startswith(".therese-publication-") and self.name.endswith(".pdf.therese.json"):
            echecs.append(self)
            raise OSError("nettoyage du compagnon interrompu")
        return unlink_reel(self, *args, **kwargs)

    with monkeypatch.context() as contexte:
        contexte.setattr(Path, "unlink", echec_compagnon_provisoire)
        publication = await client.get(f"{chemin}/pdf")
    assert publication.status_code == 200, publication.text
    assert len(echecs) == 1
    fichier = Path(publication.json()["pdf_path"])
    contenu = fichier.read_bytes()
    preuve = invoices._preuve_pdf(fichier)
    contenu_preuve = preuve.read_bytes()

    passe = "Passphrase-test-publication"
    sauvegarde = await client.post("/api/data/backup", json={"password": passe})
    assert sauvegarde.status_code == 200, sauvegarde.text
    archive = tmp_path / "sauvegarde.tar.gz"
    chiffree = Path(settings.data_dir) / "backups" / f"{sauvegarde.json()['backup_name']}.tar.gz.enc"
    decrypt_backup_archive(chiffree, archive, passe)
    with tarfile.open(archive, "r:gz") as tar:
        membre_preuve = str(preuve.relative_to(settings.data_dir))
        assert tar.getmember(membre_preuve).islnk()
    profil.name = "Camille Après"
    restauration = await client.post(
        f"/api/data/restore/{sauvegarde.json()['backup_name']}?confirm=true", json={"password": passe},
    )
    assert restauration.status_code == 200, restauration.text
    assert preuve.exists(), "Le compagnon final a disparu après restauration"
    assert preuve.read_bytes() == contenu_preuve
    assert fichier.read_bytes() == contenu
    assert invoices._meme_fichier(echecs[0], preuve)
    assert invoices._meme_fichier(Path(str(echecs[0]).removesuffix(".therese.json")), fichier)

    reprise = await client.get(f"{chemin}/{voie}")
    assert reprise.status_code == 200, reprise.text
    assert reprise.json()["pdf_path"] == str(fichier)
    assert (await client.get(f"{chemin}/pdf")).status_code == 200
    texte = PdfReader(fichier).pages[0].extract_text()
    assert "Camille Avant" in texte and "Camille Après" not in texte
    assert ("Payée" if edition else "Envoyée") in texte
    if edition:
        assert original.read_bytes() == contenu_original


@pytest.mark.asyncio
@pytest.mark.parametrize("alteration", ["pdf_remplace", "preuve_modifiee"])
async def test_reprise_ne_certifie_pas_un_fichier_etranger_ou_une_preuve_alteree(
    client, monkeypatch, tmp_path, alteration
):
    import json

    profil = UserProfile(name="Camille", address="Paris", siret="12345678900010", legal_form="EI")
    monkeypatch.setattr(invoices, "get_cached_profile", lambda: profil)
    monkeypatch.setattr(invoices, "_get_invoice_output_dir", AsyncMock(return_value=str(tmp_path)))
    contact = (await client.post("/api/memory/contacts", json={"first_name": "Alice", "address": "Lyon"})).json()
    piece = (await client.post("/api/invoices/", json={
        "contact_id": contact["id"],
        "lines": [{"description": "Prestation", "quantity": 1, "unit_price_ht": 10}],
    })).json()
    chemin = f"/api/invoices/{piece['id']}"
    emission = await client.put(chemin, json={"status": "sent"})
    assert emission.status_code == 200, emission.text
    fichier = tmp_path / f"{emission.json()['invoice_number']}.pdf"
    preuve = fichier.with_name(f"{fichier.name}.therese.json")
    lien_reel = invoices.os.link

    def interrompre_compagnon(source, destination, *args, **kwargs):
        if Path(destination) == preuve:
            raise OSError("interruption de publication simulée")
        return lien_reel(source, destination, *args, **kwargs)

    with monkeypatch.context() as contexte:
        contexte.setattr(invoices.os, "link", interrompre_compagnon)
        assert (await client.get(f"{chemin}/pdf")).status_code == 500
    contenu = fichier.read_bytes()
    if alteration == "pdf_remplace":
        # Les mêmes octets dans un autre inode ne prouvent pas la publication.
        autre = tmp_path / "fichier-etranger"
        autre.write_bytes(contenu)
        autre.replace(fichier)
    else:
        provisoire = next(tmp_path.glob(".therese-publication-*.pdf.therese.json"))
        donnees = json.loads(provisoire.read_text(encoding="utf-8"))
        donnees["user_profile"]["name"] = "Identité altérée"
        provisoire.write_text(json.dumps(donnees), encoding="utf-8")

    assert (await client.get(f"{chemin}/pdf")).status_code == 409
    assert not preuve.exists()
    assert fichier.read_bytes() == contenu


@pytest.mark.asyncio
@pytest.mark.parametrize("alteration", ["remplacement", "deplacement"])
async def test_changement_du_pdf_pendant_la_finalisation_ne_la_certifie_pas(
    client, monkeypatch, tmp_path, alteration
):
    profil = UserProfile(name="Camille", address="Paris", siret="12345678900010", legal_form="EI")
    monkeypatch.setattr(invoices, "get_cached_profile", lambda: profil)
    monkeypatch.setattr(invoices, "_get_invoice_output_dir", AsyncMock(return_value=str(tmp_path)))
    contact = (await client.post("/api/memory/contacts", json={"first_name": "Alice", "address": "Lyon"})).json()
    piece = (await client.post("/api/invoices/", json={
        "contact_id": contact["id"],
        "lines": [{"description": "Prestation", "quantity": 1, "unit_price_ht": 10}],
    })).json()
    chemin = f"/api/invoices/{piece['id']}"
    emission = await client.put(chemin, json={"status": "sent"})
    assert emission.status_code == 200, emission.text
    fichier = tmp_path / f"{emission.json()['invoice_number']}.pdf"
    preuve = fichier.with_name(f"{fichier.name}.therese.json")
    lien_reel = invoices.os.link

    def modifier_pendant_le_lien(source, destination, *args, **kwargs):
        if Path(destination) == preuve:
            autre = tmp_path / "autre-fichier"
            if alteration == "remplacement":
                autre.write_bytes(fichier.read_bytes())
                autre.replace(fichier)
            else:
                fichier.rename(autre)
        return lien_reel(source, destination, *args, **kwargs)

    with monkeypatch.context() as contexte:
        contexte.setattr(invoices.os, "link", modifier_pendant_le_lien)
        refus = await client.get(f"{chemin}/pdf")
    assert refus.status_code == 409, refus.text
    assert not preuve.exists()
    if alteration == "remplacement":
        assert (await client.get(f"{chemin}/pdf")).status_code == 409
        assert not preuve.exists()


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

    lien_reel = invoice_pdf.os.link

    def collision(provisoire, destination):
        if Path(destination) != fichier:
            return lien_reel(provisoire, destination)
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
@pytest.mark.parametrize("voie", ["envoi", "paiement"])
@pytest.mark.parametrize("type_compagnon", ["fichier", "lien_rompu"])
async def test_compagnon_sans_pdf_bloque_la_premiere_emission(client, monkeypatch, tmp_path, voie, type_compagnon):
    profil = UserProfile(name="Camille", address="Paris", siret="12345678900010", legal_form="EI")
    monkeypatch.setattr(invoices, "get_cached_profile", lambda: profil)
    monkeypatch.setattr(invoices, "_get_invoice_output_dir", AsyncMock(return_value=str(tmp_path)))
    contact = (await client.post("/api/memory/contacts", json={"first_name": "Alice", "address": "Lyon"})).json()
    piece = (await client.post("/api/invoices/", json={
        "contact_id": contact["id"],
        "lines": [{"description": "Prestation", "quantity": 1, "unit_price_ht": 10}],
    })).json()
    chemin = f"/api/invoices/{piece['id']}"
    numero = f"FACT-{invoices._date_demission().year}-001"
    compagnon = tmp_path / f"{numero}.pdf.therese.json"
    if type_compagnon == "fichier":
        compagnon.write_bytes(b"compagnon a conserver")
    else:
        compagnon.symlink_to(tmp_path / "cible-absente")

    async def emettre():
        if voie == "envoi":
            return await client.put(chemin, json={"status": "sent"})
        return await client.patch(f"{chemin}/mark-paid", json={})

    refus = await emettre()
    assert refus.status_code == 409, refus.text
    assert "compagnon" in refus.text.lower() and "déplace" in refus.text.lower()
    brouillon = (await client.get(chemin)).json()
    assert brouillon["status"] == "draft"
    assert brouillon["invoice_number"] == piece["invoice_number"]
    if type_compagnon == "lien_rompu":
        assert compagnon.is_symlink()
    else:
        assert compagnon.read_bytes() == b"compagnon a conserver"

    conserve = compagnon.rename(tmp_path / "compagnon-conserve")
    emission = await emettre()
    assert emission.status_code == 200, emission.text
    assert emission.json()["invoice_number"] == numero
    pdf = await client.get(f"{chemin}/pdf")
    assert pdf.status_code == 200, pdf.text
    assert ("Payée" if voie == "paiement" else "Envoyée") in PdfReader(pdf.json()["pdf_path"]).pages[0].extract_text()
    if type_compagnon == "lien_rompu":
        assert conserve.is_symlink()
    else:
        assert conserve.read_bytes() == b"compagnon a conserver"


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
