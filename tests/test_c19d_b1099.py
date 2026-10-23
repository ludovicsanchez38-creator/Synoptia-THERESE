import pytest
from app.services.slash_commands import execute_slash_command


@pytest.mark.asyncio
async def test_statut_retenu_en_francais(db_session):
    reponse = await execute_slash_command('projet', 'Chantier c19 statut=gelé', db_session)
    assert 'gelé' in reponse and 'actif' in reponse
    assert '« active »' not in reponse
