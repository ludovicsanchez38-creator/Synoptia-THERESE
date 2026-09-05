"""B-576 (05/09/2026) : les actions parlaient sans accents.

Les libellés, descriptions et consignes de `action_agents.json` s'affichent à
l'écran (panneau Actions) et alimentent le modèle ; l'en-tête du rapport
généré disait « Execute le … a … ». Le reste de l'interface porte ses
accents : ces textes aussi.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1] / "src" / "backend" / "app"
JSON_ACTIONS = RACINE / "agents" / "action_agents.json"
SERVICE = RACINE / "services" / "action_agents.py"

MOTS_SANS_ACCENT = (
    "tresorerie", "echanges", "activite", "reunions", "reunion", "taches",
    "payes", "payees", "previsions", "previsionnel", "resume", "redige",
    "synthese", "synthetise", "genere", "precedentes", "completees", "recus",
    "envoyes", "demandees", "reponses", "donnees", "abordes", "prevues",
    "opportunites", "effectuees", "derniere", "personnalise", "recommande",
    "telephone", "adapte", "cle", "cles", "recentes", "actualites", "actualite",
    "reseaux", "preparation", "pieges", "eviter", "encaisse", "delai", "deja",
    "emises", "acceptes", "periodes", "proposees", "visees", "elements",
    "differenciants", "differenciation", "structuree", "acces", "creer",
    "etapes", "etape", "depenses", "presente", "presence", "frequence",
    "communaute", "levees", "tiede", "decisions", "envoyees",
)
MOTIF = re.compile(r"(?<![\w'])(" + "|".join(MOTS_SANS_ACCENT) + r")(?![\w'])", re.IGNORECASE)
MOTIF_A = re.compile(r"\b[aA] (partir|envoyer|creer|créer|planifier|configurer|relancer|aborder|poser|reporter|eviter|éviter)\b")


def _textes_affiches() -> list[tuple[str, str]]:
    textes: list[tuple[str, str]] = []

    def marche(objet, chemin=""):
        if isinstance(objet, dict):
            for cle, valeur in objet.items():
                marche(valeur, f"{chemin}/{cle}")
        elif isinstance(objet, list):
            for i, valeur in enumerate(objet):
                marche(valeur, f"{chemin}[{i}]")
        elif isinstance(objet, str) and chemin.rsplit("/", 1)[-1] in (
            "name", "label", "description", "prompt", "placeholder",
        ):
            textes.append((chemin, objet))

    marche(json.loads(JSON_ACTIONS.read_text(encoding="utf-8")))
    return textes


def test_les_textes_des_actions_portent_leurs_accents():
    fautes = [
        (chemin, mot.group(0))
        for chemin, texte in _textes_affiches()
        for mot in MOTIF.finditer(texte)
    ]
    fautes += [
        (chemin, mot.group(0))
        for chemin, texte in _textes_affiches()
        for mot in MOTIF_A.finditer(texte)
    ]
    assert fautes == [], fautes


def test_l_en_tete_du_rapport_est_accentue():
    source = SERVICE.read_text(encoding="utf-8")
    assert "Exécuté le {" in source
    assert "*Execute le {" not in source
