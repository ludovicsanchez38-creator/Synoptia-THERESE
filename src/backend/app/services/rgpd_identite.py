"""L'identité d'une fiche au sens du RGPD : ce qu'on exporte, ce qu'on efface.

B-1438 (recette P-146, lot 2) : l'export Art. 20 d'une fiche oubliait
l'adresse, et l'anonymisation Art. 17 la laissait en clair. B-880 avait
corrigé la purge automatique seulement : la route manuelle tenait sa propre
liste de champs, qui avait divergé. Les deux chemins passent désormais par
ce module, et `CHAMPS_EFFACES` / `CHAMPS_GARDES` classent chaque colonne de
`Contact` (un test refuse une colonne non classée).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from app.models.entities import Contact

ANONYMISE = "[ANONYMISÉ]"

# Valeur posée à l'effacement. La relance datée part avec l'identité : sans
# quoi le brief afficherait « Relancer [ANONYMISÉ] ».
CHAMPS_EFFACES: dict[str, Any] = {
    "first_name": ANONYMISE,
    "last_name": None,
    "company": ANONYMISE,
    "email": None,
    "phone": None,
    "address": None,
    "notes": None,
    "tags": None,
    "extra_data": None,
    "next_follow_up": None,
    "stage": "archive",
}

# Gardées : techniques, ou nécessaires au registre (base légale, dates de
# collecte et d'expiration, exclusion de purge).
CHAMPS_GARDES: tuple[str, ...] = (
    "id",
    "score",
    "source",
    "last_interaction",
    "rgpd_base_legale",
    "rgpd_date_collecte",
    "rgpd_date_expiration",
    "rgpd_consentement",
    "purge_excluded",
    "scope",
    "scope_id",
    "created_at",
    "updated_at",
)


def effacer_l_identite(contact: Contact, maintenant: datetime) -> None:
    """Efface l'identité de la fiche, en place (Art. 17)."""
    for champ, valeur in CHAMPS_EFFACES.items():
        setattr(contact, champ, valeur)
    contact.updated_at = maintenant


def exporter_la_fiche(contact: Contact) -> dict[str, Any]:
    """Toutes les colonnes de la fiche, dates en ISO 8601 (Art. 20)."""
    donnees: dict[str, Any] = {}
    for champ in Contact.model_fields:
        valeur = getattr(contact, champ, None)
        donnees[champ] = valeur.isoformat() if isinstance(valeur, datetime) else valeur
    return donnees
