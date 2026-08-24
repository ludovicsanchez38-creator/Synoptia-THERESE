"""Lecture du manifeste de capacités côté sidecar (0.44).

Le manifeste est la source du vocabulaire produit : ce que THÉRÈSE sait faire,
sous quel nom, par quels chemins, avec quelles limites. Le backend en a besoin
pour deux choses — la réponse de `/aide` et la table des destinations du chat —
et il doit le lire sans dépendre du frontend.

D'où le choix d'un fichier JSON canonique sous `app/data/`, embarqué par
`backend.spec`. Le chemin est résolu **relativement à ce module**, jamais depuis
le répertoire courant : le sidecar est lancé par Tauri, dont le répertoire
courant n'a rien à voir, et sous PyInstaller l'arborescence bascule sous
`_MEIPASS`. Un chemin relatif au CWD marcherait en développement et échouerait
dans l'application livrée.
"""
import json
import logging
from functools import lru_cache
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

CHEMIN_MANIFESTE = Path(__file__).resolve().parent.parent / "data" / "capacites.json"


@lru_cache(maxsize=1)
def charger_manifeste() -> dict[str, Any]:
    """Charge le manifeste, une seule fois.

    Un manifeste illisible ne doit pas empêcher l'application de démarrer : le
    chat, l'agenda et les emails n'en dépendent pas. On journalise et on rend un
    manifeste vide, ce qui dégrade l'aide sans casser le produit.
    """
    try:
        with CHEMIN_MANIFESTE.open(encoding="utf-8") as fichier:
            return json.load(fichier)
    except (OSError, json.JSONDecodeError):
        logger.error(
            "Manifeste de capacités illisible (%s) : l'aide sera incomplète",
            CHEMIN_MANIFESTE, exc_info=True,
        )
        return {"schema": 0, "capacites": [], "points_entree": [], "identifiants_reserves": []}


def capacites() -> list[dict[str, Any]]:
    return charger_manifeste().get("capacites", [])


def capacite(identifiant: str) -> dict[str, Any] | None:
    return next((c for c in capacites() if c["id"] == identifiant), None)


def points_entree() -> list[dict[str, Any]]:
    return charger_manifeste().get("points_entree", [])


def acces_principal(identifiant: str) -> dict[str, Any] | None:
    """Le chemin à citer quand il n'en faut qu'un — déclaré, jamais déduit."""
    cible = capacite(identifiant)
    if not cible:
        return None
    return next(
        (
            p
            for p in points_entree()
            if p["id"] in cible.get("entrees", []) and p.get("principal")
        ),
        None,
    )


def texte(capacite_donnee: dict[str, Any], champ: str, langue: str = "fr-FR") -> str:
    """Lit un texte localisé, sans jamais laisser un identifiant fuiter à l'écran."""
    textes = capacite_donnee.get("textes", {})
    return textes.get(langue, {}).get(champ, "")
