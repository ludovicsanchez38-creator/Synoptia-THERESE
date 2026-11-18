"""Le faux curl doit fonctionner même si Python se trouve dans un chemin à espaces."""

import os
import sys

import pytest

from tests.test_securite_f2_recette_deb import _jouer_amorcage

pytestmark = pytest.mark.skipif(os.name != "posix", reason="La recette .deb utilise un shell POSIX.")


def test_amorcage_avec_interpreteur_dans_un_chemin_a_espaces(tmp_path, monkeypatch):
    interpreteur = tmp_path / "python avec espace"
    interpreteur.symlink_to(sys.executable)
    monkeypatch.setattr(sys, "executable", str(interpreteur))
    resultat, requetes = _jouer_amorcage(tmp_path, "jeton-prive-factice")
    assert resultat.stdout == "document-factice"
    assert len(requetes) == 1
