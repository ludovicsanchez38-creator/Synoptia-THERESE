"""
J1a (31/07/2026) - Socle des traitements longs, couche durable.

Le testeur a dû fermer THÉRÈSE pour interrompre une indexation : rien ne
montrait ce qui tournait, rien ne permettait de l'arrêter. La 0.41.3 a supprimé
le gel, pas l'impuissance.

Invariants exigés par la revue du plan (Soso, NO-GO V1) :

- `cancel_requested` n'est PAS `cancelled`. La sémantique actuelle d'ActionRunner
  (`action_agents.py:411` marque CANCELLED alors que le flux LLM continue) ne
  doit surtout pas être généralisée : l'utilisateur croirait un traitement
  arrêté alors qu'il consomme encore.
- Une tâche restée en cours après un arrêt du processus doit devenir
  `interrupted` au démarrage suivant. Aujourd'hui une AgentTask restée
  `in_progress` bloque toute nouvelle mission (`agents.py:199`) et n'est même
  plus annulable (409, `agents.py:546`).
- La reprise n'est proposée que pour un type explicitement idempotent.
"""
import pytest


class TestModeleDeTache:
    def test_les_etats_distinguent_la_demande_de_l_arret_effectif(self):
        from app.models.processing import EtatTache

        assert EtatTache.CANCEL_REQUESTED != EtatTache.CANCELLED
        # Un état terminal ne doit jamais être posé tant que le travail tourne.
        assert EtatTache.CANCELLED in EtatTache.terminaux()
        assert EtatTache.CANCEL_REQUESTED not in EtatTache.terminaux()
        assert EtatTache.INTERRUPTED in EtatTache.terminaux()

    def test_la_tache_porte_son_instance_d_execution(self):
        """`run_instance_id` distingue les tâches de CETTE exécution du sidecar."""
        from app.models.processing import ProcessingTask

        tache = ProcessingTask(type="indexation", label="rapport.pdf", run_instance_id="abc")
        assert tache.state == "queued"
        assert tache.run_instance_id == "abc"
        assert tache.resumable is False
        assert tache.progress is None

    # NOTE (31/07/2026) - raccordement au démarrage NON couvert automatiquement.
    #
    # Le finding 5 de la revue Soso était juste : la reprise n'était appelée
    # que par les tests. Elle est désormais branchée dans le `lifespan`
    # (`main.py`, juste après les migrations ad hoc).
    #
    # Un test exécutant le vrai `lifespan` a été écrit, puis RETIRÉ : la sortie
    # du lifespan appelle `close_db()`, qui DISPOSE les moteurs partagés. Ni la
    # restauration des attributs de module ni un `init_db()` ne rendent à la
    # suite l'environnement monté par le conftest — mesuré : 329 échecs en
    # suite complète, 25 même sur trois fichiers. Le coût dépassait le gain.
    #
    # Ce qui reste vérifié : la requête de reprise elle-même (tests ci-dessous).
    # Ce qui ne l'est pas : que le lifespan l'appelle toujours. Un test
    # d'application packagée le couvrirait mieux qu'un test unitaire.

    @pytest.mark.asyncio
    async def test_une_tache_orpheline_devient_interrompue_au_demarrage(self, db_session):
        """Un arrêt brutal ne doit pas laisser une tâche éternellement en cours."""
        from app.models.processing import EtatTache, ProcessingTask
        from app.services.task_registry import instance_courante, recuperer_taches_orphelines
        from sqlmodel import select

        ancienne = ProcessingTask(
            type="indexation",
            label="gros.pdf",
            state=EtatTache.RUNNING,
            run_instance_id="instance-precedente",
        )
        db_session.add(ancienne)
        await db_session.commit()

        nombre = await recuperer_taches_orphelines(db_session)

        assert nombre == 1
        relue = (
            await db_session.execute(select(ProcessingTask).where(ProcessingTask.id == ancienne.id))
        ).scalar_one()
        assert relue.state == EtatTache.INTERRUPTED
        assert relue.finished_at is not None
        assert instance_courante() != "instance-precedente"

    @pytest.mark.asyncio
    async def test_une_tache_de_l_instance_courante_est_epargnee(self, db_session):
        from app.models.processing import EtatTache, ProcessingTask
        from app.services.task_registry import instance_courante, recuperer_taches_orphelines
        from sqlmodel import select

        vivante = ProcessingTask(
            type="board",
            label="Délibération",
            state=EtatTache.RUNNING,
            run_instance_id=instance_courante(),
        )
        db_session.add(vivante)
        await db_session.commit()

        await recuperer_taches_orphelines(db_session)

        relue = (
            await db_session.execute(select(ProcessingTask).where(ProcessingTask.id == vivante.id))
        ).scalar_one()
        assert relue.state == EtatTache.RUNNING, (
            "une tâche de l'instance courante tourne toujours : la marquer interrompue "
            "afficherait un faux arrêt"
        )


class TestRegistreRuntime:
    @pytest.mark.asyncio
    async def test_l_adaptateur_asyncio_n_annonce_pas_un_arret_non_obtenu(self):
        """Finding MAJEUR n°6 : `cancel()` demande, il ne garantit pas.

        `Task.cancel()` pose une demande ; une coroutine peut différer son
        arrêt, ou absorber `CancelledError` et continuer. Retourner `True` sans
        attendre revient à annoncer `cancelled` alors que le travail tourne
        encore — exactement la confusion que la distinction
        `cancel_requested` / `cancelled` est censée empêcher.
        """
        import asyncio

        from app.services.task_registry import AnnulationParTacheAsyncio

        travail_termine = asyncio.Event()
        demarre = asyncio.Event()

        async def absorbe_l_annulation():
            demarre.set()
            try:
                await asyncio.sleep(30)
            except asyncio.CancelledError:
                # Un traitement qui prend le temps de se refermer proprement.
                await asyncio.sleep(0.05)
                travail_termine.set()

        tache = asyncio.create_task(absorbe_l_annulation())
        await asyncio.wait_for(demarre.wait(), timeout=2)

        obtenu = await AnnulationParTacheAsyncio(tache).annuler()

        assert obtenu is False or travail_termine.is_set(), (
            "l'adaptateur annonce un arrêt effectif alors que le traitement "
            "tourne encore : l'interface afficherait « annulé » à tort"
        )

    @pytest.mark.asyncio
    async def test_une_tache_terminee_ne_reste_pas_dans_le_registre(self):
        """Finding MINEUR n°8 : rien ne retirait l'entrée à la fin du travail.

        Sans nettoyage, `est_vivante` reste vrai pour toujours et une annulation
        portant le même identifiant croit avoir trouvé un traitement à couper.
        """
        import asyncio

        from app.services.task_registry import (
            AnnulationParTacheAsyncio,
            est_vivante,
            inscrire,
        )

        async def travail_bref():
            return "fini"

        tache = asyncio.create_task(travail_bref())
        inscrire("tache-breve", AnnulationParTacheAsyncio(tache))
        await tache
        # Laisser tourner les rappels de fin de tâche.
        await asyncio.sleep(0)

        assert not est_vivante("tache-breve"), (
            "l'entrée survit au traitement : le registre fuit et les annulations "
            "suivantes portant cet identifiant croient avoir quelque chose à couper"
        )
