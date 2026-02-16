"""Runtime hook PyInstaller - BUG-035 : chemins templates python-docx / python-pptx.

PyInstaller compile les modules Python dans l'archive PYZ, donc les répertoires
docx/parts/ et pptx/oxml/ n'existent pas physiquement dans _MEIPASS.
Or python-docx et python-pptx résolvent les templates via __file__ + '..' :
  docx/parts/../templates/default-footer.xml
  pptx/oxml/../templates/notes.xml
L'OS ne peut pas résoudre '..' si le répertoire intermédiaire n'existe pas.

Ce hook crée les répertoires vides nécessaires avant tout import.
"""

import os
import sys

if hasattr(sys, "_MEIPASS"):
    for subdir in ("docx/parts", "pptx/oxml", "pptx/shapes"):
        os.makedirs(os.path.join(sys._MEIPASS, subdir), exist_ok=True)
