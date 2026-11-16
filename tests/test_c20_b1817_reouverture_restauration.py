"""Une restauration n'annonce pas le succès si la base ne rouvre pas."""

from unittest.mock import AsyncMock

import pytest
from app.models import database
from app.routers import data


@pytest.mark.asyncio
async def test_restauration_signale_la_reouverture_impossible(client, monkeypatch):
    phrase = "sauvegarde-fictive-pour-test"
    sauvegarde = await client.post("/api/data/backup", json={"password": phrase})
    assert sauvegarde.status_code == 200
    nom = sauvegarde.json()["backup_name"]
    appels = []
    initialiser = database.init_db

    async def reouverture_impossible():
        appels.append(True)
        # Simule un échec tardif : le moteur synchrone est ouvert mais le
        # moteur asynchrone, indispensable aux requêtes, ne l'est pas.
        await initialiser()
        await database.async_engine.dispose()
        database.async_engine = None
        database.AsyncSessionLocal = None
        raise OSError("panne simulée de réouverture")

    monkeypatch.setattr(database, "init_db", reouverture_impossible)
    reponse = await client.post(
        f"/api/data/restore/{nom}?confirm=true", json={"password": phrase}
    )
    assert appels, "le scénario doit atteindre la réouverture de la base"
    assert reponse.status_code >= 400 or reponse.json().get("success") is False


@pytest.mark.asyncio
async def test_restauration_refuse_une_initialisation_qui_echoue_apres_creation_des_moteurs(
    client, monkeypatch,
):
    phrase = "sauvegarde-fictive-pour-test"
    sauvegarde = await client.post("/api/data/backup", json={"password": phrase})
    assert sauvegarde.status_code == 200
    nom = sauvegarde.json()["backup_name"]
    initialiser = database.init_db

    async def initialisation_incomplete():
        await initialiser()
        raise OSError("panne fictive après création des moteurs")

    monkeypatch.setattr(database, "init_db", initialisation_incomplete)
    reponse = await client.post(
        f"/api/data/restore/{nom}?confirm=true", json={"password": phrase}
    )
    assert reponse.status_code >= 400 or reponse.json().get("success") is False


@pytest.mark.asyncio
async def test_reouverture_refuse_un_moteur_async_inutilisable(monkeypatch):
    session = AsyncMock()
    session.execute.side_effect = OSError("base fictive inaccessible")
    gestionnaire = AsyncMock()
    gestionnaire.__aenter__.return_value = session
    monkeypatch.setattr(database, "sync_engine", object())
    monkeypatch.setattr(database, "async_engine", object())
    monkeypatch.setattr(database, "AsyncSessionLocal", lambda: gestionnaire)

    assert await data._rouvrir_la_base_apres_restauration() is False
