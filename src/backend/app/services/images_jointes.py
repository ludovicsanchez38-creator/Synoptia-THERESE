"""Charger une image déposée dans le chat pour la MONTRER au modèle.

Incident du 31/08/2026 : glisser une capture d'écran dans THÉRÈSE répondait
« Type de fichier non autorisé pour l'indexation : '.png' [...] Ce fichier ne
sera pas utilisé pour répondre. » L'image partait dans la chaîne d'extraction
de texte, qui ne sait rien en faire, alors que le modèle sélectionné savait
lire une image.

Une image n'est pas un document à indexer. Elle ne rejoint donc jamais la
mémoire vectorielle : elle est encodée et posée sur le message du tour.
"""

import base64
import logging
from pathlib import Path

from app.services.path_security import validate_file_path
from app.services.providers.base import ImageJointe

logger = logging.getLogger(__name__)

#: Extensions reconnues et leur type média. Volontairement court : on ne
#: promet que ce que les API des fournisseurs acceptent réellement.
EXTENSIONS_IMAGE: dict[str, str] = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
    ".gif": "image/gif",
}

#: Plafond par image, avant encodage. Aligné sur le fournisseur le plus
#: strict des trois formats émis, pour qu'une image acceptée ici ne soit pas
#: refusée plus loin.
TAILLE_MAX_IMAGE = 5 * 1024 * 1024

#: Au-delà, on ne devine pas ce que l'utilisateur voulait montrer.
PLAFOND_IMAGES_PAR_TOUR = 4


def est_une_image(chemin: str | Path) -> bool:
    return Path(chemin).suffix.lower() in EXTENSIONS_IMAGE


def charger_images_jointes(
    chemins: list[str] | None,
) -> tuple[list[ImageJointe], list[str]]:
    """Rend les images chargées, et le NOM de celles qui ne l'ont pas été.

    Une image écartée en silence ferait croire au lecteur que le modèle l'a
    vue, et sa réponse « à côté » deviendrait incompréhensible. Chaque écart
    est donc nommé pour être dit à l'utilisateur.
    """
    images: list[ImageJointe] = []
    ecartees: list[str] = []
    if not chemins:
        return images, ecartees

    for brut in chemins:
        chemin = Path(brut)
        media_type = EXTENSIONS_IMAGE.get(chemin.suffix.lower())
        if media_type is None:
            # Pas une image : ce n'est pas un écart, c'est un autre chemin.
            continue

        if len(images) >= PLAFOND_IMAGES_PAR_TOUR:
            ecartees.append(
                f"{chemin.name} (plafond de {PLAFOND_IMAGES_PAR_TOUR} images "
                "par message atteint)"
            )
            continue

        try:
            # Les chemins viennent du client : on repasse par la validation
            # commune plutôt que de lire ce qu'on nous nomme.
            valide = validate_file_path(str(chemin), None)
            taille = valide.stat().st_size
            if taille > TAILLE_MAX_IMAGE:
                ecartees.append(
                    f"{chemin.name} ({taille // (1024 * 1024)} Mo, limite "
                    f"{TAILLE_MAX_IMAGE // (1024 * 1024)} Mo)"
                )
                continue
            octets = valide.read_bytes()
        except (OSError, ValueError, PermissionError) as e:
            logger.info("Image %s non lisible : %s", chemin.name, e)
            ecartees.append(f"{chemin.name} (illisible)")
            continue

        images.append(
            ImageJointe(
                media_type=media_type,
                donnees_base64=base64.b64encode(octets).decode("ascii"),
            )
        )

    return images, ecartees
