"""B-1497 : restaurer une archive écrivait hors des entrées attendues.

`tar.extractall(dest, filter="data")` n'écarte que ce qui sort du dossier
de destination. Dans le dossier des données, il laissait passer un membre
`outputs/../x` et un lien interne `outputs/t -> ../backups` suivi de
`outputs/t/x` : une archive piégée ou abîmée pouvait écraser les autres
sauvegardes, dont l'archive de sécurité qui sert au retour arrière.
"""

import io
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
