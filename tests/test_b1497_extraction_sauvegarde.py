"""B-1497 : restaurer une archive écrivait hors des entrées attendues.

`tar.extractall(dest, filter="data")` n'écarte que ce qui sort du dossier
de destination. Dans le dossier des données, il laissait passer un membre
`outputs/../x` et un lien interne `outputs/t -> ../backups` suivi de
`outputs/t/x` : une archive piégée ou abîmée pouvait écraser les autres
sauvegardes, dont l'archive de sécurité qui sert au retour arrière.
"""

import io
import os
import tarfile

import pytest
from fastapi import HTTPException


def _archive(tmp_path, membres) -> tarfile.TarFile:
    chemin = tmp_path / "piege.tar.gz"
    with tarfile.open(chemin, "w:gz") as tar:
        for nom, lien in membres:
            info = tarfile.TarInfo(nom)
            if lien is not None:
                info.type = tarfile.SYMTYPE
                info.linkname = lien
                tar.addfile(info)
            else:
                contenu = b"piege"
                info.size = len(contenu)
                tar.addfile(info, io.BytesIO(contenu))
    return tarfile.open(chemin, "r:gz")


def _extraire(tmp_path, membres):
    from app.routers.data import _safe_extractall

    donnees = tmp_path / "donnees"
    (donnees / "backups").mkdir(parents=True)
    with _archive(tmp_path, membres) as tar, pytest.raises(HTTPException) as refus:
        _safe_extractall(tar, donnees)
    assert refus.value.status_code == 400
    return donnees


def test_un_chemin_qui_remonte_est_refuse_sans_rien_ecrire(tmp_path):
    donnees = _extraire(tmp_path, [("therese.db", None), ("outputs/../intrus.txt", None)])
    assert not (donnees / "intrus.txt").exists()
    assert not (donnees / "therese.db").exists()


def test_un_lien_interne_n_est_pas_suivi(tmp_path):
    """Un lien n'est pas extrait : ce qui passait « à travers » lui devient un
    fichier ordinaire de son entrée, jamais une écriture dans `backups/`."""
    from app.routers.data import _safe_extractall

    donnees = tmp_path / "donnees"
    (donnees / "backups").mkdir(parents=True)
    with _archive(tmp_path, [("outputs/t", "../backups"), ("outputs/t/pre_restore.tar.gz", None)]) as tar:
        _safe_extractall(tar, donnees)
    assert list((donnees / "backups").iterdir()) == []
    assert not (donnees / "outputs" / "t").is_symlink()


def test_une_sauvegarde_qui_contient_un_lien_se_restaure_quand_meme(tmp_path):
    """Régression de la première version de B-1497 : un lien posé à la main
    dans un dossier de données rendait toute la sauvegarde irrestaurable."""
    from app.routers.data import _safe_extractall

    donnees = tmp_path / "donnees"
    donnees.mkdir()
    membres = [("therese.db", None), ("projects/raccourci", "../outputs"), ("outputs/devis.pdf", None)]
    with _archive(tmp_path, membres) as tar:
        _safe_extractall(tar, donnees)
    assert (donnees / "therese.db").exists()
    assert (donnees / "outputs" / "devis.pdf").exists()
    assert not (donnees / "projects" / "raccourci").exists()


def test_liens_physiques_etrangers_aux_publications_ne_sont_pas_restaures(tmp_path):
    from app.routers.data import _safe_extractall

    donnees = tmp_path / "donnees"
    (donnees / "backups").mkdir(parents=True)
    source = f"invoices/.therese-publication-{'a' * 64}-{'b' * 32}.pdf"
    archive = tmp_path / "liens.tar.gz"
    with tarfile.open(archive, "w:gz") as tar:
        for nom in (source, source + ".therese.json", "invoices/autre.pdf"):
            info = tarfile.TarInfo(nom)
            info.size = 3
            tar.addfile(info, io.BytesIO(b"pdf"))
        for nom, cible in (
            ("invoices/sous-dossier/FACT.pdf", source),
            ("outputs/FACT.pdf", source),
            ("invoices/FACT-autre.pdf", "invoices/autre.pdf"),
            ("invoices/FACT-exterieur.pdf", "../backups/protege"),
        ):
            info = tarfile.TarInfo(nom)
            info.type = tarfile.LNKTYPE
            info.linkname = cible
            tar.addfile(info)
    with tarfile.open(archive, "r:gz") as tar:
        _safe_extractall(tar, donnees)
    assert (donnees / source).read_bytes() == b"pdf"
    assert not (donnees / "invoices/sous-dossier/FACT.pdf").exists()
    assert not (donnees / "outputs/FACT.pdf").exists()
    assert not (donnees / "invoices/FACT-autre.pdf").exists()
    assert not (donnees / "invoices/FACT-exterieur.pdf").exists()
    assert list((donnees / "backups").iterdir()) == []


def test_restauration_apres_nettoyage_interrompu_du_compagnon_provisoire(tmp_path):
    from app.routers.data import _safe_extractall

    source = tmp_path / "source" / "invoices"
    source.mkdir(parents=True)
    provisoire = source / f".therese-publication-{'a' * 64}-{'b' * 32}.pdf"
    provisoire.write_bytes(b"pdf publie")
    publie = source / "FACT.pdf"
    os.link(provisoire, publie)
    (source / "FACT.pdf.therese.json").write_bytes(b"compagnon final")
    archive = tmp_path / "nettoyage-interrompu.tar.gz"
    with tarfile.open(archive, "w:gz") as tar:
        tar.add(source, arcname="invoices")
    destination = tmp_path / "restauree"
    destination.mkdir()
    with tarfile.open(archive, "r:gz") as tar:
        assert tar.getmember("invoices/FACT.pdf").islnk()
        _safe_extractall(tar, destination)

    fichier = destination / "invoices" / "FACT.pdf"
    assert fichier.exists(), "Le PDF publié a disparu pendant le nettoyage interrompu"
    assert fichier.read_bytes() == b"pdf publie"
    assert os.path.samefile(fichier, destination / "invoices" / provisoire.name)
    assert (destination / "invoices" / "FACT.pdf.therese.json").read_bytes() == b"compagnon final"


def test_restauration_reprend_si_pdf_et_compagnon_final_sont_deux_liens(tmp_path):
    from types import SimpleNamespace

    from app.routers import invoices
    from app.routers.data import _safe_extractall

    source = tmp_path / "source" / "invoices"
    source.mkdir(parents=True)
    piece = SimpleNamespace(id="piece-test")
    publie = source / "FACT.pdf"
    provisoire = source / f"{invoices._prefixe_publication_pdf(piece, publie)}{'a' * 32}.pdf"
    provisoire.write_bytes(b"pdf publie")
    invoices._preuve_pdf(provisoire).write_bytes(b"preuve provisoire")
    os.link(provisoire, publie)
    os.link(invoices._preuve_pdf(provisoire), invoices._preuve_pdf(publie))
    archive = tmp_path / "publication-double.tar.gz"
    with tarfile.open(archive, "w:gz") as tar:
        tar.add(source, arcname="invoices")
    destination = tmp_path / "restauree"
    destination.mkdir()
    with tarfile.open(archive, "r:gz") as tar:
        assert tar.getmember("invoices/FACT.pdf").islnk()
        assert tar.getmember("invoices/FACT.pdf.therese.json").islnk()
        _safe_extractall(tar, destination)

    fichier = destination / "invoices" / "FACT.pdf"

    def verifier(candidat):
        assert candidat.read_bytes() == b"pdf publie"
        assert invoices._preuve_pdf(candidat).read_bytes() == b"preuve provisoire"

    invoices._reprendre_preuve_pdf(fichier, piece, verifier)
    assert invoices._preuve_pdf(fichier).read_bytes() == b"preuve provisoire"
    assert not (destination / "invoices" / provisoire.name).exists()


@pytest.mark.parametrize("incident", ["sans_compagnon", "source_dupliquee"])
def test_lien_de_publication_sans_source_claire_est_ignore(tmp_path, incident):
    from app.routers.data import _safe_extractall

    donnees = tmp_path / "donnees"
    donnees.mkdir()
    source = f"invoices/.therese-publication-{'a' * 64}-{'b' * 32}.pdf"
    archive = tmp_path / "publication.tar.gz"
    with tarfile.open(archive, "w:gz") as tar:
        noms = [source]
        if incident == "source_dupliquee":
            noms.extend((source, source + ".therese.json"))
        for nom in noms:
            info = tarfile.TarInfo(nom)
            info.size = 3
            tar.addfile(info, io.BytesIO(b"pdf"))
        info = tarfile.TarInfo("invoices/FACT.pdf")
        info.type = tarfile.LNKTYPE
        info.linkname = source
        tar.addfile(info)
    with tarfile.open(archive, "r:gz") as tar:
        _safe_extractall(tar, donnees)
    assert not (donnees / "invoices/FACT.pdf").exists()


def test_une_entree_hors_de_la_sauvegarde_est_refusee(tmp_path):
    donnees = _extraire(tmp_path, [("backups/pre_restore_x.tar.gz", None)])
    assert list((donnees / "backups").iterdir()) == []


def test_une_sauvegarde_ordinaire_s_extrait(tmp_path):
    from app.routers.data import _safe_extractall

    donnees = tmp_path / "donnees"
    donnees.mkdir()
    with _archive(tmp_path, [("therese.db", None), ("outputs/devis.pdf", None), ("THERESE.md", None)]) as tar:
        _safe_extractall(tar, donnees)
    assert (donnees / "outputs" / "devis.pdf").read_bytes() == b"piege"


def test_une_sauvegarde_creee_par_therese_passe_la_liste_blanche(tmp_path):
    """Sentinelle : un nom ajouté à la sauvegarde sans l'ajouter à la liste
    blanche rendrait toutes les nouvelles sauvegardes irrestaurables."""
    from app.routers.data import NOMS_D_ARCHIVE, _create_archive, _safe_extractall

    archive = tmp_path / "sauvegarde.tar.gz"
    _create_archive(archive)
    with tarfile.open(archive, "r:gz") as tar:
        premiers = {m.name.split("/")[0] for m in tar.getmembers()}
        assert premiers <= NOMS_D_ARCHIVE, premiers - NOMS_D_ARCHIVE
        destination = tmp_path / "restauree"
        destination.mkdir()
        _safe_extractall(tar, destination)
    assert premiers
    assert {chemin.name for chemin in destination.iterdir()} == premiers
