"""L'export annoncé complet doit inclure les données CRM enregistrées."""

import pytest
from app.models.entities import (
    Activity,
    Calendar,
    Conversation,
    Deliverable,
    EmailAccount,
    Preference,
    Project,
)


@pytest.mark.asyncio
async def test_export_config_inclut_les_activites_et_livrables(client, db_session):
    db_session.add(Project(id="projet-export", name="Projet d'essai"))
    await db_session.flush()
    db_session.add_all([
        Activity(id="activite-export", project_id="projet-export", type="note", title="Note"),
        Deliverable(id="livrable-export", project_id="projet-export", title="Compte rendu"),
        Conversation(id="conversation-export", project_id="projet-export", memory_scope="project"),
    ])
    await db_session.commit()

    reference = await client.get("/api/data/export")
    assert reference.status_code == 200
    assert "activite-export" in {a["id"] for a in reference.json()["activities"]}
    assert "livrable-export" in {d["id"] for d in reference.json()["deliverables"]}

    reponse = await client.post("/api/config/export")
    assert reponse.status_code == 200
    export = reponse.json()
    activites = {a["id"] for a in export.get("activities", [])}
    livrables = {d["id"] for d in export.get("deliverables", [])}
    assert ("activite-export" in activites, "livrable-export" in livrables) == (True, True)
    conversation = next(c for c in export["conversations"] if c["id"] == "conversation-export")
    assert conversation["project_id"] == "projet-export"
    assert conversation["memory_scope"] == "project"


@pytest.mark.asyncio
async def test_export_config_exclut_les_secrets_de_connexion(client, db_session):
    temoin = "valeur-confidentielle-fictive"
    db_session.add(Preference(key="crm_sheets_refresh_token", value=temoin, category="crm"))
    db_session.add(EmailAccount(
        id="compte-export", email="test@example.invalid", client_secret=temoin,
        access_token=temoin, refresh_token=temoin, imap_password=temoin,
    ))
    db_session.add(Calendar(id="cal-export", summary="Agenda", caldav_password=temoin))
    await db_session.commit()

    reponse = await client.post("/api/config/export")
    assert reponse.status_code == 200
    assert temoin not in reponse.text
    assert reponse.json()["preferences"][0]["value"] == "[REDACTED]"
