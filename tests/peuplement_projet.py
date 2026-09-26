"""Un projet garni d'un élément de chaque famille qu'il rassemble (P-148).

Partagé par les figeages des trois chemins de suppression d'un projet et par
les tests de la route d'ensemble : les deux doivent parler de la même base,
sinon « le compte annoncé est le compte exécuté » ne se vérifie nulle part.

Chaque appel pose aussi du bruit (un autre projet garni de la même façon, une
conversation et un fichier sans projet) : un total qui compterait tout ce qui
existe, et non ce qui appartient au projet, serait faux ici.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession


@dataclass
class ProjetGarni:
    projet_id: str
    fichier_id: str
    conversation_id: str
    document_id: str
    evenement_id: str
    contact_range_id: str
    sous_dossier_id: str
    taches: list[str] = field(default_factory=list)
    livrable_id: str = ""
    instantane_id: str = ""
    ressource_id: str = ""


async def garnir_un_projet(
    session: AsyncSession,
    projet_id: str,
    *,
    contact_id: str | None = None,
) -> ProjetGarni:
    """Pose le projet et un élément de chaque famille, sans valider la session."""
    from app.models.entities import (
        Calendar,
        CalendarEvent,
        Contact,
        Conversation,
        Deliverable,
        Document,
        FileMetadata,
        PlanningResource,
        PlanningSnapshot,
        Project,
        Task,
    )

    maintenant = datetime.now(UTC)
    session.add(Project(id=projet_id, name=f"Chantier {projet_id}", contact_id=contact_id))
    calendrier = Calendar(id=f"agenda-{projet_id}", summary="Agenda local")
    session.add(calendrier)

    garni = ProjetGarni(
        projet_id=projet_id,
        fichier_id=f"fichier-{projet_id}",
        conversation_id=f"conv-{projet_id}",
        document_id=f"doc-{projet_id}",
        evenement_id=f"rdv-{projet_id}",
        contact_range_id=f"contact-range-{projet_id}",
        sous_dossier_id=f"sous-{projet_id}",
        taches=[f"tache-a-{projet_id}", f"tache-b-{projet_id}"],
        livrable_id=f"livrable-{projet_id}",
        instantane_id=f"instantane-{projet_id}",
        ressource_id=f"ressource-{projet_id}",
    )
    session.add(FileMetadata(
        id=garni.fichier_id, path=f"/p148/{projet_id}/devis.md", name="devis.md",
        extension=".md", size=10, scope="project", scope_id=projet_id, indexed_at=maintenant,
    ))
    session.add(Conversation(
        id=garni.conversation_id, title="Devis cuisine", project_id=projet_id,
        memory_scope="project",
    ))
    session.add(Document(id=garni.document_id, title="Plan de formation", project_id=projet_id))
    session.add(CalendarEvent(
        id=garni.evenement_id, calendar_id=calendrier.id, project_id=projet_id,
        summary="Visite de chantier", start_datetime=maintenant,
    ))
    session.add(Contact(
        id=garni.contact_range_id, first_name="Julien", last_name="Garnier",
        scope="project", scope_id=projet_id,
    ))
    session.add(Project(
        id=garni.sous_dossier_id, name="Plans de la cuisine", scope="project", scope_id=projet_id,
    ))
    for tache_id in garni.taches:
        session.add(Task(id=tache_id, title=f"Tâche {tache_id}", project_id=projet_id))
    session.add(Deliverable(id=garni.livrable_id, project_id=projet_id, title="Plans cotés"))
    session.add(PlanningSnapshot(
        id=garni.instantane_id, project_id=projet_id, engine_version="test",
        input_hash=f"empreinte-{projet_id}", state="complete", result_json="{}",
    ))
    session.add(PlanningResource(id=garni.ressource_id, project_id=projet_id, name="Ludo"))
    return garni


async def poser_du_bruit(session: AsyncSession) -> ProjetGarni:
    """Un autre projet garni, une conversation et un fichier sans projet."""
    from app.models.entities import Conversation, FileMetadata

    autre = await garnir_un_projet(session, "projet-voisin")
    session.add(Conversation(id="conv-sans-projet", title="Question libre"))
    session.add(FileMetadata(
        id="fichier-global", path="/p148/global/notes.md", name="notes.md",
        extension=".md", size=10, scope="global",
    ))
    return autre


async def etat_du_projet_supprime(session: AsyncSession, garni: ProjetGarni) -> dict[str, object]:
    """Relit en base ce que la suppression a fait de chaque famille."""
    from app.models.entities import (
        CalendarEvent,
        Contact,
        Conversation,
        Deliverable,
        Document,
        FileMetadata,
        PlanningResource,
        PlanningSnapshot,
        Project,
        Task,
    )

    conversation = await session.get(Conversation, garni.conversation_id)
    document = await session.get(Document, garni.document_id)
    evenement = await session.get(CalendarEvent, garni.evenement_id)
    contact = await session.get(Contact, garni.contact_range_id)
    sous_dossier = await session.get(Project, garni.sous_dossier_id)
    return {
        "projet": await session.get(Project, garni.projet_id),
        "fichier": await session.get(FileMetadata, garni.fichier_id),
        "conversation": (conversation.project_id, conversation.memory_scope) if conversation else None,
        "document": document.project_id if document else "disparu",
        "evenement": evenement.project_id if evenement else "disparu",
        "contact": (contact.scope, contact.scope_id) if contact else None,
        "sous_dossier": (sous_dossier.scope, sous_dossier.scope_id) if sous_dossier else None,
        "taches": [await session.get(Task, tache_id) for tache_id in garni.taches],
        "livrable": await session.get(Deliverable, garni.livrable_id),
        "instantane": await session.get(PlanningSnapshot, garni.instantane_id),
        "ressource": await session.get(PlanningResource, garni.ressource_id),
    }


#: Ce que chacun des trois chemins doit avoir fait du projet et de ses liens.
ETAT_ATTENDU_APRES_SUPPRESSION: dict[str, object] = {
    "projet": None,
    "fichier": None,
    "conversation": (None, "global"),
    "document": None,
    "evenement": None,
    "contact": ("global", None),
    "sous_dossier": ("global", None),
    "taches": [None, None],
    "livrable": None,
    "instantane": None,
    "ressource": None,
}
