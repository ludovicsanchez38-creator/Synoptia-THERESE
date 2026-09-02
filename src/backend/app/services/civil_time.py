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


#: Heure de remplissage d'une échéance de relance.
#: L'écran ne collecte qu'une DATE (`input type="date"`) et écrit cette
#: constante ; les trois lecteurs backend tronquent à dix caractères. La
#: partie horaire n'est donc l'information de personne.
HEURE_DE_RELANCE = "09:00:00"


def echeance_de_relance(valeur: str) -> str:
    """Normalise une échéance de relance en jour civil Paris.

    B-062 : l'API acceptait n'importe quelle chaîne. Une relance posée à
    17 h 30 hors interface portait donc une heure que la première
    modification écrasait en 09:00, sans que rien ne l'annonce — le « report
    qui réécrit l'heure » de la fiche. Normaliser à l'entrée rend la perte
    impossible : il n'y a plus d'heure d'utilisateur à perdre.

    Lève `ValueError` (donc 422) sur une chaîne qui ne désigne aucun jour :
    avant, « la semaine prochaine » atteignait la base et n'était jamais due.
    """
    texte = valeur.strip()
    try:
        instant = datetime.fromisoformat(texte.replace("Z", "+00:00"))
    except ValueError as erreur:
        raise ValueError(
            "Une échéance de relance doit être un jour civil (AAAA-MM-JJ) "
            "ou une date-heure ISO 8601"
        ) from erreur
    return f"{date_civile_paris(instant).isoformat()}T{HEURE_DE_RELANCE}"
