"""B-1438 (recette P-146, lot 2, K1) : sur une fiche, l'export Art. 20 ne
contenait pas l'adresse, et l'anonymisation Art. 17 la laissait en clair
(la fiche l'affichait encore). B-880 avait corrigé la seule purge
automatique : la route manuelle tenait sa propre liste de champs.

Désormais un seul traitement efface l'identité, pour la route comme pour la
purge, et l'export rend toutes les colonnes de la fiche. Une garde oblige à
classer toute nouvelle colonne (effacée ou gardée)."""

from datetime import UTC, datetime, timedelta

import pytest
from app.models.entities import Contact
from httpx import AsyncClient

from tests.rgpd_preavis import preavis_ancien_pour_tous

ADRESSE = "3 place de l'Hôtel de Ville, 04100 Manosque"


async def _nadia(client: AsyncClient) -> str:
    reponse = await client.post("/api/memory/contacts", json={
        "first_name": "Nadia", "last_name": "Roux", "company": "Roux Conseil",
        "email": "nadia@example.test", "phone": "06 00 00 00 00", "address": ADRESSE,
    })
    assert reponse.status_code in (200, 201), reponse.text
    return reponse.json()["id"]


@pytest.mark.asyncio
async def test_l_export_contient_toutes_les_colonnes_de_la_fiche(client: AsyncClient):
    cid = await _nadia(client)
    exporte = (await client.get(f"/api/rgpd/export/{cid}")).json()["contact"]
    assert exporte["address"] == ADRESSE
    colonnes = set(Contact.model_fields) - {"projects", "activities", "invoices"}
    assert colonnes <= set(exporte), colonnes - set(exporte)


@pytest.mark.asyncio
async def test_l_anonymisation_efface_l_adresse_et_la_relance(client: AsyncClient, db_session):
    cid = await _nadia(client)
    contact = await db_session.get(Contact, cid)
    contact.next_follow_up = datetime.now(UTC) + timedelta(days=3)
    db_session.add(contact)
    await db_session.commit()

    assert (await client.post(f"/api/rgpd/anonymize/{cid}", json={"reason": "demande"})).status_code == 200
    exporte = (await client.get(f"/api/rgpd/export/{cid}")).json()["contact"]
    assert exporte["address"] is None
    # Une relance survivante afficherait « Relancer [ANONYMISÉ] » au brief.
    assert exporte["next_follow_up"] is None
    assert exporte["first_name"] == "[ANONYMISÉ]"


def test_chaque_colonne_de_la_fiche_est_classee():
    from app.services.rgpd_identite import CHAMPS_EFFACES, CHAMPS_GARDES

    colonnes = set(Contact.model_fields) - {"projects", "activities", "invoices"}
    non_classees = colonnes - set(CHAMPS_EFFACES) - set(CHAMPS_GARDES)
    assert not non_classees, f"colonnes à classer (effacée ou gardée) : {non_classees}"
    assert not set(CHAMPS_EFFACES) & set(CHAMPS_GARDES)


@pytest.mark.asyncio
async def test_la_purge_automatique_efface_aussi_la_relance(db_session):
    from unittest.mock import AsyncMock, patch

    from app.models.entities import Preference
    from app.services import rgpd_auto
    from sqlmodel import select

    db_session.add(Preference(key="rgpd_purge_enabled", value="true"))
    db_session.add(Preference(key="rgpd_purge_months", value="12"))
    contact = Contact(
        first_name="Paul", last_name="Blanc", address="12 rue des Lilas, 04100 Manosque",
        next_follow_up=datetime.now(UTC) + timedelta(days=2),
        last_interaction=datetime.now(UTC) - timedelta(days=13 * 30),
    )
    db_session.add(contact)
    await db_session.commit()
    cid = contact.id

    # B-1641 : l'anonymisation automatique exige un préavis de 30 jours.
    await preavis_ancien_pour_tous(db_session)
    with patch.object(rgpd_auto, "purge_contact_vector", new=AsyncMock(return_value=1)):
        await rgpd_auto.auto_purge_expired_contacts()
    db_session.expire_all()
    releve = (await db_session.execute(select(Contact).where(Contact.id == cid))).scalar_one()
    assert releve.address is None and releve.next_follow_up is None
