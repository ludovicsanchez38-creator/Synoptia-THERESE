"""P-102 : sous Linux, une commande supprimée va dans la corbeille du bureau.

Avant, `delete_command` ne connaissait que `~/.Trash` (macOS) ; sous Linux,
absent, la commande tombait dans le repli caché `commands/user/.trash`, que
l'utilisatrice ne retrouve pas depuis son gestionnaire de fichiers. La
corbeille du bureau suit la spécification freedesktop.org : un dossier
`files/` pour le contenu et un fichier `info/<nom>.trashinfo` qui garde le
chemin d'origine et la date, pour que « Restaurer » fonctionne.
Accepté par délégation de Ludo le 24/09 (docs/plans/2026-09-24-arbitrages-par-delegation.md).
"""

from __future__ import annotations

import sys
from urllib.parse import unquote

import pytest


@pytest.fixture
def service_linux(tmp_path, monkeypatch):
    from app.config import settings
    from app.services.user_commands import UserCommandsService

    monkeypatch.setattr(settings, "data_dir", str(tmp_path / "donnees"))
    monkeypatch.setattr(sys, "platform", "linux")
    monkeypatch.setenv("HOME", str(tmp_path / "maison"))
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "maison" / ".local" / "share"))
    return UserCommandsService()


def _corbeille(tmp_path):
    return tmp_path / "maison" / ".local" / "share" / "Trash"


def test_la_commande_supprimee_va_dans_la_corbeille_du_bureau(service_linux, tmp_path):
    service_linux.create_command(name="resume", description="d", content="Corps")
    origine = tmp_path / "donnees" / "commands" / "user" / "resume.md"

    assert service_linux.delete_command("resume") is True

    assert not origine.exists()
    assert (_corbeille(tmp_path) / "files" / "resume.md").read_text(encoding="utf-8").strip().endswith("Corps")
    assert not (tmp_path / "donnees" / "commands" / "user" / ".trash").exists(), "repli caché utilisé"
    info = (_corbeille(tmp_path) / "info" / "resume.md.trashinfo").read_text(encoding="utf-8")
    lignes = info.splitlines()
    assert lignes[0] == "[Trash Info]"
    chemin = next(ligne for ligne in lignes if ligne.startswith("Path="))[len("Path="):]
    assert unquote(chemin) == str(origine)
    assert any(ligne.startswith("DeletionDate=") and len(ligne) == len("DeletionDate=2026-09-24T21:30:00") for ligne in lignes)


def test_deux_commandes_du_meme_nom_ne_s_ecrasent_pas(service_linux, tmp_path):
    for _ in range(2):
        service_linux.create_command(name="resume", description="d", content="Corps")
        assert service_linux.delete_command("resume") is True

    fichiers = sorted(p.name for p in (_corbeille(tmp_path) / "files").iterdir())
    infos = sorted(p.name for p in (_corbeille(tmp_path) / "info").iterdir())
    assert len(fichiers) == 2, fichiers
    assert infos == sorted(f"{nom}.trashinfo" for nom in fichiers)


def test_la_purge_rgpd_efface_aussi_le_depot_et_sa_fiche(service_linux, tmp_path):
    service_linux.create_command(name="resume", description="d", content="Corps")
    service_linux.delete_command("resume")

    service_linux.purger_tout()

    assert list((_corbeille(tmp_path) / "files").iterdir()) == []
    assert list((_corbeille(tmp_path) / "info").iterdir()) == []
