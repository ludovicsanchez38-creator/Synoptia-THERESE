"""
La prestation (tranche C du 29/08).

Ludo vend des formations. Une négociation, c'est une formation pas encore
signée ; un client actif, c'est la même chose en cours. Séparer « affaire » et
« action de formation » aurait garanti deux pipelines, deux montants, deux
étapes — c'est pour ça que l'objet ne s'appelle pas Opportunity.

Le plus petit objet qui ne mente pas : qui, quoi, combien, où ça en est.
Rien de plus. Pas de BANT, pas d'objections, pas de score : `extra_data` a
déjà appris que ranger une donnée sans surface, c'est la jeter.
"""
import json

import pytest
from app.models.entities import Contact, Prestation
from app.services.memory_tools import execute_memory_tool
from sqlalchemy.ext.asyncio import AsyncSession


async def _client(session: AsyncSession, nom: str = "Esmieu") -> Contact:
    c = Contact(first_name="Nathalie", last_name=nom)
    session.add(c)
    await session.commit()
    return c


@pytest.mark.asyncio
async def test_une_personne_porte_plusieurs_prestations(db_session: AsyncSession):
    """Le seul motif qui justifiait l'entité : une personne, une étape, c'est faux.

    Un client qui rouvre une négociation est à la fois en cours et en
    proposition. `Contact.stage` ne peut pas dire les deux.
    """
    c = await _client(db_session)
    db_session.add(Prestation(contact_id=c.id, intitule="PROPULSER", phase="en_cours"))
    db_session.add(Prestation(contact_id=c.id, intitule="RAYONNER", phase="proposition"))
    await db_session.commit()

    listees = await db_session.execute(
        Prestation.__table__.select().where(Prestation.contact_id == c.id)
    )
    assert len(listees.fetchall()) == 2


@pytest.mark.asyncio
async def test_un_montant_absent_n_est_pas_zero(db_session: AsyncSession):
    """Poser 0 serait affirmer que la prestation est gratuite."""
    c = await _client(db_session)
    p = Prestation(contact_id=c.id, intitule="Diagnostic IA", phase="piste")
    db_session.add(p)
    await db_session.commit()

    assert p.montant_ht is None


@pytest.mark.asyncio
async def test_l_api_pose_lit_et_modifie_une_prestation(client):
    fiche = (await client.post(
        "/api/memory/contacts", json={"first_name": "Andre", "last_name": "Valencot"}
    )).json()

    creee = await client.post("/api/prestations", json={
        "contact_id": fiche["id"], "intitule": "FORGER", "montant_ht": 490.0, "phase": "proposition",
    })
    assert creee.status_code in (200, 201), creee.text
    assert creee.json()["intitule"] == "FORGER"

    # Une SECONDE personne, sinon le filtre ne se distingue pas de « tout
    # rendre » (meme piege que le filtre des taches, trouve par sabotage).
    autre = (await client.post(
        "/api/memory/contacts", json={"first_name": "Autre", "last_name": "Client"}
    )).json()
    await client.post("/api/prestations", json={
        "contact_id": autre["id"], "intitule": "PROPULSER", "phase": "piste",
    })

    listees = await client.get(f"/api/prestations?contact_id={fiche['id']}")
    assert [p["intitule"] for p in listees.json()] == ["FORGER"]

    modifiee = await client.patch(
        f"/api/prestations/{creee.json()['id']}", json={"phase": "gagne"}
    )
    assert modifiee.status_code == 200, modifiee.text
    assert modifiee.json()["phase"] == "gagne"


@pytest.mark.asyncio
async def test_une_phase_inventee_est_refusee(client):
    fiche = (await client.post(
        "/api/memory/contacts", json={"first_name": "Phase", "last_name": "Invalide"}
    )).json()

    reponse = await client.post("/api/prestations", json={
        "contact_id": fiche["id"], "intitule": "X", "phase": "peut-etre",
    })

    assert reponse.status_code in (400, 422), reponse.text


@pytest.mark.asyncio
async def test_l_etat_courant_derive_des_prestations_ouvertes(db_session: AsyncSession):
    """Le manuscrit meurt : l'état vient enfin d'un objet, pas d'un texte.

    C'est le but de toute la séquence A → B → C. Tant que rien n'était posé,
    `etat_courant` restait vide et l'application se taisait.
    """
    c = await _client(db_session)
    c.notes = "FORGER 490 EUR"  # le résumé périmé, toujours là
    db_session.add(Prestation(contact_id=c.id, intitule="PROPULSER", montant_ht=2490.0,
                              phase="en_cours"))
    db_session.add(Prestation(contact_id=c.id, intitule="FORGER ancien", phase="perdue"))
    await db_session.commit()

    charge = json.loads(await execute_memory_tool("read_contact", {"query": "Esmieu"}, db_session))
    fiche = charge["contacts"][0]

    assert fiche["etat_courant"] is not None
    intitules = [p["intitule"] for p in fiche["etat_courant"]["prestations_ouvertes"]]
    assert intitules == ["PROPULSER"], "seules les prestations OUVERTES sont un état"
    assert "FORGER 490 EUR" in " ".join(
        (t.get("texte") or "") for t in fiche["traces"]
    ), "le résumé périmé descend en trace, il ne disparaît pas"


@pytest.mark.asyncio
async def test_sans_prestation_l_application_se_tait_toujours(db_session: AsyncSession):
    c = await _client(db_session, nom="Muette")
    c.notes = "Un resume manuscrit qui a l'air d'un etat"
    db_session.add(c)
    await db_session.commit()

    charge = json.loads(await execute_memory_tool("read_contact", {"query": "Muette"}, db_session))

    assert charge["contacts"][0]["etat_courant"] is None


@pytest.mark.asyncio
async def test_supprimer_un_contact_emporte_ses_prestations(client, db_session: AsyncSession):
    """Une prestation SANS personne n'a pas de sens : elle n'est pas du travail
    autonome comme une tâche, c'est un engagement AVEC quelqu'un."""
    fiche = (await client.post(
        "/api/memory/contacts", json={"first_name": "Parti", "last_name": "Client"}
    )).json()
    await client.post("/api/prestations", json={
        "contact_id": fiche["id"], "intitule": "FORGER", "phase": "piste",
    })

    suppression = await client.delete(f"/api/memory/contacts/{fiche['id']}")
    assert suppression.status_code == 200, suppression.text

    restantes = await client.get(f"/api/prestations?contact_id={fiche['id']}")
    assert restantes.json() == []


@pytest.mark.asyncio
async def test_un_intitule_vide_est_refuse(client):
    """« Prestation sans nom » n'est pas une prestation : c'est une ligne vide
    dans une liste que Ludo devra deviner."""
    fiche = (await client.post(
        "/api/memory/contacts", json={"first_name": "Sans", "last_name": "Intitule"}
    )).json()

    reponse = await client.post("/api/prestations", json={
        "contact_id": fiche["id"], "intitule": "   ", "phase": "piste",
    })

    assert reponse.status_code in (400, 422), reponse.text


@pytest.mark.asyncio
async def test_une_prestation_sur_un_contact_inconnu_est_refusee(client):
    """Sinon elle serait orpheline dès sa naissance."""
    reponse = await client.post("/api/prestations", json={
        "contact_id": "ce-contact-n-existe-pas", "intitule": "FORGER", "phase": "piste",
    })

    assert reponse.status_code == 404, reponse.text
