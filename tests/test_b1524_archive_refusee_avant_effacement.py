"""B-1524 : une archive aux entrées inattendues était refusée après
l'effacement des dossiers.

La liste blanche de B-1497 est vérifiée à l'extraction, qui suit
l'effacement de qdrant, images, outputs et des éléments couverts : une
archive refusée détruisait d'abord, puis remettait l'état d'avant par un
retour arrière (avec ses propres risques). Elle est désormais examinée
avant toute destruction.
"""

import io
import os
import tarfile
from pathlib import Path

import pytest


@pytest.mark.asyncio
async def test_une_archive_refusee_ne_touche_a_rien(client):
    from app.config import settings
    from app.routers import data

    temoin = Path(str(settings.data_dir)) / "outputs" / "temoin-b1524.txt"
    temoin.parent.mkdir(parents=True, exist_ok=True)
    temoin.write_text("devis Roux", encoding="utf-8")
    inode_avant = os.stat(temoin).st_ino

    with tarfile.open(data._backups_dir() / "backup_b1524.tar.gz", "w:gz") as tar:
        for nom in ("therese.db", "backups/piege.tar.gz"):
            contenu = b"x"
            info = tarfile.TarInfo(nom)
            info.size = len(contenu)
            tar.addfile(info, io.BytesIO(contenu))

    reponse = await client.post("/api/data/restore/backup_b1524?confirm=true", json={})
    assert reponse.status_code == 400, reponse.text
    assert temoin.read_text(encoding="utf-8") == "devis Roux"
    assert os.stat(temoin).st_ino == inode_avant, "le dossier a été effacé puis remis"
