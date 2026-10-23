import pytest
from app.services.crm_import import CRMImportService


@pytest.mark.asyncio
async def test_apercu_vide_accentue():
    apercu = await CRMImportService(None).preview_contacts(b'', 'vide.csv')
    assert apercu.validation_errors[0].message == 'Aucune donnée trouvée'
