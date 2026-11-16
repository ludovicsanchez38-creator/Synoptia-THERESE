"""Un échec d'effacement du dépôt doit être signalé à l'utilisateur."""

import shutil
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock

import pytest
from app.models.entities import Contact, Notification, Preference, Project
from app.routers import memory
from app.services import qdrant, rgpd_auto
from sqlmodel import select

from tests.rgpd_preavis import preavis_ancien_pour_tous


@pytest.mark.asyncio
async def test_anonymisation_signale_un_depot_restant(client, db_session, monkeypatch, tmp_path):
    db_session.add(Contact(id="personne-test", first_name="Personne"))
    db_session.add(Project(id="dossier-test", name="Dossier", contact_id="personne-test"))
    await db_session.commit()
    depot = tmp_path / "dossier-test"
    depot.mkdir()
    document = depot / "document.txt"
    document.write_text("donnée fictive", encoding="utf-8")
    monkeypatch.setattr(memory, "racine_des_depots", lambda: tmp_path.resolve())

    def retrait_impossible(_chemin, *args, **kwargs):
        if not kwargs.get("ignore_errors"):
            raise OSError("retrait simulé impossible")

    monkeypatch.setattr(shutil, "rmtree", retrait_impossible)
    reponse = await client.post(
        "/api/rgpd/anonymize/personne-test", json={"reason": "demande de test"}
    )
    assert document.exists()
    if reponse.status_code < 400:
        contenu = reponse.json()
        message = contenu.get("message", "").lower()
        assert contenu.get("success") is False or any(
            indication in message for indication in ("échec", "impossible", "pas pu", "non supprim")
        )


@pytest.mark.asyncio
async def test_anonymisation_signale_un_index_de_recherche_non_purge(client, db_session, monkeypatch):
    db_session.add(Contact(id="personne-index", first_name="Personne"))
    await db_session.commit()
    service = qdrant.get_qdrant_service()
    monkeypatch.setattr(service, "async_delete_by_entity", AsyncMock(side_effect=OSError("panne fictive")))

    reponse = await client.post(
        "/api/rgpd/anonymize/personne-index", json={"reason": "demande de test"}
    )
    assert reponse.status_code == 200
    assert reponse.json()["success"] is False
    assert "recherche" in reponse.json()["message"]


@pytest.mark.asyncio
async def test_purge_automatique_signale_les_elements_restants(db_session, monkeypatch):
    db_session.add(Preference(key="rgpd_purge_enabled", value="true"))
    db_session.add(Preference(key="rgpd_purge_months", value="12"))
    db_session.add(Contact(
        id="personne-auto", first_name="Personne",
        last_interaction=datetime.now(UTC) - timedelta(days=13 * 30),
    ))
    db_session.add(Project(id="dossier-auto", name="Dossier", contact_id="personne-auto"))
    await db_session.commit()
    await preavis_ancien_pour_tous(db_session)
    monkeypatch.setattr(rgpd_auto, "purge_contact_vector", AsyncMock(return_value=None))
    monkeypatch.setattr(memory, "_purger_le_depot_du_dossier", AsyncMock(return_value=False))

    resultat = await rgpd_auto.auto_purge_expired_contacts()
    assert resultat["anonymisations"] == 0
    assert resultat["anonymisations_incompletes"] == 1
    db_session.expire_all()
    notification = (await db_session.execute(
        select(Notification).where(Notification.source == "rgpd_purge_done")
    )).scalar_one()
    assert notification.type == "warning"
    assert "incomplète" in notification.title
    assert "recherche" in notification.message and "dossier-auto" in notification.message
