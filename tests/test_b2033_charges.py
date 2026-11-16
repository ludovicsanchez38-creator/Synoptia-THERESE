"""Rejeu des scénarios de banc avec des délais contrôlés."""

import asyncio

import pytest
from app.services.action_agents import ActionRunner
from app.services.traitements import TraitementHandle

from tests.test_actions_traitement import TestLeRunEstUnTraitement as VerificationAction


@pytest.mark.asyncio
async def test_scenario_action_attend_le_commit_durable(client, monkeypatch):
    terminer = TraitementHandle.terminer

    async def terminer_plus_lentement(self, etat, *, error=None):
        await asyncio.sleep(0.3)
        await terminer(self, etat, error=error)

    monkeypatch.setattr(TraitementHandle, "terminer", terminer_plus_lentement)
    avant = set(ActionRunner._taches_de_fond)
    try:
        await VerificationAction().test_nominal_running_pendant_done_apres(
            client, monkeypatch
        )
    finally:
        restantes = set(ActionRunner._taches_de_fond) - avant
        if restantes:
            await asyncio.wait_for(asyncio.gather(*restantes), timeout=10)
