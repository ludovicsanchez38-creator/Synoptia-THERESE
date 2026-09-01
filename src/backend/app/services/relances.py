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
from app.services.civil_time import date_civile_paris
from sqlalchemy import func
from sqlmodel import select
from sqlmodel.sql.expression import SelectOfScalar


def contacts_a_relancer(maintenant: datetime | None = None) -> SelectOfScalar[Contact]:
    """La requête que TOUTES les surfaces doivent utiliser.

    Toute surface qui réécrit ce filtre chez elle recrée le jumeau. Un test
    (`test_relance_une_seule_definition.py`) fige l'égalité des deux
    consommateurs.
    """
    seuil = date_civile_paris(maintenant or datetime.now(UTC)).isoformat()
    return (
        select(Contact)
        .where(
            Contact.next_follow_up != None,  # noqa: E711
            # `next_follow_up` représente un JOUR décidé, même si le schéma
            # historique l'a stocké dans un DateTime. Comparer les instants
            # faisait commencer le 30 à minuit UTC au lieu de minuit à Paris.
            func.date(Contact.next_follow_up) <= seuil,
            # `archive` est le tombeau RGPD, pas une etape commerciale :
            # l'anonymisation y pose la fiche et efface tout SAUF cette date.
            # Sans cette exclusion, le brief afficherait « Relancer [ANONYMISE] ».
            Contact.stage != "archive",
        )
        # Sans tri explicite, l'ordre est celui de SQLite : la relance la plus
        # en retard peut finir en bas de l'ecran.
        .order_by(Contact.next_follow_up)
    )


# Ce qui compte comme « avoir relance » : un geste VERS la personne. Ecrire une
# note ne l'est pas. Une note de correction (« CORRECTION de ma note de ce
# matin ») eteignait le devoir en silence avant le correctif du 29/08 au soir.
GESTES_QUI_SOLDENT = frozenset({"call", "email", "meeting"})


def solder_la_relance(contact: Contact) -> None:
    """Eteint le devoir. L'appelant commit.

    Sans ce geste, une date echue reste au brief pour toujours : on aurait
    remplace un devoir invente par un devoir eternel.
    """
    contact.next_follow_up = None
