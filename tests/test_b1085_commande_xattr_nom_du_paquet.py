"""B-1085 (lecteur H1, dernière passe de la carte c12) : la note de release
conseillait « xattr -cr /Applications/THÉRÈSE.app », alors que le paquet
s'installe sous le nom de productName (THERESE.app). La commande visait un
chemin qui n'existe pas."""

from __future__ import annotations

import json
import re
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent


def test_la_note_de_release_vise_le_nom_du_paquet():
    nom = json.loads((RACINE / "src/frontend/src-tauri/tauri.conf.json").read_text(encoding="utf-8"))["productName"]
    note = (RACINE / ".github/workflows/release.yml").read_text(encoding="utf-8")
    chemins = set(re.findall(r"/Applications/([^\s`'\"]+)\.app", note))
    assert chemins == {nom}, chemins
