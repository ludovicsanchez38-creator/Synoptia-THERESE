"""
Une tâche doit pouvoir nommer la personne qu'elle concerne (plan du 29/08, lot 3).

Sans `contact_id`, les 74 tâches importées du CRM de Ludo sont des chaînes de
caractères qui ressemblent à du travail : on ne peut ni les regrouper par
client, ni les retrouver depuis une fiche, ni savoir que « Relancer Dupont »
et le prospect Dupont sont la même personne.
"""

import pytest
from app.models.entities import Contact, Task
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select


@pytest.mark.asyncio
async def test_une_tache_porte_son_contact(db_session: AsyncSession):
    contact = Contact(first_name="Nicolas", last_name="Ponzo")
    db_session.add(contact)
    await db_session.commit()

    db_session.add(Task(title="Relancer Nicolas Ponzo", contact_id=contact.id))
    await db_session.commit()

    trouvee = (
        await db_session.execute(select(Task).where(Task.contact_id == contact.id))
    ).scalars().one()
    assert trouvee.title == "Relancer Nicolas Ponzo"


@pytest.mark.asyncio
async def test_une_tache_sans_contact_reste_permise(db_session: AsyncSession):
    """Tout travail n'est pas rattaché à quelqu'un. Le champ est facultatif."""
    db_session.add(Task(title="Refaire la page tarifs"))
    await db_session.commit()

    trouvee = (
        await db_session.execute(select(Task).where(Task.contact_id == None))  # noqa: E711
    ).scalars().one()
    assert trouvee.contact_id is None


@pytest.mark.asyncio
async def test_l_api_pose_et_rend_le_contact(client):
    """Le parcours, pas le modèle : sans écriture ni lecture, le champ ne sert à rien."""
    fiche = (
        await client.post(
            "/api/memory/contacts", json={"first_name": "Joyce", "last_name": "Poussin"}
        )
    ).json()

    creee = await client.post(
        "/api/tasks", json={"title": "Rappeler Joyce", "contact_id": fiche["id"]}
    )
    assert creee.status_code in (200, 201), creee.text
    assert creee.json()["contact_id"] == fiche["id"]

    # Une tâche SANS contact, sinon le filtre ne se distingue pas de « tout
    # rendre » : la première version de ce test passait sans filtre du tout.
    await client.post("/api/tasks", json={"title": "Refaire la page tarifs"})

    listee = await client.get(f"/api/tasks?contact_id={fiche['id']}")
    assert listee.status_code == 200
    assert [t["title"] for t in listee.json()] == ["Rappeler Joyce"]

    # La lecture unitaire rend aussi le lien.
    relue = await client.get(f"/api/tasks/{creee.json()['id']}")
    assert relue.json()["contact_id"] == fiche["id"]


@pytest.mark.asyncio
async def test_supprimer_un_contact_ne_detruit_pas_ses_taches(client, db_session: AsyncSession):
    """Une tâche est du travail, pas une dépendance de la fiche.

    Si supprimer un contact effaçait ses tâches, on perdrait du travail sans
    le dire. Le lien se dénoue, la tâche reste.
    """
    contact = Contact(first_name="Ancien", last_name="Client")
    db_session.add(contact)
    await db_session.commit()
    db_session.add(Task(title="Solder la facture", contact_id=contact.id))
    await db_session.commit()

    reponse = await client.delete(f"/api/memory/contacts/{contact.id}")
    assert reponse.status_code == 200, reponse.text
    db_session.expire_all()

    restante = (
        await db_session.execute(select(Task).where(Task.title == "Solder la facture"))
    ).scalars().one()
    assert restante.contact_id is None, (
        "le lien se dénoue, la tâche reste : sinon on perd du travail en silence"
    )
