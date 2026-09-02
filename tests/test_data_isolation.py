"""Garde-fou : la suite de tests ne doit JAMAIS s'exécuter contre la base
réelle de l'utilisateur (~/.therese). Les fixtures `client`/`db_session` font
un drop_all/create_all : sans data dir isolé, lancer les tests détruit les
données locales. Le conftest doit forcer THERESE_DATA_DIR.

B-047 : le garde ne comparait que l'ÉGALITÉ des deux chemins. Un
`THERESE_DATA_DIR` posé sur un SOUS-dossier de l'installation réelle
(`~/.therese/tests`) le laissait vert, alors que les fixtures détruiraient
bien des données situées dans `~/.therese`. La règle correcte existait déjà
dans le dépôt, appliquée aux journaux, à THERESE.md et aux PDF de facture
(`tests/test_isolation_du_dossier_de_donnees.py`) : c'est une appartenance
d'arborescence, pas une inégalité. Septième jumeau non balayé.

Ce test n'utilise volontairement aucune fixture DB (pas de drop_all)."""
from pathlib import Path

from app.config import settings


def est_hors_de_l_installation_reelle(dossier: Path, reel: Path) -> bool:
    """Le dossier de données est-il VRAIMENT hors de l'installation réelle ?

    Même forme que les trois gardes de
    `tests/test_isolation_du_dossier_de_donnees.py` : `reel not in
    chemin.parents and chemin != reel`.
    """
    dossier = dossier.resolve()
    reel = reel.resolve()
    return reel not in dossier.parents and dossier != reel


def test_les_tests_n_utilisent_pas_la_base_reelle():
    real = Path.home() / ".therese"
    assert settings.data_dir is not None
    assert est_hors_de_l_installation_reelle(Path(settings.data_dir), real), (
        "Les tests pointent sur la base réelle ~/.therese (ou dans son "
        "arborescence) ; le conftest doit définir THERESE_DATA_DIR vers un "
        "dossier temporaire."
    )


def test_un_sous_dossier_de_l_installation_reelle_est_refuse(tmp_path):
    """B-047 : `~/.therese/tests` n'est PAS un dossier isolé.

    Le drop_all/create_all des fixtures y détruirait des données réelles.
    Éprouvé sur une installation factice, jamais sur le vrai `~/.therese`.
    """
    reel = tmp_path / ".therese"
    (reel / "tests").mkdir(parents=True)

    assert not est_hors_de_l_installation_reelle(reel / "tests", reel), (
        "un sous-dossier de l'installation réelle est accepté comme isolé"
    )
    assert not est_hors_de_l_installation_reelle(reel / "sauvegardes" / "x", reel), (
        "un sous-dossier profond de l'installation réelle est accepté comme isolé"
    )
    assert not est_hors_de_l_installation_reelle(reel, reel), (
        "l'installation réelle elle-même est acceptée comme isolée"
    )
    assert est_hors_de_l_installation_reelle(tmp_path / "jetable", reel), (
        "un vrai dossier jetable est refusé à tort"
    )
