"""B-1507 : un arrêt brutal pendant une restauration laissait l'archive
déchiffrée en clair, clé de chiffrement comprise.

La restauration déchiffre la sauvegarde dans `backups/.<nom>.restore.tar.gz`
et l'efface en fin de route (B-1269 couvre l'annulation). Un arrêt brutal
(coupure, application tuée) la laissait sur le disque. Le démarrage efface
désormais ce seul motif : la sauvegarde chiffrée d'origine reste en place,
et aucune autre archive en clair n'est touchée (une ancienne sauvegarde ou
l'état d'avant une restauration peuvent en être l'unique copie).
"""

from pathlib import Path


def test_le_demarrage_efface_les_dechiffrements_interrompus_et_rien_d_autre(tmp_path: Path):
    from app.routers.data import effacer_les_dechiffrements_interrompus

    (tmp_path / ".backup_20260926.restore.tar.gz").write_bytes(b"clair")
    gardes = [
        "backup_20260926.tar.gz.enc", "backup_20260926.json",
        "ancienne_en_clair.tar.gz", "ancienne_en_clair.json",
        "pre_restore_20260926_101010_000000.tar.gz",
    ]
    for nom in gardes:
        (tmp_path / nom).write_bytes(b"x")

    assert effacer_les_dechiffrements_interrompus(tmp_path) == 1
    assert sorted(p.name for p in tmp_path.iterdir()) == sorted(gardes)

