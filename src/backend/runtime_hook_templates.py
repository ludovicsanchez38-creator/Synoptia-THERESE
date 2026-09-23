"""Runtime hook PyInstaller - BUG-035 / BUG-052 : chemins templates python-docx / python-pptx.

PyInstaller compile les modules Python dans l'archive PYZ, donc les répertoires
docx/parts/ et pptx/oxml/ n'existent pas physiquement dans _MEIPASS.
Or python-docx et python-pptx résolvent les templates via __file__ + '..' :
  docx/parts/../templates/default-footer.xml
  pptx/oxml/../templates/notes.xml
L'OS ne peut pas résoudre '..' si le répertoire intermédiaire n'existe pas.

Ce hook crée les répertoires vides nécessaires avant tout import.
BUG-052 : sur Linux .deb, _MEIPASS pointe vers /usr/lib/ (lecture seule).
On catch PermissionError et on ignore : depuis B-948, backend.spec embarque un
témoin dans chacun de ces dossiers (repertoires_bundle.py), qui existent donc
déjà dans le bundle. Garder cette liste identique à REPERTOIRES_REQUIS.
"""

import os
import sys

if hasattr(sys, "_MEIPASS"):
    for subdir in ("docx/parts", "pptx/oxml", "pptx/shapes"):
        try:
            os.makedirs(os.path.join(sys._MEIPASS, subdir), exist_ok=True)
        except OSError:
            pass  # BUG-052 : _MEIPASS en lecture seule sur Linux .deb
