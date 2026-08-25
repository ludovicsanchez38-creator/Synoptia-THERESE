"""Phase 3 du chantier 0.47 - Board : la délibération est un traitement.

Contrats (design V2.1) :
- `decision_id` préalloué par la route, handle type `board` créé avant le
  premier événement SSE, identifiant du traitement émis en premier ;
- adaptateur `AnnulationParTacheAsyncio` sur la tâche porteuse : annuler
  coupe la recherche web, les advisors (cloud ET souverain) et la synthèse ;
- fence avant le commit : une demande d'arrêt posée avant gagne (aucune
  décision à moitié voulue ne se sauve) ; APRÈS le commit, done gagne ;
- pas de partiel : annulation/déconnexion = cancelled, échec = failed ;
- matrice au niveau StreamingResponse, pas seulement sur le générateur.
"""

import asyncio
import json
from types import SimpleNamespace

import pytest
from app.models.processing import EtatTache, ProcessingTask
from sqlmodel import select

SYNTHESE = json.dumps({
    "consensus_points": ["Tester"],
    "divergence_points": [],
    "recommendation": "Lancer un pilote.",
    "confidence": "high",
    "next_steps": ["Cadrer"],
})

REQUETE = {
    "question": "Faut-il lancer ce pilote dès maintenant ?",
    "mode": "cloud",
    "advisors": ["analyst"],
}


class FauxLLM:
    def __init__(self, reponses, avant_flux=None):
        self.reponses = list(reponses)
        self.avant_flux = avant_flux
        from app.services.llm import LLMProvider

        self.config = SimpleNamespace(
            provider=LLMProvider.OPENAI, model="modele-test"
        )

    def prepare_context(self, messages, system_prompt=None):
        return messages, system_prompt

    async def stream_response(self, context, usage_sink=None):
        if self.avant_flux is not None:
            await self.avant_flux()
        yield self.reponses.pop(0)


async def _contexte_web_vide(*_a, **_k) -> str:
    return ""


@pytest.fixture
def board_rapide(monkeypatch):
    """Un board cloud à un conseiller, sans web ni vrai LLM."""
    from app.services import board as board_module
    from app.services.board import BoardService

    llm = FauxLLM(["Avis mesuré.", SYNTHESE])
    monkeypatch.setattr(board_module, "get_llm_service", lambda: llm)
    monkeypatch.setattr(
        board_module, "get_llm_service_for_provider", lambda *a, **k: llm
    )
    monkeypatch.setattr(board_module, "_get_user_context", lambda: "")
    monkeypatch.setattr(BoardService, "_track_usage", lambda *a, **k: None)
    monkeypatch.setattr(
        BoardService, "_search_web_for_context", _contexte_web_vide
    )
    return llm


async def _traitement_board() -> ProcessingTask | None:
    from app.models.database import get_session_context

    async with get_session_context() as session:
        resultat = await session.execute(
            select(ProcessingTask).where(ProcessingTask.type == "board")
        )
        return resultat.scalars().first()


async def _demander_arret_du_board() -> None:
    from app.services import traitements

    ligne = await _traitement_board()
    assert ligne is not None, "le handle board doit exister avant le flux"
    await traitements.demander_arret(ligne.id)


_taches_d_arret: set = set()


async def _arret_depuis_une_autre_tache() -> None:
    """Comme en réel : la demande part d'une AUTRE tâche (la requête HTTP
    du bouton Annuler), jamais de la tâche porteuse elle-même."""
    tache = asyncio.create_task(_demander_arret_du_board())
    _taches_d_arret.add(tache)
    tache.add_done_callback(_taches_d_arret.discard)


def _evenements(texte: str) -> list[dict]:
    return [
        json.loads(ligne.removeprefix("data: "))
        for ligne in texte.splitlines()
        if ligne.startswith("data: ")
    ]


async def _decision_existe() -> bool:
    from app.models.database import get_session_context
    from app.models.entities import BoardDecisionDB

    async with get_session_context() as session:
        resultat = await session.execute(select(BoardDecisionDB))
        return resultat.scalars().first() is not None


class TestLaDeliberationEstUnTraitement:
    @pytest.mark.asyncio
    async def test_le_flux_emet_le_traitement_en_premier_et_finit_done(
        self, client, board_rapide
    ):
        reponse = await client.post("/api/board/deliberate", json=REQUETE)
        assert reponse.status_code == 200

        evenements = _evenements(reponse.text)
        assert evenements, "le flux SSE doit produire des événements"
        assert evenements[0]["type"] == "task", (
            "l'identifiant du traitement s'émet EN PREMIER - sans lui, "
            "aucun bouton Annuler ne peut viser le chemin canonique"
        )
        task_id = evenements[0]["content"]
        assert task_id

        done = next(e for e in evenements if e["type"] == "done")

        from app.services import traitements

        ligne = await traitements.lire(task_id)
        assert ligne is not None
        assert ligne.type == "board"
        assert ligne.state == EtatTache.DONE
        assert ligne.entity_id == done["content"], (
            "entity_id = le decision_id préalloué, posé dès la création"
        )

    @pytest.mark.asyncio
    async def test_un_echec_finit_failed_jamais_running(
        self, client, board_rapide, monkeypatch
    ):
        from app.services.board import BoardService

        async def synthese_en_panne(*_a, **_k):
            raise RuntimeError("panne de synthèse")

        monkeypatch.setattr(
            BoardService, "_generate_synthesis", synthese_en_panne
        )

        reponse = await client.post("/api/board/deliberate", json=REQUETE)
        evenements = _evenements(reponse.text)
        assert any(e["type"] == "error" for e in evenements)

        ligne = await _traitement_board()
        assert ligne is not None
        assert ligne.state == EtatTache.FAILED


class TestLaMatriceDAnnulation:
    @pytest.mark.asyncio
    async def test_pendant_la_recherche_web(
        self, client, board_rapide, monkeypatch
    ):
        from app.services.board import BoardService

        async def recherche_puis_arret(*_a, **_k):
            await _arret_depuis_une_autre_tache()
            await asyncio.sleep(3600)  # l'annulation doit couper CETTE attente

        monkeypatch.setattr(
            BoardService, "_search_web_for_context", recherche_puis_arret
        )

        reponse = await client.post("/api/board/deliberate", json=REQUETE)
        evenements = _evenements(reponse.text)
        assert any(e["type"] == "cancelled" for e in evenements)
        assert not any(e["type"] == "done" for e in evenements)
        assert not await _decision_existe()
        assert (await _traitement_board()).state == EtatTache.CANCELLED

    @pytest.mark.asyncio
    async def test_pendant_les_advisors_cloud(
        self, client, board_rapide, monkeypatch
    ):
        from app.services import board as board_module

        async def arret_en_plein_avis():
            await _arret_depuis_une_autre_tache()
            await asyncio.sleep(3600)

        llm = FauxLLM(["jamais rendu"], avant_flux=arret_en_plein_avis)
        monkeypatch.setattr(board_module, "get_llm_service", lambda: llm)
        monkeypatch.setattr(
            board_module, "get_llm_service_for_provider", lambda *a, **k: llm
        )

        reponse = await client.post("/api/board/deliberate", json=REQUETE)
        evenements = _evenements(reponse.text)
        assert any(e["type"] == "cancelled" for e in evenements)
        assert not await _decision_existe()
        assert (await _traitement_board()).state == EtatTache.CANCELLED

    @pytest.mark.asyncio
    async def test_en_mode_souverain_sequentiel(
        self, client, board_rapide, monkeypatch
    ):
        from app.services import board as board_module

        async def arret_en_plein_avis():
            await _arret_depuis_une_autre_tache()
            await asyncio.sleep(3600)

        llm = FauxLLM(["jamais rendu"], avant_flux=arret_en_plein_avis)
        from app.services.llm import LLMProvider

        llm.config = SimpleNamespace(provider=LLMProvider.OLLAMA, model="local-test")
        monkeypatch.setattr(board_module, "get_llm_service", lambda: None)
        monkeypatch.setattr(
            board_module, "get_llm_service_for_provider", lambda *a, **k: llm
        )

        requete = dict(REQUETE, mode="sovereign",
                       ollama_models={"analyst": "local-test"})
        reponse = await client.post("/api/board/deliberate", json=requete)
        evenements = _evenements(reponse.text)
        assert any(e["type"] == "cancelled" for e in evenements)
        assert not await _decision_existe()
        assert (await _traitement_board()).state == EtatTache.CANCELLED

    @pytest.mark.asyncio
    async def test_pendant_la_synthese(self, client, board_rapide, monkeypatch):
        from app.models.board import BoardSynthesis
        from app.services.board import BoardService

        async def synthese_puis_arret(*_a, **_k):
            await _demander_arret_du_board()
            return BoardSynthesis(
                consensus_points=["x"], divergence_points=[],
                recommendation="jamais sauvée", confidence="high",
                next_steps=[],
            )

        monkeypatch.setattr(
            BoardService, "_generate_synthesis", synthese_puis_arret
        )

        reponse = await client.post("/api/board/deliberate", json=REQUETE)
        evenements = _evenements(reponse.text)
        assert any(e["type"] == "cancelled" for e in evenements)
        assert not await _decision_existe(), (
            "une décision à moitié voulue ne se sauve pas"
        )
        assert (await _traitement_board()).state == EtatTache.CANCELLED

    @pytest.mark.asyncio
    async def test_apres_le_commit_done_gagne(
        self, client, board_rapide, monkeypatch
    ):
        from app.services.board import BoardService

        commettre_reelle = BoardService._commettre_decision

        async def commit_puis_arret(self, session, *a, **k):
            await commettre_reelle(self, session, *a, **k)
            # la demande d'arrêt arrive juste APRÈS le commit
            await _demander_arret_du_board()

        monkeypatch.setattr(
            BoardService, "_commettre_decision", commit_puis_arret
        )

        reponse = await client.post("/api/board/deliberate", json=REQUETE)
        evenements = _evenements(reponse.text)

        assert await _decision_existe(), "le commit a eu lieu : la décision reste"
        ligne = await _traitement_board()
        assert ligne.state == EtatTache.DONE, (
            "après le commit, done GAGNE - un cancel_requested tardif se "
            "résout en done (contrat 0.46)"
        )
        assert any(e["type"] == "done" for e in evenements), (
            "le client doit apprendre que sa décision existe"
        )


class TestLaFenceAuNiveauService:
    @pytest.mark.asyncio
    async def test_la_fence_bloque_le_commit_sans_annulation_de_tache(
        self, client, board_rapide
    ):
        """La fence est une garantie PROPRE : même si l'annulation de la
        tâche porteuse n'atteint jamais ce point (course), une demande
        d'arrêt durable posée avant le commit empêche la sauvegarde."""
        from app.models.board import AdvisorRole, BoardMode, BoardRequest
        from app.models.database import get_session_context
        from app.services.board import BoardService

        async def toujours_demandee() -> bool:
            return True

        async with get_session_context() as session:
            service = BoardService(session)
            requete = BoardRequest(
                question="Faut-il lancer ce pilote dès maintenant ?",
                mode=BoardMode.CLOUD,
                advisors=[AdvisorRole.ANALYST],
            )
            with pytest.raises(asyncio.CancelledError):
                async for _ in service.deliberate(
                    requete,
                    decision_id="decision-fantome",
                    annulation_demandee=toujours_demandee,
                ):
                    pass

        assert not await _decision_existe()


class TestLaFenetreDuCommit:
    @pytest.mark.asyncio
    async def test_f3_annulation_pendant_la_persistance_done_gagne_quand_meme(
        self, client, board_rapide, monkeypatch
    ):
        """F3 : la demande d'arrêt tombe PENDANT la persistance (avant la
        fin du commit sous shield). La route décidait `cancelled` sans
        attendre la fin de la persistance protégée - la décision
        apparaissait ensuite avec un traitement qui la niait."""
        from app.services.board import BoardService

        persistance_originale = BoardService._persister_decision

        async def persistance_pendant_laquelle_on_annule(
            self, decision_id, request, opinions, synthesis
        ):
            await _arret_depuis_une_autre_tache()
            # laisser l'adaptateur annuler la tâche porteuse et la route
            # avancer jusqu'à sa décision
            await asyncio.sleep(0.3)
            await persistance_originale(
                self, decision_id, request, opinions, synthesis
            )

        monkeypatch.setattr(
            BoardService, "_persister_decision",
            persistance_pendant_laquelle_on_annule,
        )

        reponse = await client.post("/api/board/deliberate", json=REQUETE)
        evenements = _evenements(reponse.text)

        # le commit protégé DOIT aboutir (le shield existe pour ça)
        decision_la = False
        for _ in range(100):
            if await _decision_existe():
                decision_la = True
                break
            await asyncio.sleep(0.05)
        assert decision_la, "le shield n'a pas laissé la persistance aboutir"

        ligne = await _traitement_board()
        assert ligne.state == EtatTache.DONE, (
            "la route a décidé cancelled sans attendre la fin de la "
            "persistance protégée : la décision existe mais le traitement "
            "la nie"
        )
        assert any(e["type"] == "done" for e in evenements), (
            "le client doit apprendre que sa décision existe"
        )


class TestLaDeconnexionSousAnyio:
    @pytest.mark.asyncio
    async def test_le_nettoyage_survit_a_l_annulation_level_triggered(
        self, client, board_rapide, monkeypatch
    ):
        """Second panel : sous uvicorn/Starlette, la déconnexion annule le
        générateur via un CancelScope anyio LEVEL-TRIGGERED - chaque await
        du bloc de nettoyage re-lève CancelledError. Un nettoyage attendu
        dans le except est coupé : la ligne board restait `running` fantôme
        jusqu'au redémarrage. Le nettoyage doit survivre en tâche détachée."""
        import anyio
        from app.models.board import BoardRequest
        from app.routers import board as board_router
        from app.services import board as board_module

        avancee = asyncio.Event()

        async def arret_jamais(*_a, **_k):
            avancee.set()
            await asyncio.sleep(3600)

        llm = FauxLLM(["jamais rendu"], avant_flux=arret_jamais)
        monkeypatch.setattr(board_module, "get_llm_service", lambda: llm)
        monkeypatch.setattr(
            board_module, "get_llm_service_for_provider", lambda *a, **k: llm
        )

        reponse = await board_router.deliberate(BoardRequest(**REQUETE))

        async def consommer(scope):
            async for _chunk in reponse.body_iterator:
                if avancee.is_set():
                    # le client disparaît : Starlette annule le scope
                    scope.cancel()

        async with anyio.create_task_group() as tg:
            tg.start_soon(consommer, tg.cancel_scope)

        # la ligne DOIT devenir terminale sans redémarrage
        ligne = None
        for _ in range(100):
            ligne = await _traitement_board()
            if ligne is not None and ligne.state in (
                EtatTache.CANCELLED, EtatTache.DONE, EtatTache.FAILED
            ):
                break
            await asyncio.sleep(0.05)
        assert ligne is not None
        assert ligne.state == EtatTache.CANCELLED, (
            f"ligne restée « {ligne.state} » : le nettoyage a été coupé par "
            "l'annulation level-triggered - board fantôme jusqu'au redémarrage"
        )


class TestLaSessionDeLaPersistance:
    @pytest.mark.asyncio
    async def test_p24_la_persistance_survit_a_la_fermeture_de_la_route(
        self, client, board_rapide, monkeypatch
    ):
        """Passe 2 (P2-4) : la persistance détachée roulait sur la session
        de la route - la déconnexion sortait du `async with` et fermait la
        session PENDANT le commit protégé. La persistance doit posséder sa
        propre session."""
        import anyio
        from app.models.board import BoardRequest
        from app.routers import board as board_router
        from app.services.board import BoardService

        persistance_commencee = asyncio.Event()
        porte = asyncio.Event()
        originale = BoardService._persister_decision

        async def persistance_gated(self, *a, **k):
            persistance_commencee.set()
            await porte.wait()
            await originale(self, *a, **k)

        monkeypatch.setattr(
            BoardService, "_persister_decision", persistance_gated
        )

        reponse = await board_router.deliberate(BoardRequest(**REQUETE))

        async with anyio.create_task_group() as tg:
            async def watcher():
                await persistance_commencee.wait()
                tg.cancel_scope.cancel()  # le client disparaît PENDANT le commit

            async def consommer():
                async for _chunk in reponse.body_iterator:
                    pass

            tg.start_soon(watcher)
            tg.start_soon(consommer)

        porte.set()  # le commit protégé peut maintenant s'exécuter

        decision_la = False
        for _ in range(100):
            if await _decision_existe():
                decision_la = True
                break
            await asyncio.sleep(0.05)
        assert decision_la, (
            "le commit protégé a échoué : il roulait sur la session fermée "
            "de la route"
        )
        ligne = None
        for _ in range(100):
            ligne = await _traitement_board()
            if ligne is not None and ligne.state in (
                EtatTache.DONE, EtatTache.CANCELLED, EtatTache.FAILED
            ):
                break
            await asyncio.sleep(0.05)
        assert ligne is not None and ligne.state == EtatTache.DONE, (
            f"ligne « {ligne.state if ligne else '?'} » : la décision existe, "
            "done doit gagner"
        )


class TestLaPasse3Board:
    @pytest.mark.asyncio
    async def test_p37_une_panne_de_verification_apres_commit_reste_done(
        self, client, board_rapide, monkeypatch
    ):
        """Passe 3 (P3-7) : commit réussi + SELECT de vérification en panne
        était requalifié en échec - la décision existait avec un traitement
        failed. Après un commit réussi, done gagne."""
        from app.services.board import BoardService

        originale = BoardService._commettre_decision

        async def commit_puis_verification_en_panne(self, session, *a, **k):
            await originale(self, session, *a, **k)
            raise RuntimeError("SELECT de vérification en panne")

        monkeypatch.setattr(
            BoardService, "_commettre_decision",
            commit_puis_verification_en_panne,
        )

        reponse = await client.post("/api/board/deliberate", json=REQUETE)
        evenements = _evenements(reponse.text)

        assert await _decision_existe(), "le commit a réellement eu lieu"
        ligne = await _traitement_board()
        assert ligne.state == EtatTache.DONE, (
            f"ligne « {ligne.state} » : une panne de la VÉRIFICATION a été "
            "requalifiée en échec alors que la décision existe"
        )
        assert any(e["type"] == "done" for e in evenements)

    @pytest.mark.asyncio
    async def test_p37b_la_separation_interne_commit_verification(
        self, client, board_rapide
    ):
        """Durcissement passe 4 (P4-3) : tester la SÉPARATION INTERNE de
        _commettre_decision, pas seulement la ceinture du routeur - une
        panne du SELECT de vérification après un commit abouti ne doit pas
        lever."""
        from app.models.board import (
            AdvisorOpinion,
            AdvisorRole,
            BoardMode,
            BoardRequest,
            BoardSynthesis,
        )
        from app.models.database import get_session_context
        from app.services.board import BoardService

        class SessionVerificationCassee:
            """Proxy : commit réel, puis tout execute suivant casse."""

            def __init__(self, vraie):
                self._vraie = vraie
                self._commit_fait = False

            def add(self, obj):
                self._vraie.add(obj)

            async def commit(self):
                await self._vraie.commit()
                self._commit_fait = True

            async def execute(self, *a, **k):
                if self._commit_fait:
                    raise RuntimeError("SELECT de vérification en panne")
                return await self._vraie.execute(*a, **k)

            async def rollback(self):
                await self._vraie.rollback()

        synthese = BoardSynthesis(
            consensus_points=["x"], divergence_points=[],
            recommendation="Tester", confidence="high", next_steps=[],
        )
        requete = BoardRequest(
            question="Faut-il lancer ce pilote dès maintenant ?",
            mode=BoardMode.CLOUD, advisors=[AdvisorRole.ANALYST],
        )
        opinions = [AdvisorOpinion(
            role=AdvisorRole.ANALYST, name="L'Analyste", emoji="",
            content="Avis", provider="test",
        )]

        async with get_session_context() as session:
            service = BoardService(session)
            # ne doit PAS lever : le commit a abouti
            await service._commettre_decision(
                SessionVerificationCassee(session),
                "decision-verif-cassee", requete, opinions, synthese,
            )

        assert await _decision_existe()
