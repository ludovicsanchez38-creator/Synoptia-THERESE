"""Validation d'un fuseau IANA à la frontière HTTP (B-553, B-555, 05/09/2026).

`ZoneInfo` transforme la clé en chemin de fichier : une chaîne trop longue
fait lever une OSError du système (« File name too long »), une chaîne vide ou
traversante un ValueError CPython avec son texte anglais et le nom TZPATH.
Les deux échappaient au seul `ZoneInfoNotFoundError` que les schémas
rattrapaient : l'une finissait en 500, l'autre affichait le message brut.
"""

from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

LONGUEUR_MAX = 64
MESSAGE = "Fuseau horaire IANA invalide"


def verifier_fuseau(nom: str) -> None:
    """Lève ValueError(MESSAGE) pour toute clé inutilisable, avant tout accès disque."""
    if not nom or len(nom) > LONGUEUR_MAX or nom.startswith(("/", ".")) or ".." in nom:
        raise ValueError(MESSAGE)
    try:
        ZoneInfo(nom)
    except (ZoneInfoNotFoundError, ValueError, OSError) as exc:
        raise ValueError(MESSAGE) from exc
