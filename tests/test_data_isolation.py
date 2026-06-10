"""Garde-fou : la suite de tests ne doit JAMAIS s'exécuter contre la base
réelle de l'utilisateur (~/.therese). Les fixtures `client`/`db_session` font
un drop_all/create_all : sans data dir isolé, lancer les tests détruit les
données locales. Le conftest doit forcer THERESE_DATA_DIR.

Ce test n'utilise volontairement aucune fixture DB (pas de drop_all)."""
from pathlib import Path

from app.config import settings


def test_les_tests_n_utilisent_pas_la_base_reelle():
    real = Path.home() / ".therese"
    assert settings.data_dir is not None
    assert Path(settings.data_dir).resolve() != real.resolve(), (
        "Les tests pointent sur la base réelle ~/.therese ; le conftest doit "
        "définir THERESE_DATA_DIR vers un dossier temporaire."
    )
