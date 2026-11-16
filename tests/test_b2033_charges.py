"""Rejeu des scénarios de banc avec des délais contrôlés."""

import asyncio
from types import SimpleNamespace

import pytest
from app.services.action_agents import ActionRunner
from app.services.traitements import TraitementHandle

from tests.test_actions_traitement import TestLeRunEstUnTraitement as VerificationAction


@pytest.mark.asyncio
@pytest.mark.parametrize("nombre", [1, 2], ids=["producteur-bloque", "nombre-inattendu"])
async def test_scenario_action_borne_et_nettoie_ses_producteurs(monkeypatch, nombre):
    producteurs = set()

    async def producteur_bloque():
        await asyncio.Event().wait()

    async def run_factice(_agent_id):
        for _ in range(nombre):
            producteur = asyncio.create_task(producteur_bloque())
            producteurs.add(producteur)
            ActionRunner._taches_de_fond.add(producteur)
            producteur.add_done_callback(ActionRunner._taches_de_fond.discard)
        return SimpleNamespace(task_id="action-factice")

    monkeypatch.setattr(ActionRunner, "run", run_factice)
    scenario = asyncio.create_task(
        VerificationAction().test_nominal_running_pendant_done_apres(None, monkeypatch)
    )
    try:
        terminees, _ = await asyncio.wait({scenario}, timeout=6)
        assert scenario in terminees, "le scénario n'a pas borné l'attente du producteur"
        with pytest.raises(TimeoutError if nombre == 1 else AssertionError):
            await scenario
        assert len(producteurs) == nombre
        assert all(tache.done() for tache in producteurs), "des producteurs du scénario restent actifs"
        assert all(tache.cancelled() for tache in producteurs)
        assert not (producteurs & ActionRunner._taches_de_fond)
    finally:
        scenario.cancel()
        for producteur in producteurs:
            producteur.cancel()
        await asyncio.gather(scenario, *producteurs, return_exceptions=True)
        ActionRunner._taches_de_fond.difference_update(producteurs)


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
