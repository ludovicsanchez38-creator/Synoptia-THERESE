"""
THÉRÈSE v2 - Agents Router

Endpoints pour le système d'agents IA embarqués (Atelier).
"""

import asyncio
import contextlib
import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.models.database import get_session
from app.models.entities_agents import AgentMessage, AgentSession, AgentTask
from app.models.processing import EtatTache as EtatTacheTraitement
from app.models.schemas_agents import (
    AgentConfigResponse,
    AgentConfigUpdate,
    AgentProfileResponse,
    AgentRequest,
    AgentSessionListResponse,
    AgentSessionResponse,
    AgentStatusResponse,
    AgentStreamChunk,
    AgentTaskListResponse,
    AgentTaskResponse,
    DiffFileResponse,
    DiffResponse,
    DispatchRequest,
    OpenClawStatusResponse,
    SendMessageRequest,
    SessionMessageResponse,
    SpawnAgentRequest,
)
from app.services.agents.git_service import GitService
from app.services.agents.swarm import SwarmOrchestrator
from app.services.error_handler import message_pour_ecran
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import func, select

logger = logging.getLogger(__name__)

router = APIRouter()


def repo_error_message(source_path: str) -> str:
    """Explique l'absence de dépôt Git à quelqu'un qui n'est pas développeur.

    Triage 26/07/2026 : un testeur avait pointé une archive ZIP de GitHub,
    décompressée. Elle contient bien un `.gitignore`, mais jamais l'historique.
    L'ancien message (« n'est pas un depot Git (.git absent) ») lui a fait
    croire qu'un fichier manquait à son dossier.
    """
    return (
        f"Le dossier « {source_path} » n'est pas un dépôt Git : le dossier .git "
        "est absent. Une archive ZIP téléchargée depuis GitHub ne contient pas "
        "l'historique du projet, même si elle contient un fichier .gitignore.\n"
        "Récupère le projet par un clone dans un dossier NEUF (Git refuse une "
        "destination déjà remplie), puis indique ce nouveau dossier ici :\n"
        "git clone <adresse du dépôt> therese-source"
    )
_running_agent_tasks: dict[str, asyncio.Task[Any]] = {}
_PROFILE_DISABLED_MUTATION_TOOLS = {"write_file", "run_command"}
_MAX_OPENCLAW_AGENTS = 3


def _get_source_path() -> str | None:
    """Récupère le chemin du source configuré.

    Priorité : DB > env var > auto-détection.
    """
    import os
    from pathlib import Path

    # 1. Préférence en DB (configurée via l'onglet Agents dans les paramètres)
    try:

        from app.config import settings

        db_path = settings.db_path
        if db_path and Path(db_path).exists():
            from app.models.database import db_connect

            conn = db_connect(db_path)  # US-014 : clé SQLCipher si chiffrée
            cursor = conn.execute("SELECT value FROM preferences WHERE key = 'agent_source_path'")
            row = cursor.fetchone()
            conn.close()
            if row and row[0]:
                raw = row[0].strip().strip('"').strip("'")
                p = Path(raw).expanduser().resolve()
                if p.exists():
                    has_git = (p / ".git").exists() or (p / ".git").is_file()
                    if not has_git:
                        logger.warning(
                            "Chemin configure '%s' (resolu: '%s') existe mais .git non trouve. "
                            "Le chemin est quand meme utilise (priorite config utilisateur).",
                            row[0], p,
                        )
                    return str(p)
                logger.warning(
                    "Chemin configure '%s' (resolu: '%s') n'existe pas, fallback auto-detection.",
                    row[0], p,
                )
    except Exception as e:
        logger.debug("Agent config non disponible: %s", e)

    # 2. Variable d'environnement explicite
    env_path = os.environ.get("THERESE_SOURCE_PATH")
    if env_path:
        return env_path

    # 3. Auto-détection en mode dev (non empaquété)
    # src/backend/app/routers/agents.py → 5 niveaux = racine projet
    project_root = Path(__file__).resolve().parent.parent.parent.parent.parent
    if (project_root / ".git").exists() and (project_root / "src" / "backend").exists():
        return str(project_root)

    # 4. Emplacements connus (build empaquété, les chemins __file__ ne marchent plus)
    home = Path.home()
    known_paths = [
        # macOS / Linux
        home / "Developer" / "Synoptia-THERESE",
        home / "Desktop" / "Dev Synoptia" / "Synoptia-THERESE",
        home / "Desktop" / "Dev Synoptia" / "THERESE V2",
        home / "repos" / "Synoptia-THERESE",
        home / "Documents" / "Synoptia-THERESE",
        # Windows (Path.home() = C:\Users\<username>)
        home / "Desktop" / "Synoptia-THERESE",
        home / "source" / "repos" / "Synoptia-THERESE",  # Visual Studio default
        home / "Projects" / "Synoptia-THERESE",
        home / "GitHub" / "Synoptia-THERESE",  # GitHub Desktop default
    ]
    for candidate in known_paths:
        if (
            candidate.exists()
            and (candidate / ".git").exists()
            and (candidate / "src" / "backend").exists()
        ):
            return str(candidate)

    return None


async def _save_task(session: AsyncSession, task: AgentTask) -> None:
    """Sauvegarde une tâche agent en DB."""
    session.add(task)
    await session.commit()
    await session.refresh(task)


async def _save_message(session: AsyncSession, msg: AgentMessage) -> None:
    """Sauvegarde un message agent en DB."""
    session.add(msg)
    await session.commit()


def _resoudre_depot_autorise(source_path: str, configured_source: str | None) -> Path:
    """Résout un chemin demandé et refuse tout écart avec le dépôt autorisé.

    B-099 : cette garde n'existait que sur `/request`. `/spawn` prenait
    `request.source_path` sans jamais le comparer aux réglages, si bien que la
    porte d'entrée dépendait de la route empruntée. Une seule fonction, pour
    que la troisième route ne diverge pas à son tour.

    Sans dépôt configuré, il n'y a rien à comparer : le chemin demandé fait
    foi, comme avant.
    """
    resolved = Path(source_path).expanduser().resolve()
    if configured_source:
        configured_resolved = Path(configured_source).expanduser().resolve()
        if resolved != configured_resolved:
            raise HTTPException(
                status_code=403,
                detail="Le chemin demandé ne correspond pas au dépôt autorisé dans les réglages.",
            )
    return resolved


# ============================================================
# Streaming endpoint
# ============================================================


@router.post("/request")
async def agent_request(
    request: AgentRequest,
    session: AsyncSession = Depends(get_session),
):
    """Soumet une demande au swarm d'agents. Retourne un stream SSE."""
    configured_source = _get_source_path()
    source_path = request.source_path or configured_source
    if not source_path:
        raise HTTPException(
            status_code=400,
            detail="Chemin du code source non configuré. Configure THERESE_SOURCE_PATH ou passe source_path.",
        )

    resolved_source = _resoudre_depot_autorise(source_path, configured_source)
    git = GitService(resolved_source)
    if not resolved_source.exists():
        raise HTTPException(status_code=400, detail="Le dossier autorisé n'est pas un dépôt Git valide.")
    depot = await git.is_repo()
    if depot is None:
        # BUG-163 : on refuse toujours de lancer une mission sur un dépôt non
        # vérifié, mais on ne prétend plus savoir pourquoi.
        raise HTTPException(
            status_code=503,
            detail="Git n'a pas répondu : impossible de vérifier le dépôt. Réessaie dans un instant.",
        )
    if not depot:
        raise HTTPException(status_code=400, detail="Le dossier autorisé n'est pas un dépôt Git valide.")
    current_branch = await git.current_branch()
    if current_branch != "main":
        raise HTTPException(
            status_code=409,
            detail=f"L'Atelier exige la branche main, branche actuelle : {current_branch}.",
        )
    if not await git.ensure_clean():
        raise HTTPException(
            status_code=409,
            detail="Le dépôt contient des changements non enregistrés. Termine-les avant de lancer une mission.",
        )
    active_result = await session.execute(
        select(func.count(AgentTask.id)).where(
            AgentTask.status.in_(["pending", "in_progress"])
        )
    )
    if (active_result.scalar() or 0) > 0:
        raise HTTPException(
            status_code=409,
            detail="Une mission Atelier est déjà en cours. Attends sa fin ou annule-la.",
        )
    source_path = str(resolved_source)

    # Créer la tâche en DB
    task = AgentTask(
        title=request.message[:100],
        description=request.message,
        status="in_progress",
        source_path=source_path,
    )
    await _save_task(session, task)

    # Sauvegarder le message utilisateur
    user_msg = AgentMessage(
        task_id=task.id,
        agent="user",
        role="user",
        content=request.message,
    )
    await _save_message(session, user_msg)

    async def event_stream():
        current_async_task = asyncio.current_task()
        if current_async_task is not None:
            _running_agent_tasks[task.id] = current_async_task
        # 0.46 : la mission est un TRAITEMENT visible - ProcessingTask lié à
        # l'AgentTask (entity_id), annulable depuis le panneau par le même
        # mécanisme que la route historique (asyncio.Task.cancel). Créé DANS
        # la zone couverte par le finally (revue F8) : une panne ici ne doit
        # pas laisser un suivi orphelin.
        from app.services import task_registry, traitements

        handle = None
        annulee_avant_demarrage = False
        try:
            handle = await traitements.creer_traitement(
                type="atelier",
                label=f"Atelier : {request.message[:80]}",
                entity_id=task.id,
            )
            try:
                await handle.demarrer()
                if current_async_task is not None:
                    await handle.lier_adaptateur(
                        task_registry.AnnulationParTacheAsyncio(current_async_task)
                    )
            except traitements.AnnuleAvantDemarrage:
                # L'annulation a gagné la course avant le démarrage : la
                # mission ne doit PAS tourner (passe 2 de revue).
                annulee_avant_demarrage = True
            except Exception:
                # Échec après la création : terminer failed plutôt que de
                # laisser un running fantôme (passe 2 de revue).
                logger.warning("Suivi de mission en panne", exc_info=True)
                with contextlib.suppress(Exception):
                    await handle.terminer(
                        EtatTacheTraitement.FAILED,
                        error="suivi en panne à l'initialisation",
                    )
                handle = None
        except Exception:
            logger.warning("Suivi de mission indisponible", exc_info=True)
            handle = None
        orchestrator = SwarmOrchestrator(source_path)
        final_status = "review"
        final_error = None
        branch_name = None
        files_changed = []
        diff_summary = ""
        run_phase = "spec"
        plan = ""
        test_results: list[str] = []
        explanation = ""
        events: list[dict[str, Any]] = []
        agent_outputs: dict[str, str] = {"katia": "", "zezette": ""}
        agent_models: dict[str, str] = {}
        base_branch = None
        commit_hash = None

        try:
            if annulee_avant_demarrage:
                raise asyncio.CancelledError()
            async for chunk in orchestrator.process_request(request.message, task.id):
                events.append(chunk.model_dump(mode="json", exclude_none=True))
                if chunk.phase:
                    run_phase = chunk.phase
                if chunk.model and chunk.agent:
                    agent_models[chunk.agent] = chunk.model
                if chunk.type == "handoff":
                    plan = chunk.content
                elif chunk.type == "test_result":
                    test_results.append(chunk.content)
                elif chunk.type == "explanation":
                    explanation += chunk.content
                elif chunk.type == "agent_chunk" and chunk.agent:
                    agent_outputs[chunk.agent] = agent_outputs.get(chunk.agent, "") + chunk.content
                elif chunk.type == "agent_done" and chunk.agent and chunk.content:
                    agent_outputs[chunk.agent] = chunk.content

                # Mettre à jour la tâche selon les événements
                if chunk.type == "review_ready":
                    branch_name = chunk.branch
                    files_changed = chunk.files_changed or []
                    diff_summary = chunk.diff_summary or ""
                    base_branch = chunk.base_branch
                    commit_hash = chunk.commit_hash
                elif chunk.type == "error":
                    final_status = "error"
                    final_error = chunk.content
                elif chunk.type == "done":
                    if chunk.phase == "review":
                        final_status = "review"
                    else:
                        final_status = "done"

                # Émettre le chunk SSE
                data = chunk.model_dump(exclude_none=True)
                yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"

        except asyncio.CancelledError:
            final_status = "cancelled"
            final_error = "Mission annulée par l'utilisateur."
            raise
        except Exception as e:
            logger.error(f"Erreur swarm: {e}", exc_info=True)
            error_chunk = AgentStreamChunk(
                type="error",
                content=f"Erreur inattendue : {e}",
                task_id=task.id,
            )
            yield f"data: {json.dumps(error_chunk.model_dump(exclude_none=True), ensure_ascii=False)}\n\n"
            final_status = "error"
            final_error = str(e)
        finally:
            persistance_agent_task_ok = False
            if _running_agent_tasks.get(task.id) is current_async_task:
                _running_agent_tasks.pop(task.id, None)
            # rien ici : le traitement est terminé APRÈS la persistance de
            # l'AgentTask, plus bas (revue F8 : deux transactions, la seconde
            # en échec laissait done + in_progress - incohérence durable).
            # Même si le client ferme le flux, l'état local doit refléter
            # l'annulation et ne jamais rester artificiellement « en cours ».
            try:
                from app.models.database import get_session_context

                async with get_session_context() as update_session:
                    result = await update_session.execute(
                        select(AgentTask).where(AgentTask.id == task.id)
                    )
                    db_task = result.scalar_one_or_none()
                    if db_task:
                        db_task.status = final_status
                        db_task.branch_name = branch_name
                        db_task.files_changed = (
                            json.dumps(files_changed, ensure_ascii=False) if files_changed else None
                        )
                        db_task.diff_summary = diff_summary
                        db_task.run_phase = run_phase
                        db_task.plan = plan or None
                        db_task.test_results = json.dumps(test_results, ensure_ascii=False)
                        db_task.explanation = explanation or None
                        db_task.events = json.dumps(events, ensure_ascii=False)
                        db_task.agent_outputs = json.dumps(agent_outputs, ensure_ascii=False)
                        db_task.agent_model = (
                            json.dumps(agent_models, ensure_ascii=False) if agent_models else None
                        )
                        db_task.base_branch = base_branch
                        db_task.commit_hash = commit_hash
                        db_task.error = final_error
                        db_task.updated_at = datetime.now(UTC)
                        await update_session.commit()
                persistance_agent_task_ok = True
            except Exception as e:
                logger.error(f"Erreur mise à jour tâche: {e}")


            # Cohérence des deux cycles de vie (revue F8) : le traitement se
            # termine APRÈS l'AgentTask. Si SA persistance a échoué, le
            # traitement le DIT (failed) plutôt que d'annoncer un done
            # incohérent avec une mission restée in_progress.
            if handle is not None:
                try:
                    if not persistance_agent_task_ok:
                        await handle.terminer(
                            EtatTacheTraitement.FAILED,
                            error="Persistance de la mission en échec - états à réconcilier",
                        )
                    elif final_status == "cancelled":
                        await handle.terminer(EtatTacheTraitement.CANCELLED)
                    elif final_status == "error":
                        await handle.terminer(
                            EtatTacheTraitement.FAILED, error=(final_error or "")[:500]
                        )
                    else:
                        await handle.terminer(EtatTacheTraitement.DONE)
                except Exception:
                    logger.warning(
                        "État du traitement Atelier non consigné", exc_info=True
                    )
    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )



# ============================================================
# Agent Profiles & Spawn (agents locaux preconfigures)
# ============================================================


@router.get("/profiles")
async def list_profiles() -> list[AgentProfileResponse]:
    """Liste les profils d'agents preconfigures disponibles dans l'Atelier."""
    from app.services.agents.profiles import get_profiles

    profiles = get_profiles()

    # Lire le modele LLM configure par l'utilisateur (pour proposer comme defaut)
    user_model = None
    try:
        from app.services.llm import get_llm_service
        svc = get_llm_service()
        if svc and svc.config:
            user_model = svc.config.model
    except Exception:
        pass

    default_model = user_model or "claude-sonnet-4-6"

    return [
        AgentProfileResponse(
            id=p["id"],
            name=p["name"],
            icon=p["icon"],
            description=p["description"],
            color=p["color"],
            tools=[
                tool
                for tool in p["tools"]
                if tool not in _PROFILE_DISABLED_MUTATION_TOOLS
            ],
            default_model=default_model,
        )
        for p in profiles
    ]


@router.post("/spawn")
async def spawn_agent(request: SpawnAgentRequest):
    """Lance un agent local avec un profil preconfigure. Retourne un stream SSE.

    L'agent utilise le system_prompt du profil et uniquement les outils autorises
    par ce profil. Pas de flow Katia/Zezette (agent autonome, pas de handoff).
    """
    from app.services.agents.config import AgentConfig
    from app.services.agents.profiles import get_profile
    from app.services.agents.runtime import AgentRuntime
    from app.services.agents.tools import (
        THERESE_TOOLS,
        ZEZETTE_TOOLS,
        AgentToolExecutor,
    )

    # Determiner le source_path (pour les outils fichiers/git)
    # B-099 : la garde du dépôt autorisé passe AVANT tout le reste, comme sur
    # /request. Un chemin hors périmètre n'a pas à dépendre de la validité du
    # profil demandé.
    configured_source = _get_source_path()
    source_path = request.source_path or configured_source
    if source_path:
        _resoudre_depot_autorise(source_path, configured_source)

    # Charger le profil
    profile = get_profile(request.profile_id)
    if not profile:
        raise HTTPException(
            status_code=404,
            detail=f"Profil d'agent introuvable : {request.profile_id}",
        )

    # Creer la config d'agent a partir du profil
    config = AgentConfig(
        id=profile["id"],
        name=profile["name"],
        description=profile["description"],
        system_prompt=profile["system_prompt"],
        tools=profile["tools"],
        max_iterations=10,
    )

    # Creer le tool executor avec git si le source path existe
    git_svc = None
    if source_path:
        git_svc = GitService(source_path)
    tool_executor = AgentToolExecutor(
        source_path=source_path,
        git_service=git_svc,
    )

    # Filtrer les outils selon le profil (exclure les outils swarm internes)
    # Les profils autonomes n'ont ni worktree isolé ni revue persistée.
    # Ils restent donc en lecture/recherche jusqu'à adoption du contrat 0.40.
    allowed_tools = set(profile["tools"]) - _PROFILE_DISABLED_MUTATION_TOOLS
    swarm_only_tools = {"clarify", "create_spec", "explain_change"}
    all_tools = {
        t["function"]["name"]: t
        for t in THERESE_TOOLS + ZEZETTE_TOOLS
        if t["function"]["name"] not in swarm_only_tools
    }

    # Ajouter web_search si demande par le profil
    if "web_search" in allowed_tools:
        all_tools["web_search"] = {
            "type": "function",
            "function": {
                "name": "web_search",
                "description": "Recherche sur le web via Brave Search ou DuckDuckGo",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Requete de recherche",
                        },
                        "max_results": {
                            "type": "integer",
                            "description": "Nombre max de resultats (defaut: 5)",
                        },
                    },
                    "required": ["query"],
                },
            },
        }

    tools_schema = [all_tools[name] for name in allowed_tools if name in all_tools]

    # Determiner le modele LLM (requete > config utilisateur > defaut profil)
    agent_model = request.model
    if not agent_model:
        try:
            from app.services.llm import get_llm_service
            svc = get_llm_service()
            if svc and svc.config:
                agent_model = svc.config.model
        except Exception:
            pass

    # Creer le runtime
    runtime = AgentRuntime(
        config=config,
        tool_executor=tool_executor,
        tools_schema=tools_schema,
        model_override=agent_model,
    )

    async def event_stream():
        try:
            async for event in runtime.run(request.instruction):
                chunk = AgentStreamChunk(
                    type=event.type,
                    agent=profile["id"],
                    content=event.content,
                    tool_name=event.tool_name,
                )
                data = chunk.model_dump(exclude_none=True)
                yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"

        except Exception as e:
            logger.error(f"Erreur agent spawn {profile['id']}: {e}", exc_info=True)
            error_chunk = AgentStreamChunk(
                type="error",
                agent=profile["id"],
                content=message_pour_ecran(e, ou="pendant la mission de l'agent"),
            )
            yield f"data: {json.dumps(error_chunk.model_dump(exclude_none=True), ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ============================================================
# Tasks CRUD
# ============================================================


@router.post("/tasks/{task_id}/cancel")
async def cancel_task(
    task_id: str,
    session: AsyncSession = Depends(get_session),
) -> dict[str, str]:
    """Interrompt réellement une mission locale encore en cours."""
    result = await session.execute(select(AgentTask).where(AgentTask.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Tâche introuvable")
    if task.status not in {"pending", "in_progress"}:
        raise HTTPException(
            status_code=400,
            detail=f"La tâche en statut '{task.status}' n'est plus annulable.",
        )

    running_task = _running_agent_tasks.get(task_id)
    if running_task is None or running_task.done():
        raise HTTPException(
            status_code=409,
            detail="Le processus de cette mission n'est plus actif. Recharge son statut.",
        )
    # 0.46 : le Stop historique passe par le service canonique quand le
    # traitement existe - même transition cancel_requested, même adaptateur
    # (.cancel() de l'asyncio.Task), un seul chemin d'annulation. Repli sur
    # le cancel direct si le suivi n'a pas pu naître.
    from app.models.database import get_session_context as _ctx
    from app.models.processing import EtatTache as _Etat
    from app.models.processing import ProcessingTask as _PT
    from app.services import traitements as _traitements
    from sqlmodel import select as _select

    async with _ctx() as _session:
        _r = await _session.execute(
            _select(_PT).where(
                _PT.type == "atelier",
                _PT.entity_id == task_id,
                _PT.state.in_(tuple(_Etat.actifs())),
            )
        )
        _traitement = _r.scalars().first()
    if _traitement is not None:
        await _traitements.demander_arret(_traitement.id)
    else:
        running_task.cancel()
    return {"status": "cancelling", "task_id": task_id}


@router.get("/tasks")
async def list_tasks(
    limit: int = 50,
    status: str | None = None,
    session: AsyncSession = Depends(get_session),
) -> AgentTaskListResponse:
    """Liste les tâches agents."""
    query = select(AgentTask).order_by(AgentTask.created_at.desc()).limit(limit)
    # B-102 : le compte porte le MEME filtre que les lignes. Sans lui, une
    # liste filtree annoncait un total que la liste ne montrait pas.
    count_query = select(func.count(AgentTask.id))
    if status:
        query = query.where(AgentTask.status == status)
        count_query = count_query.where(AgentTask.status == status)

    result = await session.execute(query)
    tasks = result.scalars().all()

    count_result = await session.execute(count_query)
    total = count_result.scalar() or 0

    return AgentTaskListResponse(
        tasks=[_task_to_response(t) for t in tasks],
        total=total,
    )


@router.get("/tasks/{task_id}")
async def get_task(
    task_id: str,
    session: AsyncSession = Depends(get_session),
) -> AgentTaskResponse:
    """Détail d'une tâche agent."""
    result = await session.execute(select(AgentTask).where(AgentTask.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Tâche introuvable")
    return _task_to_response(task)


@router.get("/tasks/{task_id}/diff")
async def get_task_diff(
    task_id: str,
    session: AsyncSession = Depends(get_session),
) -> DiffResponse:
    """Récupère le diff complet d'une tâche pour review."""
    result = await session.execute(select(AgentTask).where(AgentTask.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Tâche introuvable")
    if not task.branch_name or not task.source_path:
        raise HTTPException(status_code=400, detail="Pas de branche associée à cette tâche")

    git = GitService(task.source_path)

    # Obtenir le diff par fichier
    files = await git.diff_files(base="main", head=task.branch_name)
    diff_files = []
    total_add = 0
    total_del = 0

    for f in files:
        file_diff = await git.diff_file(
            f["file_path"], base="main", head=task.branch_name
        )
        # Compter les lignes ajoutées/supprimées
        adds = sum(
            1
            for line in file_diff.split("\n")
            if line.startswith("+") and not line.startswith("+++")
        )
        dels = sum(
            1
            for line in file_diff.split("\n")
            if line.startswith("-") and not line.startswith("---")
        )
        total_add += adds
        total_del += dels

        diff_files.append(
            DiffFileResponse(
                file_path=f["file_path"],
                change_type=f["change_type"],
                diff_hunk=file_diff,
                additions=adds,
                deletions=dels,
            )
        )

    return DiffResponse(
        task_id=task_id,
        branch_name=task.branch_name,
        summary=task.diff_summary,
        files=diff_files,
        total_additions=total_add,
        total_deletions=total_del,
    )


# ============================================================
# Review actions
# ============================================================


@router.post("/tasks/{task_id}/approve")
async def approve_task(
    task_id: str,
    session: AsyncSession = Depends(get_session),
):
    """Approuve et merge la branche d'une tâche."""
    result = await session.execute(select(AgentTask).where(AgentTask.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Tâche introuvable")
    if task.status != "review":
        raise HTTPException(
            status_code=400, detail=f"Tâche en statut '{task.status}', attendu 'review'"
        )
    if not task.branch_name or not task.source_path:
        raise HTTPException(status_code=400, detail="Pas de branche à merger")
    if not task.branch_name.startswith("agent/"):
        raise HTTPException(status_code=400, detail="Branche Atelier invalide")

    git = GitService(task.source_path)
    if await git.current_branch() != "main":
        raise HTTPException(
            status_code=409,
            detail="Reviens sur la branche main avant d'appliquer les changements.",
        )
    if not await git.ensure_clean():
        raise HTTPException(
            status_code=409,
            detail="Le dépôt contient des changements non enregistrés.",
        )

    # Merge la branche
    success = await git.merge(task.branch_name, into="main")
    if not success:
        raise HTTPException(status_code=500, detail="Échec du merge. Vérifie les conflits.")

    # Supprimer la branche
    await git.delete_branch(task.branch_name)

    # Mettre à jour la tâche
    task.status = "merged"
    task.merged_at = datetime.now(UTC)
    task.updated_at = datetime.now(UTC)
    await session.commit()

    return {"status": "merged", "task_id": task_id}


@router.post("/tasks/{task_id}/reject")
async def reject_task(
    task_id: str,
    session: AsyncSession = Depends(get_session),
):
    """Rejette et supprime la branche d'une tâche."""
    result = await session.execute(select(AgentTask).where(AgentTask.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Tâche introuvable")
    if task.status != "review":
        raise HTTPException(status_code=400, detail=f"Tâche en statut '{task.status}'")

    if task.branch_name and task.source_path:
        if not task.branch_name.startswith("agent/"):
            raise HTTPException(status_code=400, detail="Branche Atelier invalide")
        git = GitService(task.source_path)
        if not await git.delete_branch(task.branch_name):
            raise HTTPException(status_code=500, detail="Impossible de supprimer la branche Atelier")

    task.status = "rejected"
    task.updated_at = datetime.now(UTC)
    await session.commit()

    return {"status": "rejected", "task_id": task_id}


@router.post("/tasks/{task_id}/rollback")
async def rollback_task(
    task_id: str,
    session: AsyncSession = Depends(get_session),
):
    """Annule un merge précédent via git revert."""
    result = await session.execute(select(AgentTask).where(AgentTask.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Tâche introuvable")
    if task.status != "merged":
        raise HTTPException(
            status_code=400, detail="Seules les tâches mergées peuvent être annulées"
        )
    if not task.source_path:
        raise HTTPException(status_code=400, detail="Chemin source manquant")

    git = GitService(task.source_path)
    if await git.current_branch() != "main":
        raise HTTPException(
            status_code=409,
            detail="Reviens sur la branche main avant d'annuler les changements.",
        )
    if not await git.ensure_clean():
        raise HTTPException(
            status_code=409,
            detail="Le dépôt contient des changements non enregistrés.",
        )

    # Le nom de branche contient l'identifiant unique de la tâche et reste
    # enregistré en base, même après suppression de la branche locale.
    merge_commit = (
        await git.find_merge_commit(task.branch_name) if task.branch_name else None
    )

    if not merge_commit:
        raise HTTPException(status_code=400, detail="Commit de merge introuvable")

    success = await git.rollback(merge_commit)
    if not success:
        raise HTTPException(status_code=500, detail="Échec du rollback")

    task.status = "rejected"
    task.updated_at = datetime.now(UTC)
    await session.commit()

    return {"status": "rolled_back", "task_id": task_id}


# ============================================================
# Configuration
# ============================================================


@router.get("/config")
async def get_config(
    session: AsyncSession = Depends(get_session),
) -> AgentConfigResponse:
    """Récupère la configuration des agents avec les modèles disponibles."""
    from app.models.entities import Preference
    from app.models.schemas_agents import AgentModelInfo
    from app.services.agents.config import AVAILABLE_MODELS

    source_path = _get_source_path()

    # Lire les modèles choisis en DB. BUG-149 : la clé LEGACY
    # agent_therese_model est lue EN PREMIER pour ne servir que de repli -
    # lue après, elle écrasait la sélection agent_katia_model à chaque
    # lecture (l'Atelier réaffichait l'ancien modèle malgré la sauvegarde).
    katia_model = "claude-sonnet-4-6"
    zezette_model = "claude-sonnet-4-6"
    for key in ("agent_therese_model", "agent_katia_model", "agent_zezette_model"):
        result = await session.execute(select(Preference).where(Preference.key == key))
        pref = result.scalar_one_or_none()
        if pref and pref.value:
            if key in ("agent_katia_model", "agent_therese_model"):
                katia_model = pref.value
            else:
                zezette_model = pref.value

    # Filtrer les modeles par providers ayant une cle API configuree
    import os
    import shutil

    from app.services.llm import _get_api_key_from_db

    configured_providers: set[str] = set()
    provider_env_map = {
        "anthropic": "ANTHROPIC_API_KEY",
        "openai": "OPENAI_API_KEY",
        "gemini": "GEMINI_API_KEY",
        "mistral": "MISTRAL_API_KEY",
        "grok": "GROK_API_KEY",
        "openrouter": "OPENROUTER_API_KEY",
        "deepseek": "DEEPSEEK_API_KEY",
    }
    for provider_name, env_var in provider_env_map.items():
        if _get_api_key_from_db(provider_name) or os.environ.get(env_var):
            configured_providers.add(provider_name)

    # Ollama toujours disponible si le binaire existe
    if shutil.which("ollama"):
        configured_providers.add("ollama")

    # Si aucun provider configure, montrer tous les modeles (premier lancement)
    if configured_providers:
        filtered_models = [m for m in AVAILABLE_MODELS if m["provider"] in configured_providers]
    else:
        filtered_models = AVAILABLE_MODELS

    return AgentConfigResponse(
        source_path=source_path,
        katia_model=katia_model,
        zezette_model=zezette_model,
        available_models=[AgentModelInfo(**m) for m in filtered_models],
    )


@router.put("/config")
async def update_config(
    config: AgentConfigUpdate,
    session: AsyncSession = Depends(get_session),
) -> AgentConfigResponse:
    """Met à jour la configuration des agents."""
    from app.models.entities import Preference

    # Persister chaque paramètre en DB
    updates = {}
    if config.source_path:
        updates["agent_source_path"] = config.source_path
    if config.katia_model:
        updates["agent_katia_model"] = config.katia_model
    if config.zezette_model:
        updates["agent_zezette_model"] = config.zezette_model

    for key, value in updates.items():
        result = await session.execute(select(Preference).where(Preference.key == key))
        pref = result.scalar_one_or_none()
        if pref:
            pref.value = value
        else:
            session.add(Preference(key=key, value=value))

    # BUG-149 : assainir la clé LEGACY dès qu'un modèle Katia est choisi,
    # sinon elle resterait en base comme repli fantôme.
    if "agent_katia_model" in updates:
        result = await session.execute(
            select(Preference).where(Preference.key == "agent_therese_model")
        )
        legacy = result.scalar_one_or_none()
        if legacy:
            await session.delete(legacy)

    if updates:
        await session.commit()

    return await get_config(session)


# ============================================================
# Status
# ============================================================


@router.get("/status")
async def get_status(
    session: AsyncSession = Depends(get_session),
) -> AgentStatusResponse:
    """Vérifie le statut du système d'agents."""
    import shutil

    git_available = shutil.which("git") is not None
    source_path = _get_source_path()
    # BUG-163, contre-vérification : `False` affirmait l'absence de dépôt
    # AVANT même que le contrôle ait tourné. Quand git est introuvable ou
    # qu'aucun chemin n'est résolu, le bloc de vérification n'est pas exécuté
    # et la réponse partait quand même avec « dépôt absent » — deux croix
    # rouges pour un seul fait établi. C'est ce chemin, et non le timeout git,
    # qui est réellement atteignable depuis cet écran.
    repo_detected: bool | None = None
    current_branch = None
    repo_error = None
    working_tree_clean = None

    if source_path and git_available:
        git = GitService(source_path)
        repo_detected = await git.is_repo()
        if repo_detected:
            current_branch = await git.current_branch()
            working_tree_clean = await git.ensure_clean()
        elif repo_detected is None:
            # BUG-163 : git n'a pas répondu. On ne sait rien, donc on n'affirme
            # rien. La version précédente servait ici le message qui prescrit un
            # reclonage, et envoyait le testeur réparer un dépôt intact.
            repo_error = (
                "La vérification du dépôt n'a pas abouti : Git n'a pas répondu "
                "dans le temps imparti. Ton dépôt n'est pas forcément en cause. "
                "Réessaie dans un instant."
            )
        else:
            repo_error = repo_error_message(source_path)
    elif source_path and not git_available:
        # `git_available` est mesuré sur le PATH hérité au démarrage du backend.
        # Un testeur qui installe Git pendant que THÉRÈSE tourne garde un
        # environnement périmé jusqu'à la fermeture, et retrouve un statut sain
        # au lancement suivant : c'est l'explication la plus probable d'une
        # erreur « disparue toute seule ». Le message le dit désormais.
        repo_error = (
            "Git est introuvable dans le PATH de l'application. Le dépôt n'a "
            "donc pas pu être vérifié. Si tu viens d'installer Git, redémarre "
            "THÉRÈSE pour qu'elle prenne en compte le nouvel environnement."
        )
    elif not source_path:
        repo_error = (
            "Aucun chemin de code source n'a pu être résolu, le dépôt n'a donc "
            "pas été vérifié. Renseigne le dossier du code dans les réglages, "
            "ou réessaie si le dossier est sur un disque externe ou un espace "
            "synchronisé qui n'était pas encore disponible."
        )


    # Compter les tâches actives
    result = await session.execute(
        select(func.count(AgentTask.id)).where(
            AgentTask.status.in_(["pending", "in_progress"])
        )
    )
    active_tasks = result.scalar() or 0

    # Vérifier que les configs agents existent
    katia_ready = False
    zezette_ready = False
    try:
        from app.services.agents.config import load_agent_config

        load_agent_config("katia")
        katia_ready = True
    except Exception as e:
        logger.debug("Agent config non disponible: %s", e)
    try:
        from app.services.agents.config import load_agent_config

        load_agent_config("zezette")
        zezette_ready = True
    except Exception as e:
        logger.debug("Agent config non disponible: %s", e)

    return AgentStatusResponse(
        git_available=git_available,
        repo_detected=repo_detected,
        repo_path=source_path,
        repo_error=repo_error,
        current_branch=current_branch,
        working_tree_clean=working_tree_clean,
        active_tasks=active_tasks,
        katia_ready=katia_ready,
        zezette_ready=zezette_ready,
    )


# ============================================================
# Helpers
# ============================================================


def _task_to_response(task: AgentTask) -> AgentTaskResponse:
    """Convertit un AgentTask en réponse API."""
    files = None
    if task.files_changed:
        try:
            files = json.loads(task.files_changed)
        except json.JSONDecodeError:
            files = None

    def json_value(raw: str | None, fallback: Any) -> Any:
        if not raw:
            return fallback
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return fallback

    return AgentTaskResponse(
        id=task.id,
        title=task.title,
        description=task.description,
        status=task.status,
        branch_name=task.branch_name,
        diff_summary=task.diff_summary,
        files_changed=files,
        agent_model=task.agent_model,
        tokens_used=task.tokens_used,
        cost_eur=task.cost_eur,
        run_phase=task.run_phase,
        plan=task.plan,
        test_results=json_value(task.test_results, []),
        explanation=task.explanation,
        events=json_value(task.events, []),
        agent_outputs=json_value(task.agent_outputs, {}),
        base_branch=task.base_branch,
        commit_hash=task.commit_hash,
        error=task.error,
        created_at=task.created_at,
        updated_at=task.updated_at,
        merged_at=task.merged_at,
    )


# ============================================================
# OpenClaw Integration (US-001)
# ============================================================


@router.post("/dispatch")
async def dispatch_to_openclaw(
    request: DispatchRequest,
    http_request: Request,
    session: AsyncSession = Depends(get_session),
):
    """Lance un agent OpenClaw depuis l Atelier.

    Crée une AgentSession en DB et spawn une session OpenClaw.
    Limite le nombre d agents en parallèle (US-003).
    """
    from app.services.openclaw_bridge import spawn_session

    # US-003 : vérifier la limite d agents en parallèle
    running_count_result = await session.execute(
        select(func.count(AgentSession.id)).where(AgentSession.status == "running")
    )
    running_count = running_count_result.scalar() or 0

    if running_count >= _MAX_OPENCLAW_AGENTS:
        raise HTTPException(
            status_code=429,
            detail=f"Tu as déjà {running_count} agents en cours. Attends qu un se termine ou annule-en un.",
        )

    # Vérifier la connexion OpenClaw
    from app.services.openclaw_bridge import check_connection

    connected = await check_connection()
    if not connected:
        raise HTTPException(
            status_code=503,
            detail="OpenClaw n'est pas accessible. Vérifie que le gateway tourne sur le port 18789.",
        )

    # Créer la session en DB
    agent_session = AgentSession(
        agent_name=request.agent_name,
        instruction=request.instruction,
    )
    session.add(agent_session)
    await session.commit()
    await session.refresh(agent_session)

    # Spawn la session OpenClaw avec le MCP bridge
    mcp_config = {
        "therese-bridge": {
            "command": "python3",
            "args": ["-m", "app.services.mcp_therese_server"],
            "env": {
                "THERESE_API_URL": "http://127.0.0.1:17293",
                "THERESE_MCP_TOKEN": getattr(
                    http_request.app.state, "session_token", ""
                ),
            },
        }
    }

    result = await spawn_session(
        agent_name=request.agent_name,
        instruction=request.instruction,
        mcp_config=mcp_config,
    )

    if "error" in result:
        agent_session.status = "error"
        agent_session.result_summary = result["error"]
        session.add(agent_session)
        await session.commit()
        raise HTTPException(status_code=502, detail=result["error"])

    # Mettre à jour avec l ID de session OpenClaw
    openclaw_id = result.get("session_id") or result.get("id", "")
    agent_session.openclaw_session_id = openclaw_id
    session.add(agent_session)
    await session.commit()
    await session.refresh(agent_session)

    return AgentSessionResponse(
        id=agent_session.id,
        agent_name=agent_session.agent_name,
        instruction=agent_session.instruction,
        status=agent_session.status,
        openclaw_session_id=agent_session.openclaw_session_id,
        created_at=agent_session.created_at,
        finished_at=agent_session.finished_at,
        result_summary=agent_session.result_summary,
        actions_count=agent_session.actions_count,
    )


@router.get("/sessions")
async def list_openclaw_sessions(
    limit: int = 50,
    status: str | None = None,
    session: AsyncSession = Depends(get_session),
):
    """Liste les sessions OpenClaw."""

    query = select(AgentSession).order_by(AgentSession.created_at.desc()).limit(limit)
    # B-102 : meme invariant que /tasks - le total suit le filtre de statut.
    count_query = select(func.count(AgentSession.id))
    if status:
        query = query.where(AgentSession.status == status)
        count_query = count_query.where(AgentSession.status == status)

    result = await session.execute(query)
    sessions_list = result.scalars().all()

    count_result = await session.execute(count_query)
    total = count_result.scalar() or 0

    return AgentSessionListResponse(
        sessions=[
            AgentSessionResponse(
                id=s.id,
                agent_name=s.agent_name,
                instruction=s.instruction,
                status=s.status,
                openclaw_session_id=s.openclaw_session_id,
                created_at=s.created_at,
                finished_at=s.finished_at,
                result_summary=s.result_summary,
                actions_count=s.actions_count,
            )
            for s in sessions_list
        ],
        total=total,
    )


@router.get("/sessions/{session_id}")
async def get_openclaw_session(
    session_id: str,
    session: AsyncSession = Depends(get_session),
):
    """Détail d une session OpenClaw."""

    result = await session.execute(select(AgentSession).where(AgentSession.id == session_id))
    agent_session = result.scalar_one_or_none()
    if not agent_session:
        raise HTTPException(status_code=404, detail="Session introuvable")

    # Synchroniser le statut avec OpenClaw si running
    if agent_session.openclaw_session_id and agent_session.status == "running":
        from app.services.openclaw_bridge import get_session_status

        oc_status = await get_session_status(agent_session.openclaw_session_id)
        if "error" not in oc_status:
            new_status = oc_status.get("status", agent_session.status)
            if new_status != agent_session.status:
                agent_session.status = new_status
                if new_status in ("done", "error"):
                    from datetime import UTC, datetime

                    agent_session.finished_at = datetime.now(UTC)
                session.add(agent_session)
                await session.commit()
                await session.refresh(agent_session)

    return AgentSessionResponse(
        id=agent_session.id,
        agent_name=agent_session.agent_name,
        instruction=agent_session.instruction,
        status=agent_session.status,
        openclaw_session_id=agent_session.openclaw_session_id,
        created_at=agent_session.created_at,
        finished_at=agent_session.finished_at,
        result_summary=agent_session.result_summary,
        actions_count=agent_session.actions_count,
    )


@router.get("/sessions/{session_id}/messages")
async def get_openclaw_session_messages(
    session_id: str,
    session: AsyncSession = Depends(get_session),
):
    """Messages d une session OpenClaw."""

    result = await session.execute(select(AgentSession).where(AgentSession.id == session_id))
    agent_session = result.scalar_one_or_none()
    if not agent_session:
        raise HTTPException(status_code=404, detail="Session introuvable")

    if not agent_session.openclaw_session_id:
        return []

    from app.services.openclaw_bridge import get_session_messages

    messages = await get_session_messages(agent_session.openclaw_session_id)
    return [
        SessionMessageResponse(
            role=m.get("role", "assistant"),
            content=m.get("content", ""),
            timestamp=m.get("timestamp") or m.get("created_at"),
        )
        for m in messages
    ]


@router.post("/sessions/{session_id}/send")
async def send_to_openclaw_session(
    session_id: str,
    request: SendMessageRequest,
    session: AsyncSession = Depends(get_session),
):
    """Envoie un message à un agent dans une session OpenClaw."""

    result = await session.execute(select(AgentSession).where(AgentSession.id == session_id))
    agent_session = result.scalar_one_or_none()
    if not agent_session:
        raise HTTPException(status_code=404, detail="Session introuvable")
    if agent_session.status != "running":
        raise HTTPException(
            status_code=400, detail=f"Session en statut {agent_session.status}, pas running"
        )
    if not agent_session.openclaw_session_id:
        raise HTTPException(status_code=400, detail="Pas de session OpenClaw associée")

    from app.services.openclaw_bridge import send_message

    response = await send_message(agent_session.openclaw_session_id, request.content)

    if "error" in response:
        raise HTTPException(status_code=502, detail=response["error"])

    # Incrémenter le compteur d actions
    agent_session.actions_count += 1
    session.add(agent_session)
    await session.commit()

    return response


@router.post("/sessions/{session_id}/cancel")
async def cancel_openclaw_session(
    session_id: str,
    session: AsyncSession = Depends(get_session),
):
    """Annule une session OpenClaw."""

    result = await session.execute(select(AgentSession).where(AgentSession.id == session_id))
    agent_session = result.scalar_one_or_none()
    if not agent_session:
        raise HTTPException(status_code=404, detail="Session introuvable")
    if agent_session.status != "running":
        raise HTTPException(
            status_code=400, detail=f"Session en statut {agent_session.status}, pas running"
        )

    # Annuler dans OpenClaw
    if agent_session.openclaw_session_id:
        from app.services.openclaw_bridge import cancel_session

        cancelled = await cancel_session(agent_session.openclaw_session_id)
        if not cancelled:
            raise HTTPException(
                status_code=502,
                detail="OpenClaw n'a pas confirmé l'annulation de la session.",
            )

    from datetime import UTC, datetime

    agent_session.status = "cancelled"
    agent_session.finished_at = datetime.now(UTC)
    session.add(agent_session)
    await session.commit()

    return {"status": "cancelled", "session_id": session_id}


@router.get("/sessions/running/count")
async def get_running_sessions_count(
    session: AsyncSession = Depends(get_session),
):
    """Retourne le nombre de sessions en cours (US-003)."""

    result = await session.execute(
        select(func.count(AgentSession.id)).where(AgentSession.status == "running")
    )
    count = result.scalar() or 0
    return {"running_count": count, "max_agents": 3}


@router.get("/openclaw/status")
async def get_openclaw_status():
    """Vérifie la connexion OpenClaw et liste les agents disponibles."""
    from app.services.openclaw_bridge import OPENCLAW_API_URL, check_connection, list_agents

    connected = await check_connection()
    agents = []
    if connected:
        agents = await list_agents()

    return OpenClawStatusResponse(
        connected=connected,
        agents=agents,
        url=OPENCLAW_API_URL,
    )
