"""Environnement des outils du poste lancés par le moteur (B-949, 23/09/2026).

Sous Linux, le moteur livré est un bundle PyInstaller onedir. Son bootloader
préfixe `LD_LIBRARY_PATH` avec le dossier `_internal` du bundle et conserve
l'ancienne valeur dans `LD_LIBRARY_PATH_ORIG`. Un outil du poste (grep, git,
pytest, npm...) qui hérite tel quel de cet environnement charge la libstdc++,
l'OpenSSL ou la zlib du bundle au lieu de celles du système : versions plus
anciennes, voire refus de démarrer (« GLIBCXX_3.4.32 not found »).

La documentation de PyInstaller recommande de rendre la valeur d'origine aux
programmes externes ; c'est ce que fait ce module. Hors bundle (développement,
tests), l'environnement n'est pas modifié.
"""

from __future__ import annotations

import os
import sys


def environnement_outils_systeme(**ajouts: str) -> dict[str, str]:
    """Copie de `os.environ` à passer à un outil du poste, plus `ajouts`."""
    env = dict(os.environ)
    if getattr(sys, "frozen", False):
        origine = env.pop("LD_LIBRARY_PATH_ORIG", None)
        if origine is not None:
            env["LD_LIBRARY_PATH"] = origine
        else:
            env.pop("LD_LIBRARY_PATH", None)
    env.update(ajouts)
    return env
