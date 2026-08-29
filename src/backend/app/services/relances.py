"""
La définition unique de « à relancer » (plan du 29/08/2026, lot 2).

Avant ce module, deux surfaces répondaient différemment à la même question.
Sur les vraies données de Ludo, l'accueil comptait 24 contacts à relancer et
la cloche 20 : l'un comptait ceux qui n'avaient aucune date, l'autre les
excluait. Deux bouches, deux chiffres.

La règle est désormais qu'une relance est une **date posée et échue**. Elle
n'est plus déduite d'une absence d'interaction : quelqu'un qui n'a rien
demandé depuis deux ans ne doit rien, et l'application n'a pas à l'affirmer.

L'étape ne filtre pas. Les vraies échéances (questionnaire à froid, séance,
attestation d'un financeur) portent sur des contacts déjà clients, que
l'ancienne règle ne regardait même pas.
"""

from datetime import UTC, datetime

from app.models.entities import Contact
from sqlmodel import select
from sqlmodel.sql.expression import SelectOfScalar


def contacts_a_relancer(maintenant: datetime | None = None) -> SelectOfScalar[Contact]:
    """La requête que TOUTES les surfaces doivent utiliser.

    Toute surface qui réécrit ce filtre chez elle recrée le jumeau. Un test
    (`test_relance_une_seule_definition.py`) fige l'égalité des deux
    consommateurs.
    """
    seuil = maintenant or datetime.now(UTC)
    return select(Contact).where(
        Contact.next_follow_up != None,  # noqa: E711
        Contact.next_follow_up <= seuil,
    )
