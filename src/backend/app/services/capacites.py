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


_MANIFESTE_VIDE: dict[str, Any] = {
    "schema": 0, "capacites": [], "points_entree": [], "identifiants_reserves": [],
}


def _structure_valide(manifeste: dict[str, Any]) -> bool:
    """Le contrat minimal que les consommateurs supposent.

    Revue 0.44 : « schema: 1 » est un numéro, pas une validation. Un JSON légal
    mais structurellement faux traversait le chargement puis levait un KeyError
    chez le premier consommateur — le fail-open annoncé ne couvrait que la
    syntaxe. On vérifie ici ce que le code lit réellement, et on impose au
    passage les restrictions qui rendent la canonicalisation inter-langages
    sûre : clés ASCII, nombres entiers (1.0 devient « 1.0 » en Python et « 1 »
    en JavaScript — deux empreintes pour un même fichier).
    """
    if not isinstance(manifeste.get("capacites"), list):
        return False
    if not isinstance(manifeste.get("points_entree"), list):
        return False
    for capacite in manifeste["capacites"]:
        if not isinstance(capacite, dict) or "id" not in capacite:
            return False
        if not isinstance(capacite.get("entrees", []), list):
            return False
    for point in manifeste["points_entree"]:
        if not isinstance(point, dict):
            return False
        binding = point.get("binding")
        if not isinstance(binding, dict) or "registre" not in binding:
            return False
        if binding["registre"] in ("action", "raccourci") and "actionId" not in binding:
            return False

    def _sur(valeur: Any) -> bool:
        if isinstance(valeur, dict):
            return all(
                isinstance(cle, str) and cle.isascii() and _sur(v)
                for cle, v in valeur.items()
            )
        if isinstance(valeur, list):
            return all(_sur(v) for v in valeur)
        # Entiers seulement : 1.0 devient « 1.0 » en Python et « 1 » en
        # JavaScript — deux empreintes pour un même fichier.
        return not isinstance(valeur, float)

    return _sur(manifeste)


@lru_cache(maxsize=1)
def charger_manifeste() -> dict[str, Any]:
    """Charge le manifeste, une seule fois.

    Un manifeste illisible OU structurellement invalide ne doit pas empêcher
    l'application de démarrer : le chat, l'agenda et les emails n'en dépendent
    pas. On journalise et on rend un manifeste vide, ce qui dégrade l'aide sans
    casser le produit.
    """
    try:
        with CHEMIN_MANIFESTE.open(encoding="utf-8") as fichier:
            manifeste = json.load(fichier)
    except (OSError, json.JSONDecodeError):
        logger.error(
            "Manifeste de capacités illisible (%s) : l'aide sera incomplète",
            CHEMIN_MANIFESTE, exc_info=True,
        )
        return dict(_MANIFESTE_VIDE)
    if not isinstance(manifeste, dict) or not _structure_valide(manifeste):
        logger.error(
            "Manifeste de capacités invalide (%s) : structure non conforme, "
            "l'aide sera incomplète", CHEMIN_MANIFESTE,
        )
        return dict(_MANIFESTE_VIDE)
    return manifeste


def empreinte_manifeste() -> str:
    """Empreinte du fichier canonique, pour détecter une divergence de génération.

    Le manifeste vit en deux exemplaires : bundle frontend et binaire sidecar.
    Rien ne garantit qu'un frontend et un sidecar packagés à des moments
    différents portent la même version. Le frontend compare cette empreinte à
    la sienne au démarrage : deux générations différentes doivent le dire, pas
    diverger en silence.

    Sur le JSON CANONIQUE (clés triées, sans espaces) du contenu SERVI — celui
    du cache, pas une relecture du fichier. La revue a reproduit la
    dissociation : cache rempli d'un contenu, empreinte calculée sur un autre.
    Une empreinte qui ne décrit pas ce que les consommateurs lisent ne détecte
    rien. Sentinelle « absent » si le manifeste n'a pas pu être chargé.
    """
    import hashlib

    manifeste = charger_manifeste()
    if manifeste.get("schema", 0) == 0 and not manifeste.get("capacites"):
        return "absent"
    canonique = json.dumps(
        manifeste, sort_keys=True, ensure_ascii=False, separators=(",", ":")
    )
    return hashlib.sha256(canonique.encode("utf-8")).hexdigest()


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
