"""Identité durable du dossier, indépendante de ses graphies et liens."""
import os
from pathlib import Path
from stat import S_ISDIR
from uuid import UUID, uuid4


def identite_profil(dossier: Path) -> str:
    dossier = dossier.resolve(strict=True)
    info = dossier.stat()
    if not S_ISDIR(info.st_mode):
        raise NotADirectoryError(str(dossier))
    # Linux ne fournit pas toujours la naissance et peut réutiliser un inode.
    # Le nonce appartient au dossier créé ; une copie vers un autre inode
    # garde une identité distincte. L'ouverture exclusive ne remplace jamais
    # un identifiant existant, même illisible ou partiellement écrit.
    marqueur = dossier / ".therese-profile-id"
    try:
        with marqueur.open("x", encoding="ascii") as fichier:
            fichier.write(uuid4().hex)
            fichier.flush()
            os.fsync(fichier.fileno())
    except FileExistsError:
        pass
    identifiant = UUID(marqueur.read_text(encoding="ascii")).hex
    return f"directory:{info.st_dev}:{info.st_ino}:{identifiant}"
