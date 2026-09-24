"""B-1083 (lecteur G1, dernière passe de la carte c12) : réimporter un fichier
de projets sans colonne contact ni statut déliait chaque projet de son client
et le repassait en « active ». Une colonne absente, vide ou inconnue ne doit
rien effacer de la fiche existante.
"""

from __future__ import annotations

import pytest
from app.models.entities import Contact, Project
from app.services.crm_import import CRMImportService


async def _projet_lie(session) -> Project:
    contact = Contact(id="contact-b1083", first_name="Jeanne", last_name="Martin", scope="global")
    projet = Project(id="projet-b1083", name="Chantier Martin", contact_id=contact.id, status="on_hold")
    session.add(contact)
    session.add(projet)
    await session.commit()
    return projet


async def _relire(session) -> Project:
    await session.commit()
    projet = await session.get(Project, "projet-b1083")
    await session.refresh(projet)
    return projet


@pytest.mark.asyncio
async def test_un_fichier_sans_colonne_contact_ni_statut_ne_delie_rien(db_session):
    await _projet_lie(db_session)
    resultat = await CRMImportService(db_session).import_projects(b"id,name\nprojet-b1083,Chantier Martin bis\n", "projets.csv")
    assert resultat.updated == 1, resultat
    projet = await _relire(db_session)
    assert projet.name == "Chantier Martin bis"
    assert projet.contact_id == "contact-b1083"
    assert projet.status == "on_hold"


@pytest.mark.asyncio
async def test_un_contact_inconnu_ou_un_statut_inconnu_ne_remplacent_rien(db_session):
    await _projet_lie(db_session)
    await CRMImportService(db_session).import_projects(
        b"id,name,contact_id,status\nprojet-b1083,Chantier Martin,contact-absent,Gele\n", "projets.csv"
    )
    projet = await _relire(db_session)
    assert projet.contact_id == "contact-b1083"
    assert projet.status == "on_hold"


@pytest.mark.asyncio
async def test_un_statut_reconnu_est_toujours_applique(db_session):
    await _projet_lie(db_session)
    await CRMImportService(db_session).import_projects(b"id,name,status\nprojet-b1083,Chantier Martin,termine\n", "projets.csv")
    projet = await _relire(db_session)
    assert projet.status == "completed"
    assert projet.contact_id == "contact-b1083"
