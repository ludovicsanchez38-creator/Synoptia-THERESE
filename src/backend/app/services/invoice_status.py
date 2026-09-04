"""Statut métier effectif des pièces de facturation."""

from datetime import UTC, date, datetime

from app.services.civil_time import date_civile_paris


def statut_effectif_facture(
    statut: str,
    type_document: str,
    echeance: datetime | None,
    *,
    aujourd_hui: date | None = None,
) -> str:
    """Retourne le statut visible, en tenant compte de l'échéance civile.

    Une facture envoyée devient en retard dès le lendemain de son échéance.
    Les devis gardent leur statut propre : leur date est une validité, pas une
    échéance de paiement. Un ancien statut ``overdue`` explicite reste honoré
    afin de ne pas masquer les données historiques.
    """
    if (
        type_document == "facture"
        and statut == "sent"
        and echeance is not None
        and date_civile_paris(echeance)
        < (aujourd_hui or date_civile_paris(datetime.now(UTC)))
    ):
        return "overdue"
    return statut
