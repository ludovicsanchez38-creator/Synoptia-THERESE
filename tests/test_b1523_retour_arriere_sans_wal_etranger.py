"""B-1523 : le retour arrière d'une restauration rejouait le WAL de
l'archive fautive sur la base remise.

Une sauvegarde faite pendant un point de contrôle incomplet range
therese.db-wal et therese.db-shm à part. Si sa restauration échoue après
l'extraction, le retour arrière remet la base d'avant mais laisse ces deux
fichiers à côté d'elle : SQLite les rejoue à l'ouverture (sonde de la revue :
la base remise se lit avec la ligne étrangère, integrity_check « ok »).
"""

import io
import tarfile
from pathlib import Path

import pytest


def _archive_fautive(chemin: Path, base: Path, dossier_de_travail: Path, contact_id: str) -> None:
    """Une vraie archive fautive : la base d'avant, plus un WAL valide (même
    clé) qui porte un contact étranger jamais consolidé."""
    import shutil

    from app.models.database import db_connect

    with db_connect(base) as connexion:
        connexion.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    copie = dossier_de_travail / "therese.db"
    shutil.copyfile(base, copie)
    octets_de_base = copie.read_bytes()
    connexion = db_connect(copie)
    connexion.execute("PRAGMA journal_mode=WAL")
    connexion.execute("PRAGMA wal_autocheckpoint=0")
    connexion.execute("CREATE TEMP TABLE modele AS SELECT * FROM contacts WHERE id = ?", (contact_id,))
    connexion.execute("UPDATE modele SET id = 'contact-etranger', first_name = 'Étranger'")
    connexion.execute("INSERT INTO contacts SELECT * FROM modele")
    connexion.commit()
    wal = Path(f"{copie}-wal").read_bytes()
    connexion.close()
    assert wal, "le WAL témoin est vide : la sonde ne prouverait rien"
    with tarfile.open(chemin, "w:gz") as tar:
        for nom, contenu in (("therese.db", octets_de_base), ("therese.db-wal", wal)):
            info = tarfile.TarInfo(nom)
            info.size = len(contenu)
            tar.addfile(info, io.BytesIO(contenu))


@pytest.mark.asyncio
async def test_le_retour_arriere_ne_rejoue_pas_le_wal_de_l_archive_fautive(client, monkeypatch, tmp_path):
    from app.config import settings
    from app.routers import data

    base = Path(str(settings.db_path))
    contact = await client.post("/api/memory/contacts", json={"first_name": "Avant", "last_name": "Restauration"})
    assert contact.status_code == 200, contact.text

    _archive_fautive(data._backups_dir() / "backup_b1523.tar.gz", base, tmp_path, contact.json()["id"])

    def verification_en_echec() -> None:
        raise RuntimeError("base restaurée illisible")

    monkeypatch.setattr(data, "_verify_restored_db", verification_en_echec)
    reponse = await client.post("/api/data/restore/backup_b1523?confirm=true", json={})
    assert reponse.status_code == 500 and "état précédent" in reponse.text, reponse.text

    assert (await client.get(f"/api/memory/contacts/{contact.json()['id']}")).status_code == 200
    etranger = await client.get("/api/memory/contacts/contact-etranger")
    assert etranger.status_code == 404, "le WAL de l'archive fautive a été rejoué sur la base remise"
