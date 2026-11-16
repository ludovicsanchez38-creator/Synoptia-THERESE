"""Identité du dossier, indépendante de ses graphies et liens symboliques."""
from pathlib import Path
from stat import S_ISDIR


def identite_profil(dossier: Path) -> str:
    info = dossier.stat()
    if not S_ISDIR(info.st_mode):
        raise NotADirectoryError(str(dossier))
    # La naissance distingue aussi une réutilisation d'inode sur macOS.
    naissance = getattr(info, "st_birthtime_ns", None)
    if naissance is None:
        naissance = int(getattr(info, "st_birthtime", 0) * 1_000_000_000)
    return f"directory:{info.st_dev}:{info.st_ino}:{naissance}"
