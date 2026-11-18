"""Rejeu des scénarios de banc avec des délais contrôlés."""

import asyncio
import inspect
from types import SimpleNamespace

import pytest
from app.services.action_agents import ActionRunner, TaskState, TaskStatus
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
@pytest.mark.parametrize(
    "instant",
    ["pendant-commit", "avant-cloture", "annulation-retardee", "fermeture-protegee"],
)
async def test_scenario_action_nettoie_la_cloture_protegee(monkeypatch, instant):
    """Rejouer le vrai finally de _execute et le shield de terminer."""
    verrou = asyncio.Event()
    entree = asyncio.Event()
    verrou_autre = asyncio.Event()
    entree_autre = asyncio.Event()
    ecritures = []
    fermetures = []
    producteurs = set()

    async def fermeture_retenue():
        await verrou.wait()

    async def ecriture_retenue():
        try:
            await verrou.wait()
        except asyncio.CancelledError:
            if instant == "annulation-retardee":
                await verrou.wait()
            raise
        finally:
            if instant == "fermeture-protegee":
                # Comme get_session_context : la fermeture a aussi son shield.
                fermeture = fermeture_retenue()
                fermetures.append(fermeture)
                await asyncio.shield(fermeture)
            else:
                # Le scénario doit aussi attendre le nettoyage de l'écriture.
                await asyncio.sleep(0.05)

    async def autre_ecriture():
        entree_autre.set()
        await verrou_autre.wait()

    def ecrire_retenu(self, etat, *, error):
        if self.id == "autre-traitement":
            return autre_ecriture()
        coroutine = ecriture_retenue()
        ecritures.append(coroutine)
        if instant != "avant-cloture":
            entree.set()
        return coroutine

    async def derouler_retenu(cls, task, agent_def, params, on_progress):
        if instant == "avant-cloture":
            entree.set()
            await verrou.wait()
        task.status = TaskStatus.COMPLETED

    async def run_factice(_agent_id):
        task = TaskState("action-factice", "agent", "Agent")
        task._handle = TraitementHandle("traitement-factice")
        producteur = asyncio.create_task(
            ActionRunner._execute(task, SimpleNamespace(id="agent"), {}, None)
        )
        producteurs.add(producteur)
        ActionRunner._taches_de_fond.add(producteur)
        producteur.add_done_callback(ActionRunner._taches_de_fond.discard)
        return task

    monkeypatch.setattr(TraitementHandle, "_ecrire_etat_terminal", ecrire_retenu)
    monkeypatch.setattr(ActionRunner, "_derouler", classmethod(derouler_retenu))
    monkeypatch.setattr(ActionRunner, "run", run_factice)
    autre = asyncio.create_task(TraitementHandle("autre-traitement").terminer("done"))
    scenario = asyncio.create_task(
        VerificationAction().test_nominal_running_pendant_done_apres(None, monkeypatch)
    )
    try:
        await asyncio.wait_for(entree_autre.wait(), timeout=2)
        await asyncio.wait_for(entree.wait(), timeout=2)
        delai = 12 if instant in {"annulation-retardee", "fermeture-protegee"} else 6
        terminees, _ = await asyncio.wait({scenario}, timeout=delai)
        assert scenario in terminees, "le scénario reste suspendu pendant la clôture"
        assert all(tache.done() for tache in producteurs), "un producteur reste actif"
        assert len(ecritures) == 1, "la clôture du scénario n'a pas été lancée"
        assert all(
            inspect.getcoroutinestate(ecriture) == inspect.CORO_CLOSED
            for ecriture in ecritures
        ), "une écriture de clôture reste active"
        if instant == "fermeture-protegee":
            assert len(fermetures) == 1, "la fermeture protégée n'a pas été lancée"
            assert all(
                inspect.getcoroutinestate(fermeture) == inspect.CORO_CLOSED
                for fermeture in fermetures
            ), "une fermeture protégée reste active"
        assert not autre.done(), "une clôture extérieure au scénario a été arrêtée"
        with pytest.raises(TimeoutError):
            await scenario
    finally:
        verrou.set()
        verrou_autre.set()
        scenario.cancel()
        for producteur in producteurs:
            producteur.cancel()
        await asyncio.gather(scenario, autre, *producteurs, return_exceptions=True)
        restantes = [
            tache for tache in asyncio.all_tasks()
            if tache.get_coro() in ecritures + fermetures
        ]
        await asyncio.gather(*restantes, return_exceptions=True)
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
