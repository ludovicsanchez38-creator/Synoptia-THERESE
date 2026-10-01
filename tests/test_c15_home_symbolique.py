"""Le dossier personnel reste protégé quand son chemin est un lien symbolique."""

from pathlib import Path

import pytest
from app.services.path_security import validate_file_path


@pytest.fixture
def home_symbolique(tmp_path, monkeypatch):
    domicile = tmp_path / "domicile"
    domicile.mkdir()
    alias = tmp_path / "alias"
    try:
        alias.symlink_to(domicile, target_is_directory=True)
    except OSError:
        pytest.skip("Les liens symboliques de dossier sont indisponibles")
    monkeypatch.setenv("HOME", str(alias))
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: alias))
    return domicile, alias


@pytest.mark.parametrize("dossier", [".ssh", ".aws", ".gnupg"])
@pytest.mark.parametrize("present", [False, True])
def test_un_home_symbolique_ne_rouvre_pas_les_secrets(home_symbolique, dossier, present):
    domicile, alias = home_symbolique
    cible = domicile / dossier / "donnee-synthetique"
    if present:
        cible.parent.mkdir()
        cible.write_text("jetable", encoding="utf-8")
    with pytest.raises(PermissionError) as capture:
        validate_file_path(alias / dossier / cible.name)
    assert str(domicile) not in str(capture.value)
    assert cible.name not in str(capture.value)


def test_un_fichier_ordinaire_du_home_symbolique_reste_lisible(home_symbolique):
    domicile, alias = home_symbolique
    cible = domicile / "note.md"
    cible.write_text("Donnée synthétique", encoding="utf-8")
    assert validate_file_path(alias / cible.name) == cible
