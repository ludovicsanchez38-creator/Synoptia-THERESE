"""P-148, constat 10 de la revue : figer les trois chemins qui suppriment un projet.

`_nettoyer_et_supprimer_projet` a trois appelants : la route
`DELETE /api/memory/projects/{id}`, la suppression d'un contact en cascade
(`DELETE /api/memory/contacts/{id}?cascade=true`) et l'anonymisation RGPD
(`POST /api/rgpd/anonymize/{id}`). P-148 fait lire ses clauses à la route
d'ensemble, pour que le compte annoncé soit le compte exécuté. Ces tests sont
écrits AVANT cette refonte : ils figent l'effet en base et le rapport de
chacun des trois chemins, sur un projet garni d'un élément de chaque famille
et à côté d'un projet voisin qui ne doit pas bouger.
"""

from __future__ import annotations

import pytest

from tests.peuplement_projet import (
    ETAT_ATTENDU_APRES_SUPPRESSION,
    ProjetGarni,
    etat_du_projet_supprime,
    garnir_un_projet,
    poser_du_bruit,
)

RAPPORT_D_UN_PROJET_GARNI = {
    "files": 1,
    "conversations_detachees": 1,
    "documents_detaches": 1,
    "evenements_detaches": 1,
    "contacts_rendus_au_general": 1,
    "sous_dossiers_rendus_au_general": 1,
    "taches_supprimees": 2,
    "livrables_supprimes": 1,
}


async def _voisin_intact(voisin: ProjetGarni) -> None:
    from app.models import database as db_module

    async with db_module.AsyncSessionLocal() as session:
        etat = await etat_du_projet_supprime(session, voisin)
    assert etat["projet"] is not None
    assert etat["fichier"] is not None
    assert etat["conversation"] == (voisin.projet_id, "project")
    assert etat["document"] == voisin.projet_id
    assert etat["evenement"] == voisin.projet_id
    assert etat["contact"] == ("project", voisin.projet_id)
    assert etat["sous_dossier"] == ("project", voisin.projet_id)
    taches = etat["taches"]
    assert isinstance(taches, list) and all(tache is not None for tache in taches)
    assert etat["livrable"] is not None
    assert etat["instantane"] is not None
    assert etat["ressource"] is not None


async def _garnir(contact_id: str | None = None) -> tuple[ProjetGarni, ProjetGarni]:
    from app.models import database as db_module
    from app.models.entities import Contact

    async with db_module.AsyncSessionLocal() as session:
        if contact_id:
            session.add(Contact(id=contact_id, first_name="Camille", last_name="Roux"))
        garni = await garnir_un_projet(session, "projet-cible", contact_id=contact_id)
        voisin = await poser_du_bruit(session)
        await session.commit()
    return garni, voisin


async def _etat(garni: ProjetGarni) -> dict[str, object]:
    from app.models import database as db_module

    async with db_module.AsyncSessionLocal() as session:
        return await etat_du_projet_supprime(session, garni)


@pytest.mark.asyncio
async def test_la_route_de_suppression_d_un_projet(client):
    garni, voisin = await _garnir()

    reponse = await client.delete(f"/api/memory/projects/{garni.projet_id}")

    assert reponse.status_code == 200, reponse.text
    assert reponse.json()["cascade_deleted"] == RAPPORT_D_UN_PROJET_GARNI
    assert await _etat(garni) == ETAT_ATTENDU_APRES_SUPPRESSION
    await _voisin_intact(voisin)


@pytest.mark.asyncio
async def test_la_suppression_d_un_contact_en_cascade(client):
    garni, voisin = await _garnir(contact_id="contact-camille")

    reponse = await client.delete("/api/memory/contacts/contact-camille?cascade=true")

    assert reponse.status_code == 200, reponse.text
    assert reponse.json()["cascade_deleted"] == {
        "activities": 0,
        **RAPPORT_D_UN_PROJET_GARNI,
        "projects": 1,
    }
    assert await _etat(garni) == ETAT_ATTENDU_APRES_SUPPRESSION
    await _voisin_intact(voisin)


@pytest.mark.asyncio
async def test_l_anonymisation_rgpd(client):
    garni, voisin = await _garnir(contact_id="contact-camille")

    reponse = await client.post(
        "/api/rgpd/anonymize/contact-camille", json={"reason": "demande du client"}
    )

    assert reponse.status_code == 200, reponse.text
    assert "1 dossier du contact a été supprimé" in reponse.json()["message"]
    assert await _etat(garni) == ETAT_ATTENDU_APRES_SUPPRESSION
    await _voisin_intact(voisin)
