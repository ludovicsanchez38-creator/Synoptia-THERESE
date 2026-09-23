"""Répertoires que tout bundle PyInstaller doit contenir (B-948, 23/09/2026).

python-docx et python-pptx ouvrent leurs gabarits par un chemin relatif à leur
module (`docx/parts/../templates/default-footer.xml`). PyInstaller range ces
modules dans l'archive PYZ : sans dossier `docx/parts/` sur disque, Linux ne
résout pas `..` et l'ouverture échoue.

`runtime_hook_templates.py` crée ces dossiers au démarrage, ce qui ne suffit
pas quand le bundle est en lecture seule (paquet .deb sous /usr/lib). Le spec
embarque donc un fichier témoin dans chacun d'eux : ils existent alors dans
tout bundle. Liste identique à celle du hook, vérifiée par
tests/test_b948_repertoires_bundle.py.
"""

from __future__ import annotations

from pathlib import Path

REPERTOIRES_REQUIS: tuple[str, ...] = ("docx/parts", "pptx/oxml", "pptx/shapes")
TEMOIN = Path(__file__).with_name("repertoire_requis.txt")


def datas_repertoires_requis() -> list[tuple[str, str]]:
    """Entrées `datas` PyInstaller : le témoin, copié dans chaque répertoire requis."""
    return [(str(TEMOIN), repertoire) for repertoire in REPERTOIRES_REQUIS]
