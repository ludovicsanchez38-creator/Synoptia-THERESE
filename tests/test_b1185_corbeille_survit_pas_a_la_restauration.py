"""B-1185 : l'index des dépôts en Corbeille (`commands/user/.corbeille.json`)
vit dans un dossier que la sauvegarde archive et que la restauration vide puis
réextrait (B-1157). Sauvegarder, supprimer une commande (copie en Corbeille,
index mis à jour), restaurer, puis « Effacer toutes mes données » : la purge
ne connaît plus la copie en Corbeille, qui survit.

Attendu (B-465, user_commands.py:258-261 et :357-364) : « le dépôt en
Corbeille est noté, sans quoi la purge RGPD ne pouvait pas le retrouver et le
texte de l'utilisatrice survivait à toutes mes données ».

La Corbeille est un faux `~/.Trash` (Path.home redirigé) : jamais la vraie.
"""

from __future__ import annotations

import pathlib
import sys
from pathlib import Path

import pytest
from app.config import settings

PASSE = "Passphrase-Test-123"


@pytest.fixture(params=["darwin", "linux"])
def fausse_corbeille(request, tmp_path, monkeypatch):
    # B-1233 : les deux chemins de la Corbeille, ~/.Trash (macOS) et
    # freedesktop (Linux, P-102), écrivent dans le même index ; forcer la
    # plateforme sur un seul (B-1198) retirait l'autre de la couverture.
    maison = tmp_path / "maison"
    (maison / ".Trash").mkdir(parents=True)
    monkeypatch.setattr(pathlib.Path, "home", classmethod(lambda cls: maison))
    monkeypatch.setenv("XDG_DATA_HOME", str(maison / ".local" / "share"))
    monkeypatch.setattr(sys, "platform", request.param)
    from app.services.user_commands import UserCommandsService

    monkeypatch.setattr(UserCommandsService, "_instance", None)
    if request.param == "linux":
        return maison / ".local" / "share" / "Trash" / "files"
    return maison / ".Trash"


def _poser_commande(data_dir: Path) -> Path:
    dossier = data_dir / "commands" / "user"
    dossier.mkdir(parents=True, exist_ok=True)
    chemin = dossier / "ma-commande.md"
    chemin.write_text("---\nname: ma-commande\n---\nTexte privé de Ludo", encoding="utf-8")
    return chemin


def _supprimer_commande(corbeille: Path) -> Path:
    from app.services.user_commands import UserCommandsService

    service = UserCommandsService.get_instance()
    assert service.delete_command("ma-commande") is True
    depot = corbeille / "ma-commande.md"
    assert depot.exists(), sorted(p.name for p in corbeille.iterdir())
    assert str(depot) in service._depots_en_corbeille(), service._depots_en_corbeille()
    return depot


@pytest.mark.asyncio
async def test_une_commande_en_corbeille_ne_survit_pas_a_restauration_puis_purge(
    client, fausse_corbeille
):
    data_dir = Path(settings.data_dir)
    _poser_commande(data_dir)
    resp = await client.post("/api/data/backup", json={"password": PASSE})
    assert resp.status_code == 200, resp.text
    nom = resp.json()["backup_name"]

    depot = _supprimer_commande(fausse_corbeille)

    resp = await client.post(f"/api/data/restore/{nom}?confirm=true", json={"password": PASSE})
    assert resp.status_code == 200, resp.text

    resp = await client.delete("/api/data/all?confirm=true")
    assert resp.status_code == 200, resp.text

    assert not depot.exists(), (
        f"après sauvegarde, suppression, restauration puis purge RGPD, la copie "
        f"en Corbeille survit : {depot} ({depot.read_text(encoding='utf-8')!r})"
    )


@pytest.mark.asyncio
async def test_temoin_sans_restauration_la_purge_efface_la_copie_en_corbeille(
    client, fausse_corbeille
):
    data_dir = Path(settings.data_dir)
    _poser_commande(data_dir)
    depot = _supprimer_commande(fausse_corbeille)

    resp = await client.delete("/api/data/all?confirm=true")
    assert resp.status_code == 200, resp.text

    assert not depot.exists()
