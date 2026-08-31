"""Horloge civile commune aux écrans et relances métier."""

from datetime import UTC, date, datetime
from zoneinfo import ZoneInfo

PARIS = ZoneInfo("Europe/Paris")


def date_civile_paris(instant: datetime | None = None) -> date:
    """Retourne le jour métier à Paris pour un instant absolu."""
    valeur = instant or datetime.now(UTC)
    if valeur.tzinfo is None:
        # Une horloge naïve n'identifie aucun instant fiable. Les appelants
        # historiques la produisent en heure locale, donc on la rattache au
        # fuseau métier avant toute conversion.
        valeur = valeur.replace(tzinfo=PARIS)
    return valeur.astimezone(PARIS).date()
