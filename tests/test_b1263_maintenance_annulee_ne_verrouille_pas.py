"""B-1263 : `begin()` pose le verrou de maintenance PUIS attend la fin des
requêtes déjà admises (une réponse de chat en flux peut durer). Annulée
pendant cette attente (déconnexion, arrêt), la restauration laissait le
verrou actif : toute l'API répondait « mode maintenance » jusqu'au
redémarrage. L'appelant ne peut pas le rattraper, begin() étant hors du
try dont le finally appelle end()."""

import asyncio

import pytest
from app.services.maintenance import MaintenanceMode, RequestAdmission


@pytest.mark.asyncio
async def test_begin_annule_pendant_l_attente_rend_la_main():
    mode = MaintenanceMode()
    admission = mode.admit("POST", "/api/chat/send")
    assert admission is RequestAdmission.TRACKED

    attente = asyncio.create_task(mode.begin())
    await asyncio.sleep(0.05)
    assert mode.active is True
    attente.cancel()
    with pytest.raises(asyncio.CancelledError):
        await attente

    assert mode.active is False, "verrou de maintenance laissé actif après l'annulation"
    mode.release(admission)
    assert mode.admit("GET", "/api/memory/contacts") is RequestAdmission.TRACKED


@pytest.mark.asyncio
async def test_begin_sans_annulation_garde_le_verrou():
    mode = MaintenanceMode()
    await mode.begin()
    assert mode.active is True
    assert mode.admit("GET", "/api/memory/contacts") is RequestAdmission.REJECTED
    mode.end()
