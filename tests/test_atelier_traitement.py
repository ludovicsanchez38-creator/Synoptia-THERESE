"""Phase 3 du chantier 0.46 - l'Atelier est un traitement visible et honnête.

Contrats (design V2.1) : une mission crée un ProcessingTask type `atelier`
lié à l'AgentTask (`entity_id`), vivant au registre runtime PENDANT le flux,
et l'état final est COHÉRENT avec celui de l'AgentTask sur tous les chemins
de sortie (succès, erreur, annulation/déconnexion).
"""

import asyncio
import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from app.models.processing import EtatTache, ProcessingTask
from app.models.schemas_agents import AgentStreamChunk
from sqlmodel import select


def _git_factice():
    git = MagicMock()
    git.is_repo = AsyncMock(return_value=True)
    git.current_branch = AsyncMock(return_value="main")
    git.ensure_clean = AsyncMock(return_value=True)
    return git


async def _traitement_atelier(agent_task_id: str) -> ProcessingTask | None:
    from app.models.database import get_session_context

    async with get_session_context() as session:
        resultat = await session.execute(
            select(ProcessingTask).where(
                ProcessingTask.type == "atelier",
                ProcessingTask.entity_id == agent_task_id,
            )
        )
        return resultat.scalars().first()


def _task_id_du_flux(texte: str) -> str:
    ligne = next(
        ligne for ligne in texte.splitlines() if '"task_id"' in ligne
    )
    return json.loads(ligne.removeprefix("data: "))["task_id"]


class TestLaMissionEstUnTraitement:
    @pytest.mark.asyncio
    async def test_nominal_running_pendant_done_apres(self, client, tmp_path: Path):
        repo = tmp_path / "repo-a"
        repo.mkdir()
        constats: dict[str, object] = {}

        class FakeSwarm:
            def __init__(self, _source_path: str):
                pass

            async def process_request(self, _message: str, task_id: str):
                # PENDANT le flux : le traitement existe, tourne, et son
                # adaptateur est vivant (annulable depuis le panneau).
                from app.services import task_registry

                traitement = await _traitement_atelier(task_id)
                constats["pendant_state"] = traitement.state if traitement else None
                constats["pendant_vivant"] = (
                    task_registry.est_vivante(traitement.id) if traitement else False
                )
                yield AgentStreamChunk(
                    type="done", content="Terminé", task_id=task_id, phase="review",
                )

        with (
            patch("app.routers.agents._get_source_path", return_value=str(repo)),
            patch("app.routers.agents.GitService", return_value=_git_factice()),
            patch("app.routers.agents.SwarmOrchestrator", FakeSwarm),
        ):
            reponse = await client.post(
                "/api/agents/request", json={"message": "Mission nominale"},
            )

        assert reponse.status_code == 200, reponse.text
        assert constats["pendant_state"] == EtatTache.RUNNING
        assert constats["pendant_vivant"] is True

        traitement = await _traitement_atelier(_task_id_du_flux(reponse.text))
        assert traitement is not None
        assert traitement.state == EtatTache.DONE
        assert "Mission nominale" in traitement.label

    @pytest.mark.asyncio
    async def test_une_erreur_termine_failed(self, client, tmp_path: Path):
        repo = tmp_path / "repo-b"
        repo.mkdir()

        class SwarmEnPanne:
            def __init__(self, _source_path: str):
                pass

            async def process_request(self, _message: str, task_id: str):
                yield AgentStreamChunk(
                    type="agent_start", agent="katia", content="départ",
                    task_id=task_id, phase="spec",
                )
                raise RuntimeError("orchestrateur en panne")

        with (
            patch("app.routers.agents._get_source_path", return_value=str(repo)),
            patch("app.routers.agents.GitService", return_value=_git_factice()),
            patch("app.routers.agents.SwarmOrchestrator", SwarmEnPanne),
        ):
            reponse = await client.post(
                "/api/agents/request", json={"message": "Mission en panne"},
            )

        traitement = await _traitement_atelier(_task_id_du_flux(reponse.text))
        assert traitement is not None
        assert traitement.state == EtatTache.FAILED
        assert "panne" in (traitement.error or "")

    @pytest.mark.asyncio
    async def test_une_annulation_termine_cancelled_et_reste_coherente(
        self, client, tmp_path: Path
    ):
        """Déconnexion ou annulation : CancelledError traverse le flux - le
        ProcessingTask finit `cancelled`, comme l'AgentTask, jamais un
        `running` fantôme."""
        repo = tmp_path / "repo-c"
        repo.mkdir()
        capture: dict[str, str] = {}

        class SwarmAnnule:
            def __init__(self, _source_path: str):
                pass

            async def process_request(self, _message: str, task_id: str):
                capture["agent_task_id"] = task_id
                yield AgentStreamChunk(
                    type="agent_start", agent="katia", content="départ",
                    task_id=task_id, phase="spec",
                )
                raise asyncio.CancelledError()

        with (
            patch("app.routers.agents._get_source_path", return_value=str(repo)),
            patch("app.routers.agents.GitService", return_value=_git_factice()),
            patch("app.routers.agents.SwarmOrchestrator", SwarmAnnule),
        ):
            try:
                await client.post(
                    "/api/agents/request", json={"message": "Mission annulée"},
                )
            except BaseException:
                pass  # le CancelledError peut traverser le client de test

        traitement = await _traitement_atelier(capture["agent_task_id"])
        assert traitement is not None
        assert traitement.state == EtatTache.CANCELLED

        from app.models.database import get_session_context
        from app.models.entities_agents import AgentTask

        async with get_session_context() as session:
            resultat = await session.execute(
                select(AgentTask).where(AgentTask.id == capture["agent_task_id"])
            )
            agent_task = resultat.scalar_one_or_none()
        assert agent_task is not None
        assert agent_task.status == "cancelled", (
            "les deux cycles de vie doivent dire la même chose"
        )


class TestLInitialisationEstCouverte:
    """Passe 2 de revue : l'annulation gagnée avant le démarrage lançait
    quand même la mission, et un échec de liaison laissait un running
    fantôme."""

    @pytest.mark.asyncio
    async def test_une_mission_annulee_avant_demarrage_ne_tourne_pas(
        self, client, tmp_path: Path, monkeypatch
    ):
        from app.services import traitements

        repo = tmp_path / "repo-annule"
        repo.mkdir()
        orchestrateur_lance = {"oui": False}
        # Sans ce temoin, l'unique assertion du test portait sur la valeur
        # INITIALE d'orchestrateur_lance : elle etait satisfaite d'avance, y
        # compris si la requete echouait avant meme d'atteindre le traitement.
        demarrage_demande = {"oui": False}

        class SwarmSentinelle:
            def __init__(self, _source_path: str):
                pass

            async def process_request(self, _message: str, task_id: str):
                orchestrateur_lance["oui"] = True
                yield AgentStreamChunk(
                    type="done", content="", task_id=task_id, phase="review",
                )

        class HandleAnnule:
            id = "mission-annulee"

            async def demarrer(self):
                demarrage_demande["oui"] = True
                raise traitements.AnnuleAvantDemarrage("annulée")

            async def lier_adaptateur(self, _a):
                raise AssertionError("jamais atteint")

            async def terminer(self, *_a, **_k):
                return None

        async def creer_annulee(**_k):
            return HandleAnnule()

        monkeypatch.setattr(traitements, "creer_traitement", creer_annulee)

        with (
            patch("app.routers.agents._get_source_path", return_value=str(repo)),
            patch("app.routers.agents.GitService", return_value=_git_factice()),
            patch("app.routers.agents.SwarmOrchestrator", SwarmSentinelle),
        ):
            try:
                await client.post(
                    "/api/agents/request", json={"message": "Mission annulée tôt"},
                )
            except asyncio.CancelledError:
                # SEULE exception attendue. `except BaseException: pass`
                # avalait aussi l'AssertionError sentinelle de
                # lier_adaptateur et n'importe quelle panne de requete : le
                # test etait vert quelle que soit la cause.
                pass

        assert demarrage_demande["oui"] is True, (
            "le parcours n'a pas atteint le demarrage du traitement : "
            "ce test ne prouve rien sur l'annulation"
        )
        assert orchestrateur_lance["oui"] is False, (
            "l'orchestrateur ne doit JAMAIS tourner pour une mission annulée "
            "avant son démarrage"
        )

    @pytest.mark.asyncio
    async def test_un_echec_de_liaison_termine_failed(
        self, client, tmp_path: Path, monkeypatch
    ):
        from app.models.processing import EtatTache as Etat
        from app.services import traitements

        repo = tmp_path / "repo-bancal"
        repo.mkdir()
        terminaisons: list[tuple] = []

        class SwarmOk:
            def __init__(self, _source_path: str):
                pass

            async def process_request(self, _message: str, task_id: str):
                yield AgentStreamChunk(
                    type="done", content="Fini", task_id=task_id, phase="review",
                )

        class HandleBancal:
            id = "mission-bancale"

            async def demarrer(self):
                return None

            async def lier_adaptateur(self, _a):
                raise RuntimeError("registre en panne")

            async def terminer(self, etat, error=None):
                terminaisons.append((etat, error))

        async def creer_bancale(**_k):
            return HandleBancal()

        monkeypatch.setattr(traitements, "creer_traitement", creer_bancale)

        with (
            patch("app.routers.agents._get_source_path", return_value=str(repo)),
            patch("app.routers.agents.GitService", return_value=_git_factice()),
            patch("app.routers.agents.SwarmOrchestrator", SwarmOk),
        ):
            reponse = await client.post(
                "/api/agents/request", json={"message": "Mission bancale"},
            )

        assert reponse.status_code == 200
        assert terminaisons and terminaisons[0][0] == Etat.FAILED, (
            "l'echec de liaison doit terminer la ligne failed, jamais "
            "l'abandonner running"
        )
