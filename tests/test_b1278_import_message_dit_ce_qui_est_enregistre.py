"""B-1278 : B-1256 et B-1262 signalent au rapport une cellule écartée (budget,
étape) sur une ligne pourtant enregistrée. Le message disait alors
« Import avec erreurs: 1 erreurs sur N lignes », sans dire que les lignes
étaient enregistrées. Revue du diff, passe 5."""

import pytest
from app.services.crm_import import CRMImportService


@pytest.mark.asyncio
async def test_le_message_compte_les_lignes_enregistrees(db_session):
    res = await CRMImportService(db_session).import_contacts(
        "id,first_name,last_name,stage\nc-1,Marie,Exemple,gelé\nc-2,Jean,Exemple,contact\n".encode(),
        filename="c.csv",
    )
    assert res.created == 2, res
    assert res.errors, "la cellule d'étape écartée doit rester au rapport"
    assert "2 créés" in res.message, res.message
    assert "Import avec erreurs" not in res.message, res.message


@pytest.mark.asyncio
async def test_le_message_sans_signalement(db_session):
    res = await CRMImportService(db_session).import_contacts(
        "id,first_name,last_name\nc-3,Léa,Exemple\n".encode(), filename="c.csv"
    )
    assert res.message == "Import terminé : 1 créés, 0 mis à jour, 0 ignorés", res.message
