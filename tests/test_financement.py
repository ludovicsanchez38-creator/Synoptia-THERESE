"""
Le dossier de financement (tranche E1 du 29/08).

C'est ce que les notes de Ludo corrigent le plus : « CORRECTION de ma note de
ce matin : le dossier AFDAS est DEPOSE ET VALIDE depuis le 27/07 », « Relance
OPCO Atlas 08/08 », « Atlas répond : ne pas maintenir la séance du 24 sans
l'attestation fiscale ». 17 des 120 notes importées parlent d'un financeur.

Grok : « Pas un deuxième objet si un champ suffit. » C'est un état de la
prestation, pas une entité : un dossier de financement sans prestation ne veut
rien dire.
"""
import json

import pytest
from app.models.entities import Contact, Prestation
from app.services.memory_tools import execute_memory_tool
from sqlalchemy.ext.asyncio import AsyncSession


async def _prestation(session: AsyncSession, **kw) -> tuple[Contact, Prestation]:
    c = Contact(first_name="Nathalie", last_name="Esmieu")
    session.add(c)
    await session.commit()
    p = Prestation(contact_id=c.id, intitule="PROPULSER", phase="en_cours", **kw)
    session.add(p)
    await session.commit()
    return c, p


@pytest.mark.asyncio
async def test_une_prestation_naît_sans_financeur(db_session: AsyncSession):
    """La plupart des prestations n'en ont pas. Rien ne doit être affirmé."""
    _, p = await _prestation(db_session)

    assert p.financeur is None
    assert p.statut_financement is None


@pytest.mark.asyncio
async def test_l_api_pose_le_financeur_et_son_statut(client):
    fiche = (await client.post(
        "/api/memory/contacts", json={"first_name": "Andre", "last_name": "Valencot"}
    )).json()
    p = (await client.post("/api/prestations", json={
        "contact_id": fiche["id"], "intitule": "FORGER", "phase": "gagne",
    })).json()

    maj = await client.patch(f"/api/prestations/{p['id']}", json={
        "financeur": "AFDAS", "statut_financement": "depose",
    })

    assert maj.status_code == 200, maj.text
    assert maj.json()["financeur"] == "AFDAS"
    assert maj.json()["statut_financement"] == "depose"


@pytest.mark.asyncio
async def test_un_statut_de_financement_invente_est_refuse(client):
    fiche = (await client.post(
        "/api/memory/contacts", json={"first_name": "Statut", "last_name": "Faux"}
    )).json()
    p = (await client.post("/api/prestations", json={
        "contact_id": fiche["id"], "intitule": "FORGER", "phase": "piste",
    })).json()

    # AVEC un financeur, sinon c'est l'autre garde qui refuse et ce test ne
    # distingue rien (trouvé par sabotage).
    reponse = await client.patch(f"/api/prestations/{p['id']}", json={
        "financeur": "AFDAS", "statut_financement": "peut-etre",
    })

    assert reponse.status_code in (400, 422), reponse.text
    assert "statut_financement" in reponse.text


@pytest.mark.asyncio
async def test_un_statut_sans_financeur_est_refuse(client):
    """« Déposé » chez qui ? Un statut sans financeur ne dit rien."""
    fiche = (await client.post(
        "/api/memory/contacts", json={"first_name": "Sans", "last_name": "Financeur"}
    )).json()
    p = (await client.post("/api/prestations", json={
        "contact_id": fiche["id"], "intitule": "FORGER", "phase": "piste",
    })).json()

    reponse = await client.patch(f"/api/prestations/{p['id']}", json={
        "statut_financement": "depose",
    })

    assert reponse.status_code == 400, reponse.text


@pytest.mark.asyncio
async def test_le_modele_voit_le_financement_dans_l_etat(db_session: AsyncSession):
    """C'est un ÉTAT, pas une trace : quelqu'un l'a posé."""
    await _prestation(db_session, financeur="AFDAS", statut_financement="valide")

    charge = json.loads(await execute_memory_tool("read_contact", {"query": "Esmieu"}, db_session))
    etat = charge["contacts"][0]["etat_courant"]["prestations_ouvertes"][0]

    assert etat["financeur"] == "AFDAS"
    assert etat["statut_financement"] == "valide"
