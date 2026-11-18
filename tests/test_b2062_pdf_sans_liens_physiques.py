"""B-2062 : publier un PDF sans écraser l'existant sur un volume sans liens physiques."""

import errno
import io
from pathlib import Path
from unittest.mock import Mock

import pytest
from app.services import invoice_pdf
from pypdf import PdfReader


def générer(dossier: Path, document: str = "facture") -> str:
    return invoice_pdf.InvoicePDFGenerator(output_dir=str(dossier)).generate_invoice_pdf(
        invoice_data={
            "invoice_number": "PIECE-2062",
            "document_type": document,
            "issue_date": "2026-07-01",
            "due_date": "2026-07-31",
            "status": "sent",
            "subtotal_ht": 100,
            "total_tax": 20,
            "total_ttc": 120,
            "lines": [{
                "description": "Prestation réalisée",
                "quantity": 1,
                "unit_price_ht": 100,
                "tva_rate": 20,
                "total_ht": 100,
                "total_ttc": 120,
            }],
        },
        contact_data={"name": "Élodie"},
        user_profile={"name": "Camille"},
        conserver_existant=True,
    )


@pytest.mark.parametrize("document", ["facture", "devis"])
@pytest.mark.parametrize("refus", [
    "EPERM", "ENOTSUP", "EOPNOTSUPP", "EXDEV", "ENOSYS", "EMLINK", "EINVAL", "EACCES", "absent",
])
def test_le_pdf_est_publié_intégralement_sans_lien_physique(tmp_path, monkeypatch, document, refus):
    contenus = []

    def lien_refusé(source, destination):
        contenus.append(Path(source).read_bytes())
        raise OSError(getattr(errno, refus), "Lien physique indisponible")

    if refus == "absent":
        monkeypatch.delattr(invoice_pdf.os, "link")
    else:
        monkeypatch.setattr(invoice_pdf.os, "link", lien_refusé)
    synchroniser = Mock(wraps=invoice_pdf.os.fsync)
    monkeypatch.setattr(invoice_pdf.os, "fsync", synchroniser)

    fichier = Path(générer(tmp_path, document))

    if contenus:
        assert fichier.read_bytes() == contenus[0]
    texte = " ".join(page.extract_text() for page in PdfReader(fichier).pages)
    assert "Prestation réalisée" in texte
    assert ("DEVIS" if document == "devis" else "FACTURE") in texte
    synchroniser.assert_called_once()
    assert list(tmp_path.iterdir()) == [fichier]


def test_un_pdf_déjà_présent_n_est_pas_écrasé_sans_lien_physique(tmp_path, monkeypatch):
    fichier = tmp_path / "PIECE-2062.pdf"
    fichier.write_bytes(b"PDF existant")
    monkeypatch.setattr(invoice_pdf.os, "link", Mock(side_effect=OSError(errno.EPERM, "Refusé")))

    with pytest.raises(FileExistsError):
        générer(tmp_path)

    assert fichier.read_bytes() == b"PDF existant"
    assert list(tmp_path.iterdir()) == [fichier]


@pytest.mark.parametrize("étape", ["écriture", "synchronisation"])
def test_un_échec_de_publication_supprime_le_pdf_partiel(tmp_path, monkeypatch, étape):
    fichier = tmp_path / "PIECE-2062.pdf"
    monkeypatch.setattr(invoice_pdf.os, "link", Mock(side_effect=OSError(errno.EPERM, "Refusé")))
    ouvrir_réel = io.open
    écritures = []

    def ouvrir(chemin, mode="r", *args, **kwargs):
        flux = ouvrir_réel(chemin, mode, *args, **kwargs)
        if chemin == fichier and mode == "xb":
            écrire_réel = flux.write

            def écrire(contenu):
                écritures.append(écrire_réel(contenu[:23]))
                flux.flush()
                raise OSError(errno.EIO, "Écriture interrompue")

            monkeypatch.setattr(flux, "write", écrire)
        return flux

    if étape == "écriture":
        monkeypatch.setattr(io, "open", ouvrir)
    else:
        monkeypatch.setattr(invoice_pdf.os, "fsync", Mock(
            side_effect=OSError(errno.EIO, "Synchronisation interrompue"),
        ))

    with pytest.raises(OSError) as erreur:
        générer(tmp_path)

    assert erreur.value.errno == errno.EIO
    if étape == "écriture":
        assert écritures == [23]
    assert list(tmp_path.iterdir()) == []


def test_un_echec_de_publication_preserve_le_fichier_remplace(tmp_path, monkeypatch):
    fichier = tmp_path / "PIECE-2062.pdf"
    tiers = tmp_path / "tiers.pdf"
    tiers.write_bytes(b"PDF du tiers")
    erreur = OSError(errno.EIO, "Synchronisation interrompue")
    monkeypatch.setattr(invoice_pdf.os, "link", Mock(side_effect=OSError(errno.EPERM, "Refusé")))

    def remplacer_avant_echec(_descripteur):
        tiers.replace(fichier)
        raise erreur

    monkeypatch.setattr(invoice_pdf.os, "fsync", remplacer_avant_echec)

    with pytest.raises(OSError) as resultat:
        générer(tmp_path)

    assert resultat.value is erreur
    assert fichier.read_bytes() == b"PDF du tiers"


def test_un_echec_du_nettoyage_preserve_l_erreur_de_publication(tmp_path, monkeypatch):
    fichier = tmp_path / "PIECE-2062.pdf"
    erreur = OSError(errno.EIO, "Synchronisation interrompue")
    monkeypatch.setattr(invoice_pdf.os, "link", Mock(side_effect=OSError(errno.EPERM, "Refusé")))
    monkeypatch.setattr(invoice_pdf.os, "fsync", Mock(side_effect=erreur))
    retirer_reel = Path.unlink
    echecs = []

    def retirer(chemin, *args, **kwargs):
        if chemin == fichier:
            echecs.append(chemin)
            raise OSError(errno.EACCES, "Retrait refusé")
        return retirer_reel(chemin, *args, **kwargs)

    monkeypatch.setattr(Path, "unlink", retirer)

    with pytest.raises(OSError) as resultat:
        générer(tmp_path)

    assert echecs == [fichier]
    assert resultat.value is erreur


def test_un_pdf_apparu_entre_temps_reste_une_erreur_propagée(tmp_path, monkeypatch):
    refus = OSError(errno.EEXIST, "Publication refusée")
    monkeypatch.setattr(invoice_pdf.os, "link", Mock(side_effect=refus))

    with pytest.raises(OSError) as résultat:
        générer(tmp_path)

    assert résultat.value is refus
    assert list(tmp_path.iterdir()) == []
