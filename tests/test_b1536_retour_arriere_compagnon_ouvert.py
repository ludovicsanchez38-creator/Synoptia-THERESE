"""B-1536 (régression de B-1523, vue par la CI Windows) : le retour arrière
d'une restauration supprimait le -wal et le -shm avant d'extraire l'archive de
sécurité. Sous Windows, un fichier encore ouvert ne se supprime pas
(PermissionError) : le retour arrière s'arrêtait là, la base restait dans
l'état de l'archive fautive, et 1 400 tests suivants tombaient en « file is
not a database ».

Le refus de Windows est simulé : `unlink` lève PermissionError sur les deux
compagnons de la base.
"""

from __future__ import annotations

import errno
import pathlib
from pathlib import Path

import pytest
from app.config import settings
from app.routers import data as data_router

PASSE = "Passphrase-Test-123"


@pytest.mark.asyncio
async def test_le_retour_arriere_aboutit_quand_windows_refuse_de_supprimer_le_wal(client, monkeypatch):
    data_dir = Path(settings.data_dir)
    (data_dir / "THERESE.md").write_text("Mes consignes actuelles", encoding="utf-8")
    sauvegarde = await client.post("/api/data/backup", json={"password": PASSE})
    assert sauvegarde.status_code == 200, sauvegarde.text

    vraie_extraction = data_router._safe_extractall
    appels: list[int] = []

    def echoue_une_fois(tar, dest):
        appels.append(1)
        if len(appels) == 1:
            raise OSError(errno.ENOSPC, "No space left on device")
        return vraie_extraction(tar, dest)

    _refuser_la_suppression_des_compagnons(monkeypatch)
    monkeypatch.setattr(data_router, "_safe_extractall", echoue_une_fois)

    reponse = await client.post(
        f"/api/data/restore/{sauvegarde.json()['backup_name']}?confirm=true", json={"password": PASSE},
    )

    assert reponse.status_code == 500
    assert len(appels) == 2, "le retour arrière n'a pas atteint l'extraction de l'archive de sécurité"
    assert "Données restaurées à l'état précédent" in reponse.json().get("message", "")
    assert (data_dir / "THERESE.md").read_text(encoding="utf-8") == "Mes consignes actuelles"


def _refuser_la_suppression_des_compagnons(monkeypatch) -> None:
    compagnons = {f"{settings.db_path}-wal", f"{settings.db_path}-shm"}
    vrai_unlink = pathlib.Path.unlink

    def unlink_a_la_windows(self, missing_ok=False):
        if str(self) in compagnons:
            raise PermissionError(errno.EACCES, "fichier ouvert par un autre processus", str(self))
        return vrai_unlink(self, missing_ok=missing_ok)

    monkeypatch.setattr(pathlib.Path, "unlink", unlink_a_la_windows)


@pytest.mark.asyncio
async def test_le_wal_fautif_non_supprimable_n_est_pas_rejoue(client, monkeypatch, tmp_path):
    """Le scénario de B-1523 (vrai WAL chiffré porteur d'un contact étranger)
    quand Windows refuse la suppression : le WAL est vidé, pas rejoué."""
    from tests.test_b1523_retour_arriere_sans_wal_etranger import _archive_fautive

    contact = await client.post("/api/memory/contacts", json={"first_name": "Avant", "last_name": "Restauration"})
    assert contact.status_code == 200, contact.text
    _archive_fautive(
        data_router._backups_dir() / "backup_b1536.tar.gz", Path(str(settings.db_path)), tmp_path, contact.json()["id"],
    )

    def verification_en_echec() -> None:
        raise RuntimeError("base restaurée illisible")

    monkeypatch.setattr(data_router, "_verify_restored_db", verification_en_echec)
    _refuser_la_suppression_des_compagnons(monkeypatch)
    reponse = await client.post("/api/data/restore/backup_b1536?confirm=true", json={})
    assert reponse.status_code == 500 and "état précédent" in reponse.text, reponse.text

    assert (await client.get(f"/api/memory/contacts/{contact.json()['id']}")).status_code == 200
    etranger = await client.get("/api/memory/contacts/contact-etranger")
    assert etranger.status_code == 404, "le WAL de l'archive fautive a été rejoué sur la base remise"
