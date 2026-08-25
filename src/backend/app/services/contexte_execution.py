"""Contexte d'exécution d'une génération de chat (0.47, phase fencing).

Le drapeau d'annulation historique était indexé par conversation : deux
générations chevauchées pouvaient fencer la mauvaise, et les outils ne
recevaient aucun signal. Le `ContexteExecution` est l'AUTORITÉ : un unique
token par génération alimente le flux SSE, l'adaptateur canonique, le
fallback d'indexation et les outils. Aucun service n'importe
`routers.chat` : le contexte descend du chat vers les handlers en
paramètre.

Promesse (design V2.1) : « aucun nouvel effet MÉTIER local après
observation de l'annulation » - la consignation du traitement et le
message partiel sont explicitement exclus.
"""

import asyncio
from dataclasses import dataclass, field

# Classes d'effet des outils du dispatcher. Un outil non classé échappe au
# raisonnement d'annulation : le test de complétude le rend rouge.
LECTURE_SEULE = "read_only"
MUTATION_LOCALE = "local_mutation"
MUTATION_EXTERNE = "external_mutation"

CLASSIFICATION_DES_OUTILS: dict[str, str] = {
    # Outils mémoire
    "create_contact": MUTATION_LOCALE,
    "create_project": MUTATION_LOCALE,
    "read_contact": LECTURE_SEULE,
    # Outils workspace
    "read_emails": LECTURE_SEULE,
    "summarize_emails": LECTURE_SEULE,
    "send_email": MUTATION_EXTERNE,
    "search_emails": LECTURE_SEULE,
    "list_calendar_events": LECTURE_SEULE,
    # Geste confirmé séparément (carte de confirmation) : la mutation
    # n'est PAS immédiate, le fencing du calendrier est hors périmètre.
    "create_calendar_event": MUTATION_LOCALE,
    "generate_document": MUTATION_LOCALE,
    "search_invoices": LECTURE_SEULE,
    # Outils intégrés
    "web_search": MUTATION_EXTERNE,
    "browser_navigate": MUTATION_EXTERNE,
}


def classe_de(nom: str) -> str:
    """Classe d'effet d'un outil. Un outil MCP inconnu est externe par
    nature : dans le doute, la classe la plus prudente."""
    return CLASSIFICATION_DES_OUTILS.get(nom, MUTATION_EXTERNE)


@dataclass
class ContexteExecution:
    """Identité et token d'annulation d'UNE génération.

    Le token n'est jamais partagé entre générations : annuler la
    conversation pose le token de la génération COURANTE, jamais celui
    d'une génération remplacée.
    """

    generation_id: str | None = None
    arret: asyncio.Event = field(default_factory=asyncio.Event, repr=False)

    def annulation_observee(self) -> bool:
        return self.arret.is_set()

    def demander_arret(self) -> None:
        self.arret.set()
