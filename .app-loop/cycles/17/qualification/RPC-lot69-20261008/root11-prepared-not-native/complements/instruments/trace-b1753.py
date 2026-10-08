"""Traces et ordonnancement de reproduction, sans modifier le produit."""
import asyncio
import importlib.util
import json
import os
from pathlib import Path
import threading
import time

import pytest

REPO = Path(os.environ['ENQUETE_REPO'])
TRACE = Path(os.environ['ENQUETE_TRACE'])
spec = importlib.util.spec_from_file_location('garde_enquete', REPO / 'tests/couverture/backend_offline.py')
garde = importlib.util.module_from_spec(spec)
spec.loader.exec_module(garde)
garde.installer_garde_socket()


def tracer(evenement, **valeurs):
    ligne = {'instant': time.monotonic(), 'thread': threading.get_ident(), 'evenement': evenement, **valeurs}
    with TRACE.open('a') as fichier:
        fichier.write(json.dumps(ligne, ensure_ascii=False, default=str) + '\n')


@pytest.fixture(autouse=True)
def observer_action(request, monkeypatch):
    from app.models import database
    from app.services import action_agents, task_registry, traitements

    tracer('debut_test', test=request.node.nodeid, registre=task_registry.vivantes(), db_initialisee=database.AsyncSessionLocal is not None)
    controle = os.environ.get('ENQUETE_MODE') == 'controle' and request.node.name == 'test_delete_passe_par_le_traitement_durable'
    contexte_libere = asyncio.Event()
    cloture_liberee = asyncio.Event()
    annulation_constatee = threading.Event()
    flux_commence = threading.Event()
    boucle_producteur = {'boucle': None}
    setattr_original = action_agents.TaskState.__setattr__

    def assigner(self, nom, valeur):
        setattr_original(self, nom, valeur)
        if nom == 'status':
            tracer('statut_action', task=getattr(self, 'task_id', None), statut=valeur)
            if valeur == action_agents.TaskStatus.CANCELLED:
                annulation_constatee.set()

    monkeypatch.setattr(action_agents.TaskState, '__setattr__', assigner)
    contexte_original = action_agents._gather_local_context

    async def contexte(*args, **kwargs):
        boucle_producteur['boucle'] = asyncio.get_running_loop()
        tracer('contexte_entree')
        if controle:
            await contexte_libere.wait()
        resultat = await contexte_original(*args, **kwargs)
        tracer('contexte_sortie')
        return resultat

    monkeypatch.setattr(action_agents, '_gather_local_context', contexte)
    terminal_original = traitements.TraitementHandle._ecrire_etat_terminal

    async def terminal(self, etat, **kwargs):
        tracer('terminal_entree', traitement=self.id, etat=etat, registre=task_registry.vivantes())
        if controle:
            await cloture_liberee.wait()
        resultat = await terminal_original(self, etat, **kwargs)
        tracer('terminal_sortie', traitement=self.id, registre=task_registry.vivantes())
        return resultat

    monkeypatch.setattr(traitements.TraitementHandle, '_ecrire_etat_terminal', terminal)
    arret_original = traitements.demander_arret

    async def arret(identifiant):
        tracer('demande_arret_entree', traitement=identifiant)
        resultat = await arret_original(identifiant)
        tracer('demande_arret_sortie', traitement=identifiant, resultat=resultat)
        if controle and not flux_commence.is_set():
            boucle_producteur['boucle'].call_soon_threadsafe(contexte_libere.set)
            assert await asyncio.to_thread(annulation_constatee.wait, 3), 'La boucle doit constater la demande avant toute étape'
        return resultat

    monkeypatch.setattr(traitements, 'demander_arret', arret)
    if hasattr(request.node.module, '_faux_llm'):
        faux_original = request.node.module._faux_llm

        def faux(*args, **kwargs):
            llm = faux_original(*args, **kwargs)
            flux_original = llm.stream_response

            async def flux(*a, **k):
                flux_commence.set()
                tracer('flux_llm_entree', verrou_libere=kwargs.get('lent').is_set() if kwargs.get('lent') else None)
                async for morceau in flux_original(*a, **k):
                    yield morceau
                tracer('flux_llm_sortie')

            llm.stream_response = flux
            return llm

        monkeypatch.setattr(request.node.module, '_faux_llm', faux)
    # Observer les synchronisations du nouveau témoin pour libérer les
    # barrières de l'enquête. Aucun état du produit ni assertion n'est changé.
    if controle and hasattr(request.node.module, '_attendre_entree_flux'):
        attendre_original = request.node.module._attendre_entree_flux
        clore_original = request.node.module._clore_action_temoin

        async def attendre_flux(entree):
            tracer('temoin_attend_flux')
            contexte_libere.set()
            await attendre_original(entree)

        async def clore_temoin(*args, **kwargs):
            tracer('temoin_cleanup')
            cloture_liberee.set()
            return await clore_original(*args, **kwargs)

        monkeypatch.setattr(request.node.module, '_attendre_entree_flux', attendre_flux)
        monkeypatch.setattr(request.node.module, '_clore_action_temoin', clore_temoin)
    yield
    tracer('fin_test', test=request.node.nodeid, registre=task_registry.vivantes(), db_initialisee=database.AsyncSessionLocal is not None,
           actions={i: t.status for i, t in action_agents.ActionRunner._tasks.items()},
           fonds=[{'terminee': t.done(), 'annulee': t.cancelled()} for t in action_agents.ActionRunner._taches_de_fond])
