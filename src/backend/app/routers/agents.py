"""
THÉRÈSE v2 - Agents Router

Endpoints pour le système d'agents IA embarqués (Atelier).
"""

import json
import logging
from datetime import UTC, datetime

from app.models.database import get_session
from app.models.entities_agents import AgentMessage, AgentTask
from app.models.schemas_agents import (
    AgentConfigResponse,
    AgentConfigUpdate,
    AgentRequest,
    AgentStatusResponse,
    AgentStreamChunk,
    AgentTaskListResponse,
    AgentTaskResponse,
    DiffFileResponse,
    DiffResponse,
)
from app.services.agents.git_service import GitService
from app.services.agents.swarm import SwarmOrchestrator
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import func, select

logger = logging.getLogger(__name__)

router = APIRouter()


def _get_source_path() -> str | None:
    """Récupère le chemin du source configuré.

    Priorité : DB > env var > auto-détection.
    """
    import os
    from pathlib import Path

    # 1. Préférence en DB (configurée via l'onglet Agents dans les paramètres)
    try:
        import sqlite3

        from app.config import settings

        db_path = settings.db_path
        if db_path and Path(db_path).exists():
            conn = sqlite3.connect(str(db_path))
            cursor = conn.execute(
                "SELECT value FROM preferences WHERE key = 'agent_source_path'"
            )
            row = cursor.fetchone()
            conn.close()
            if row and row[0]:
                p = Path(row[0])
                if p.exists() and (p / ".git").exists():
                    return str(p)
    except Exception:
        pass

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
        home / "Developer" / "Synoptia-THERESE",
        home / "Desktop" / "Dev Synoptia" / "THERESE V2",
        home / "repos" / "Synoptia-THERESE",
        home / "Documents" / "Synoptia-THERESE",
    ]
    for candidate in known_paths:
        if candidate.exists() and (candidate / ".git").exists() and (candidate / "src" / "backend").exists():
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


# ============================================================
# Streaming endpoint
# ============================================================


@router.post("/request")
async def agent_request(
    request: AgentRequest,
    session: AsyncSession = Depends(get_session),
):
    """Soumet une demande au swarm d'agents. Retourne un stream SSE."""
    source_path = request.source_path or _get_source_path()
    if not source_path:
        raise HTTPException(
            status_code=400,
            detail="Chemin du code source non configuré. Configurez THERESE_SOURCE_PATH ou passez source_path.",
        )

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
        orchestrator = SwarmOrchestrator(source_path)
        final_status = "review"
        branch_name = None
        files_changed = []
        diff_summary = ""

        try:
            async for chunk in orchestrator.process_request(request.message, task.id):
                # Mettre à jour la tâche selon les événements
                if chunk.type == "review_ready":
                    branch_name = chunk.branch
                    files_changed = chunk.files_changed or []
                    diff_summary = chunk.diff_summary or ""
                elif chunk.type == "error":
                    final_status = "pending"
                elif chunk.type == "done":
                    if chunk.phase == "done":
                        final_status = "done"
                    elif chunk.phase == "review":
                        final_status = "review"
                    else:
                        final_status = "pending"

                # Émettre le chunk SSE
                data = chunk.model_dump(exclude_none=True)
                yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"

        except Exception as e:
            logger.error(f"Erreur swarm: {e}", exc_info=True)
            error_chunk = AgentStreamChunk(
                type="error",
                content=f"Erreur inattendue : {e}",
                task_id=task.id,
            )
            yield f"data: {json.dumps(error_chunk.model_dump(exclude_none=True), ensure_ascii=False)}\n\n"
            final_status = "pending"

        # Mettre à jour la tâche finale
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
                    db_task.files_changed = json.dumps(files_changed, ensure_ascii=False) if files_changed else None
                    db_task.diff_summary = diff_summary
                    db_task.updated_at = datetime.now(UTC)
                    await update_session.commit()
        except Exception as e:
            logger.error(f"Erreur mise à jour tâche: {e}")

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


@router.get("/tasks")
async def list_tasks(
    limit: int = 50,
    status: str | None = None,
    session: AsyncSession = Depends(get_session),
) -> AgentTaskListResponse:
    """Liste les tâches agents."""
    query = select(AgentTask).order_by(AgentTask.created_at.desc()).limit(limit)
    if status:
        query = query.where(AgentTask.status == status)

    result = await session.execute(query)
    tasks = result.scalars().all()

    count_result = await session.execute(select(func.count(AgentTask.id)))
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
    result = await session.execute(
        select(AgentTask).where(AgentTask.id == task_id)
    )
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
    result = await session.execute(
        select(AgentTask).where(AgentTask.id == task_id)
    )
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Tâche introuvable")
    if not task.branch_name or not task.source_path:
        raise HTTPException(status_code=400, detail="Pas de branche associée à cette tâche")

    git = GitService(task.source_path)

    # Obtenir le diff par fichier
    files = await git.diff_files(base="main")
    diff_files = []
    total_add = 0
    total_del = 0

    for f in files:
        file_diff = await git.diff_file(f["file_path"], base="main")
        # Compter les lignes ajoutées/supprimées
        adds = sum(1 for line in file_diff.split("\n") if line.startswith("+") and not line.startswith("+++"))
        dels = sum(1 for line in file_diff.split("\n") if line.startswith("-") and not line.startswith("---"))
        total_add += adds
        total_del += dels

        diff_files.append(DiffFileResponse(
            file_path=f["file_path"],
            change_type=f["change_type"],
            diff_hunk=file_diff,
            additions=adds,
            deletions=dels,
        ))

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
    result = await session.execute(
        select(AgentTask).where(AgentTask.id == task_id)
    )
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Tâche introuvable")
    if task.status != "review":
        raise HTTPException(status_code=400, detail=f"Tâche en statut '{task.status}', attendu 'review'")
    if not task.branch_name or not task.source_path:
        raise HTTPException(status_code=400, detail="Pas de branche à merger")

    git = GitService(task.source_path)

    # Merge la branche
    success = await git.merge(task.branch_name, into="main")
    if not success:
        raise HTTPException(status_code=500, detail="Échec du merge. Vérifiez les conflits.")

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
    result = await session.execute(
        select(AgentTask).where(AgentTask.id == task_id)
    )
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Tâche introuvable")
    if task.status not in ("review", "in_progress"):
        raise HTTPException(status_code=400, detail=f"Tâche en statut '{task.status}'")

    if task.branch_name and task.source_path:
        git = GitService(task.source_path)
        current = await git.current_branch()
        if current == task.branch_name:
            await git.checkout("main")
        await git.delete_branch(task.branch_name)

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
    result = await session.execute(
        select(AgentTask).where(AgentTask.id == task_id)
    )
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Tâche introuvable")
    if task.status != "merged":
        raise HTTPException(status_code=400, detail="Seules les tâches mergées peuvent être annulées")
    if not task.source_path:
        raise HTTPException(status_code=400, detail="Chemin source manquant")

    git = GitService(task.source_path)

    # Trouver le dernier commit de merge
    commits = await git.log(limit=5)
    merge_commit = None
    for c in commits:
        if task.branch_name and task.branch_name in c.get("message", ""):
            merge_commit = c["hash"]
            break

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

    # Lire les modèles choisis en DB (avec fallback sur les anciennes clés "therese")
    katia_model = "claude-sonnet-4-6"
    zezette_model = "claude-sonnet-4-6"
    for key in ("agent_katia_model", "agent_therese_model", "agent_zezette_model"):
        result = await session.execute(
            select(Preference).where(Preference.key == key)
        )
        pref = result.scalar_one_or_none()
        if pref and pref.value:
            if key in ("agent_katia_model", "agent_therese_model"):
                katia_model = pref.value
            else:
                zezette_model = pref.value

    return AgentConfigResponse(
        source_path=source_path,
        katia_model=katia_model,
        zezette_model=zezette_model,
        available_models=[AgentModelInfo(**m) for m in AVAILABLE_MODELS],
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
        result = await session.execute(
            select(Preference).where(Preference.key == key)
        )
        pref = result.scalar_one_or_none()
        if pref:
            pref.value = value
        else:
            session.add(Preference(key=key, value=value))

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
    repo_detected = False
    current_branch = None

    if source_path and git_available:
        git = GitService(source_path)
        repo_detected = await git.is_repo()
        if repo_detected:
            current_branch = await git.current_branch()

    # Compter les tâches actives
    result = await session.execute(
        select(func.count(AgentTask.id)).where(
            AgentTask.status.in_(["pending", "in_progress", "review"])
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
    except Exception:
        pass
    try:
        from app.services.agents.config import load_agent_config
        load_agent_config("zezette")
        zezette_ready = True
    except Exception:
        pass

    return AgentStatusResponse(
        git_available=git_available,
        repo_detected=repo_detected,
        repo_path=source_path,
        current_branch=current_branch,
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
        error=task.error,
        created_at=task.created_at,
        updated_at=task.updated_at,
        merged_at=task.merged_at,
    )
