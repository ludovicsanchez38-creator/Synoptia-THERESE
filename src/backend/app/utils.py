"""
THERESE v2 - Utilitaires

Fonctions utilitaires partagees par les modules backend.
"""

from datetime import UTC, datetime


def utc_now() -> datetime:
    """Retourne la date/heure UTC actuelle (timezone-aware).

    Remplace datetime.utcnow() qui est deprecie depuis Python 3.12.
    """
    return datetime.now(UTC)
