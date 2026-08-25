"""Phase 1 du chantier 0.47 - ActionRunner : corriger le mensonge, enrôler.

Contrats (design V2.1) :
- `cancel_task` ne pose plus JAMAIS l'état terminal : il appelle la
  primitive unique `demander_arret_action` (évènement + CANCEL_REQUESTED
  observable, sans completed_at) ; seule la boucle constate et pose
  CANCELLED ;
- un run est un ProcessingTask type `action` : running pendant, progression
  par étapes, mapping COMPLETED→done / ERROR→failed / CANCELLED→cancelled ;
- l'enveloppe terminale couvre TOUT `_execute` (contexte local compris) :
  plus aucun chemin ne laisse TaskState ET ProcessingTask running ;
- annulée avant le démarrage de `_execute` : RUNNING n'est jamais réécrit.
"""

import asyncio

import pytest
from app.models.processing import EtatTache, ProcessingTask
from app.services.action_agents import ActionRunner, TaskStatus
from sqlmodel import select


async def _traitement_action(task_id: str) -> ProcessingTask | None:
    from app.models.database import get_session_context

    async with get_session_context() as session:
        resultat = await session.execute(
            select(ProcessingTask).where(
                ProcessingTask.type == "action",
                ProcessingTask.entity_id == task_id,
            )
        )
        return resultat.scalars().first()


def _faux_llm(morceaux=("étape faite",), lent: asyncio.Event | None = None):
    class FauxLLM:
        config = type(
            "C", (),
            {"provider": type("P", (), {"value": "ollama"})(), "model": "test"},
        )()

        def prepare_context(self, messages, system_prompt=None, memory_context=None):
            return type("Ctx", (), {"messages": messages})()

        async def stream_response(self, _context, raise_on_error=False):
            if lent is not None:
                await lent.wait()
            for morceau in morceaux:
                yield morceau

    return FauxLLM()


async def _attendre(condition, timeout=5.0):
    for _ in range(int(timeout / 0.05)):
        if condition():
            return True
        await asyncio.sleep(0.05)
    return False


class TestLeMensongeEstCorrige:
    @pytest.mark.asyncio
    async def test_cancel_task_ne_pose_plus_l_etat_terminal(
        self, client, monkeypatch
    ):
        from app.services import action_agents as module

        verrou = asyncio.Event()
        monkeypatch.setattr(
            module, "get_llm_service", lambda: _faux_llm(lent=verrou),
            raising=False,
        )
        monkeypatch.setattr(
            "app.services.llm.get_llm_service", lambda: _faux_llm(lent=verrou),
        )

        task = await ActionRunner.run("rapport-hebdo")
        assert await _attendre(
            lambda: ActionRunner.get_task(task.task_id).status == TaskStatus.RUNNING
        )

        assert ActionRunner.cancel_task(task.task_id) is True
        etat = ActionRunner.get_task(task.task_id)
        assert etat.status == TaskStatus.CANCEL_REQUESTED, (
            "l'arrêt est DEMANDÉ - le flux LLM de l'étape tourne encore, "
            "annoncer cancelled maintenant est le mensonge historique"
        )
        assert etat.completed_at is None

        verrou.set()  # l'étape en cours se termine, la boucle constate
        assert await _attendre(
            lambda: ActionRunner.get_task(task.task_id).status == TaskStatus.CANCELLED
        )
        assert ActionRunner.get_task(task.task_id).completed_at is not None


class TestLeRunEstUnTraitement:
    @pytest.mark.asyncio
    async def test_nominal_running_pendant_done_apres(self, client, monkeypatch):
        monkeypatch.setattr(
            "app.services.llm.get_llm_service", lambda: _faux_llm(),
        )

        task = await ActionRunner.run("rapport-hebdo")
        assert await _attendre(
            lambda: ActionRunner.get_task(task.task_id).status
            == TaskStatus.COMPLETED
        )

        traitement = await _traitement_action(task.task_id)
        assert traitement is not None
        assert traitement.state == EtatTache.DONE
        assert traitement.progress == 1.0

    @pytest.mark.asyncio
    async def test_l_annulation_par_le_panneau_converge(self, client, monkeypatch):
        """demander_arret sur le ProcessingTask coupe entre deux étapes et
        les DEUX cycles de vie finissent cancelled."""
        from app.services import traitements

        verrou = asyncio.Event()
        monkeypatch.setattr(
            "app.services.llm.get_llm_service", lambda: _faux_llm(lent=verrou),
        )

        task = await ActionRunner.run("rapport-hebdo")
        assert await _attendre(
            lambda: ActionRunner.get_task(task.task_id).status == TaskStatus.RUNNING
        )
        traitement = await _traitement_action(task.task_id)
        assert traitement is not None

        await traitements.demander_arret(traitement.id)
        etat = ActionRunner.get_task(task.task_id)
        assert etat.status == TaskStatus.CANCEL_REQUESTED, (
            "l'adaptateur canonique doit passer par la primitive unique - "
            "sinon le panneau Actions reste running"
        )

        verrou.set()
        assert await _attendre(
            lambda: ActionRunner.get_task(task.task_id).status == TaskStatus.CANCELLED
        )
        # relire jusqu'a l'etat terminal (la boucle termine en tache de fond)
        traitement_final = None
        for _ in range(50):
            traitement_final = await _traitement_action(task.task_id)
            if traitement_final.state == EtatTache.CANCELLED:
                break
            await asyncio.sleep(0.05)
        assert traitement_final.state == EtatTache.CANCELLED

    @pytest.mark.asyncio
    async def test_une_panne_du_contexte_local_ne_laisse_rien_running(
        self, client, monkeypatch
    ):
        """Enveloppe terminale TOTALE : _gather_local_context hors try
        laissait TaskState et ProcessingTask running pour toujours."""
        from app.services import action_agents as module

        async def contexte_en_panne(_tools):
            raise RuntimeError("contexte local en panne")

        monkeypatch.setattr(module, "_gather_local_context", contexte_en_panne)
        monkeypatch.setattr(
            "app.services.llm.get_llm_service", lambda: _faux_llm(),
        )

        task = await ActionRunner.run("rapport-hebdo")
        assert await _attendre(
            lambda: ActionRunner.get_task(task.task_id).status == TaskStatus.ERROR
        )
        # Revue 0.48 (F4) : l'erreur consignée est LISIBLE, jamais le brut -
        # « contexte local en panne » vit dans les logs, pas à l'écran.
        erreur = ActionRunner.get_task(task.task_id).error or ""
        assert erreur, "une erreur lisible doit être consignée"
        assert "contexte local en panne" not in erreur

        for _ in range(50):
            traitement = await _traitement_action(task.task_id)
            if traitement and traitement.state == EtatTache.FAILED:
                break
            await asyncio.sleep(0.05)
        assert traitement is not None
        assert traitement.state == EtatTache.FAILED

    @pytest.mark.asyncio
    async def test_annulee_avant_execute_ne_reecrit_pas_running(
        self, client, monkeypatch
    ):
        """La course : cancel_task gagne avant le démarrage de _execute -
        RUNNING ne doit jamais réapparaître, aucune étape ne tourne."""
        from app.services import action_agents as module

        etapes_lancees = {"n": 0}

        class LLMSentinelle:
            config = type(
                "C", (),
                {"provider": type("P", (), {"value": "ollama"})(), "model": "t"},
            )()

            def prepare_context(self, messages, **_k):
                return type("Ctx", (), {"messages": messages})()

            async def stream_response(self, _context, raise_on_error=False):
                etapes_lancees["n"] += 1
                yield "jamais"

        monkeypatch.setattr(
            "app.services.llm.get_llm_service", lambda: LLMSentinelle(),
        )
        # bloquer le demarrage de _execute pour laisser la course se jouer
        vrai_execute = module.ActionRunner._execute
        pret = asyncio.Event()
        fini = asyncio.Event()

        async def execute_retarde(task, agent_def, params, on_progress):
            await pret.wait()
            try:
                await vrai_execute(task, agent_def, params, on_progress)
            finally:
                fini.set()

        monkeypatch.setattr(
            module.ActionRunner, "_execute", execute_retarde,
        )

        historique: list[TaskStatus] = []
        setattr_original = module.TaskState.__setattr__

        def traceur(self, nom, valeur):
            if nom == "status":
                historique.append(valeur)
            setattr_original(self, nom, valeur)

        monkeypatch.setattr(module.TaskState, "__setattr__", traceur)

        task = await ActionRunner.run("rapport-hebdo")
        ActionRunner.cancel_task(task.task_id)
        pret.set()
        await asyncio.wait_for(fini.wait(), timeout=5)

        assert (
            ActionRunner.get_task(task.task_id).status == TaskStatus.CANCELLED
        )
        assert etapes_lancees["n"] == 0, (
            "aucune étape ne doit tourner pour une action annulée avant "
            "son démarrage"
        )
        assert TaskStatus.RUNNING not in historique, (
            "l'annulation a gagné la course : _execute ne doit pas "
            "réécrire RUNNING par-dessus"
        )


class TestLaRouteHistoriqueEstCanonique:
    @pytest.mark.asyncio
    async def test_delete_passe_par_le_traitement_durable(
        self, client, monkeypatch
    ):
        """DELETE /api/actions/tasks/{id} doit emprunter le chemin canonique :
        la transition cancel_requested est posée sur le ProcessingTask, qui la
        relaie à la primitive - un seul chemin d'annulation."""
        verrou = asyncio.Event()
        monkeypatch.setattr(
            "app.services.llm.get_llm_service", lambda: _faux_llm(lent=verrou),
        )

        task = await ActionRunner.run("rapport-hebdo")
        assert await _attendre(
            lambda: ActionRunner.get_task(task.task_id).status == TaskStatus.RUNNING
        )
        assert (await _traitement_action(task.task_id)) is not None

        reponse = await client.delete(f"/api/actions/tasks/{task.task_id}")
        assert reponse.status_code == 200

        relu = await _traitement_action(task.task_id)
        assert relu.state == EtatTache.CANCEL_REQUESTED, (
            "la route historique doit passer par le service canonique - "
            "un cancel purement en mémoire laisse le panneau Traitements "
            "afficher running"
        )
        assert (
            ActionRunner.get_task(task.task_id).status
            == TaskStatus.CANCEL_REQUESTED
        )

        verrou.set()
        assert await _attendre(
            lambda: ActionRunner.get_task(task.task_id).status == TaskStatus.CANCELLED
        )
        for _ in range(50):
            final = await _traitement_action(task.task_id)
            if final.state == EtatTache.CANCELLED:
                break
            await asyncio.sleep(0.05)
        assert final.state == EtatTache.CANCELLED

    @pytest.mark.asyncio
    async def test_delete_sans_traitement_replie_sur_la_primitive(
        self, client, monkeypatch
    ):
        """Suivi en panne (fail-open) : le DELETE doit quand même arrêter."""
        verrou = asyncio.Event()
        monkeypatch.setattr(
            "app.services.llm.get_llm_service", lambda: _faux_llm(lent=verrou),
        )

        async def suivi_en_panne(**_k):
            raise RuntimeError("table indisponible")

        from app.services import action_agents as module

        monkeypatch.setattr(
            module.traitements_service, "creer_traitement", suivi_en_panne
        )

        task = await ActionRunner.run("rapport-hebdo")
        assert await _attendre(
            lambda: ActionRunner.get_task(task.task_id).status == TaskStatus.RUNNING
        )
        assert (await _traitement_action(task.task_id)) is None

        reponse = await client.delete(f"/api/actions/tasks/{task.task_id}")
        assert reponse.status_code == 200
        assert (
            ActionRunner.get_task(task.task_id).status
            == TaskStatus.CANCEL_REQUESTED
        )

        verrou.set()
        assert await _attendre(
            lambda: ActionRunner.get_task(task.task_id).status == TaskStatus.CANCELLED
        )


class TestLaFenetreDEnrolement:
    @pytest.mark.asyncio
    async def test_f9_delete_pendant_l_enrolement_est_accepte(
        self, client, monkeypatch
    ):
        """F9 : entre demarrer() et lier_adaptateur(), demander_arret rend
        « unavailable » mais RETIENT la demande (rejouée à l'enrôlement).
        La route répondait 400 alors que l'arrêt allait réellement avoir
        lieu."""
        from app.services import traitements

        monkeypatch.setattr(
            "app.services.llm.get_llm_service", lambda: _faux_llm(),
        )

        porte = asyncio.Event()
        lier_originale = traitements.TraitementHandle.lier_adaptateur

        async def lier_retardee(self, adaptateur):
            await porte.wait()
            await lier_originale(self, adaptateur)

        monkeypatch.setattr(
            traitements.TraitementHandle, "lier_adaptateur", lier_retardee
        )

        task = await ActionRunner.run("rapport-hebdo")

        # attendre la fenêtre : traitement RUNNING, adaptateur pas encore là
        traitement = None
        for _ in range(100):
            traitement = await _traitement_action(task.task_id)
            if traitement is not None and traitement.state == EtatTache.RUNNING:
                break
            await asyncio.sleep(0.05)
        assert traitement is not None and traitement.state == EtatTache.RUNNING

        reponse = await client.delete(f"/api/actions/tasks/{task.task_id}")
        assert reponse.status_code == 200, (
            "la demande est posée durablement et sera rejouée à "
            "l'enrôlement : la refuser en 400 est un mensonge"
        )
        # Passe 2 de revue : la demande doit être DURABLE (pas seulement en
        # mémoire) - c'est elle que lier_adaptateur rejouera.
        relu = await _traitement_action(task.task_id)
        assert relu.state == EtatTache.CANCEL_REQUESTED

        porte.set()
        assert await _attendre(
            lambda: ActionRunner.get_task(task.task_id).status
            == TaskStatus.CANCELLED
        )
        etapes_executees = [
            s for s in ActionRunner.get_task(task.task_id).steps
            if s.status.value == "completed"
        ]
        assert etapes_executees == [], (
            "des étapes ont tourné alors que l'arrêt était demandé avant "
            "l'enrôlement"
        )
