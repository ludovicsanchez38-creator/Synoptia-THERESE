"""Une ligne non vide écartée doit apparaître dans le bilan CRM."""

import pytest
from app.services import crm_sync, sheets_service


@pytest.mark.asyncio
async def test_ligne_sans_identifiant_signalee_en_import_et_synchronisation(client, monkeypatch):
    class FeuilleFictive:
        def __init__(self, **_kwargs):
            pass

        async def get_all_data_as_dicts(self, _identifiant, onglet):
            return [{"Nom": "Dossier sans identifiant"}] if onglet == "Clients" else []

    async def autorisation_fictive(_session):
        return "simulation-locale"

    monkeypatch.setattr(sheets_service, "GoogleSheetsService", FeuilleFictive)
    monkeypatch.setattr(crm_sync, "ensure_valid_crm_token", autorisation_fictive)
    config = await client.post("/api/crm/sync/config", json={"spreadsheet_id": "feuille-fictive"})
    assert config.status_code == 200

    direct = await client.post(
        "/api/crm/sync/import", json={"clients": [{"Nom": "Dossier sans identifiant"}]}
    )
    synchro = await client.post("/api/crm/sync")
    assert direct.status_code == synchro.status_code == 200
    bilans = [direct.json(), synchro.json()]
    assert [bilan["success"] for bilan in bilans] == [False, False]
    assert all(bilan["stats"]["errors"] for bilan in bilans)


@pytest.mark.asyncio
async def test_import_signale_chaque_type_de_ligne_non_vide_invalide(client):
    reponse = await client.post("/api/crm/sync/import", json={
        "clients": [{"ID": "client-valide", "Nom": "Client"}, {"Nom": "Sans identifiant"}, {}],
        "projects": [{"Name": "Projet sans identifiant"}],
        "deliverables": [{"Title": "Livrable sans identifiant"}],
        "tasks": [{"Title": "Tâche sans identifiant"}],
    })
    assert reponse.status_code == 200
    bilan = reponse.json()
    assert bilan["success"] is False
    assert bilan["stats"]["contacts_created"] == 1
    assert len(bilan["stats"]["errors"]) == 4
    assert "incomplet" in bilan["message"].lower()
