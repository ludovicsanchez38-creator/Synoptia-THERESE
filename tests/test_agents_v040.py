"""Garanties de sûreté et de vérité de l'Atelier 0.40."""

import asyncio
import subprocess
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from app.models.entities_agents import AgentSession, AgentTask
from app.models.schemas_agents import AgentStreamChunk
from app.routers import agents as agents_router
from app.services.agents.git_service import GitService
from app.services.agents.tools import AgentToolExecutor
from app.services.mcp_therese_server import execute_tool
from fastapi import HTTPException


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _init_repo(repo: Path) -> None:
    repo.mkdir()
    subprocess.run(
        ["git", "init", "-b", "main", str(repo)],
        check=True,
        capture_output=True,
    )
    _git(repo, "config", "user.email", "atelier@test.local")
    _git(repo, "config", "user.name", "Atelier Test")
    (repo / "README.md").write_text("initial\n", encoding="utf-8")
    _git(repo, "add", "README.md")
    _git(repo, "commit", "-m", "Initial")


def test_local_prototype_origin_is_allowed_outside_production() -> None:
    from app.main import _cors_origins

    assert "http://127.0.0.1:1420" in _cors_origins


def test_validate_path_refuses_prefix_escape_absolute_symlink_and_secrets(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    sibling = tmp_path / "repo-escape"
    repo.mkdir()
    sibling.mkdir()
    (sibling / "secret.txt").write_text("secret", encoding="utf-8")
    (repo / "outside-link").symlink_to(sibling, target_is_directory=True)
    executor = AgentToolExecutor(str(repo))

    for unsafe_path in (
        "../repo-escape/secret.txt",
        str(sibling / "secret.txt"),
        "outside-link/secret.txt",
        ".env",
        ".git/config",
        "certificat.pem",
    ):
        with pytest.raises(PermissionError):
            executor._validate_path(unsafe_path)


@pytest.mark.asyncio
async def test_run_command_refuses_direct_code_and_free_form_scripts(
    tmp_path: Path,
) -> None:
    executor = AgentToolExecutor(str(tmp_path))

    assert "non autorisée" in await executor.run_command("python -c print(1)")
    assert "non autorisé" in await executor.run_command("npm run arbitrary")
    assert "sous-commande" in await executor.run_command("make")


@pytest.mark.asyncio
async def test_git_worktree_keeps_user_checkout_untouched_and_diff_uses_task_branch(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    worktree = tmp_path / "agent-worktree"
    _init_repo(repo)
    root_git = GitService(repo)

    assert await root_git.create_worktree(worktree, "agent/test-isolation", "main")
    agent_git = GitService(worktree)
    (worktree / "README.md").write_text("initial\nmission\n", encoding="utf-8")
    assert await agent_git.commit("[agent] isolation")

    assert await root_git.current_branch() == "main"
    assert await root_git.ensure_clean()
    assert await root_git.diff_files(
        base="main", head="agent/test-isolation"
    ) == [{"file_path": "README.md", "change_type": "modified"}]
    assert await root_git.remove_worktree(worktree)
    assert not worktree.exists()
    assert "agent/test-isolation" in _git(repo, "branch", "--list")


@pytest.mark.asyncio
async def test_get_task_diff_reads_the_persisted_agent_branch(db_session) -> None:
    task = AgentTask(
        title="Mission",
        status="review",
        source_path="/tmp/repo",
        branch_name="agent/mission-123",
        diff_summary="1 file changed",
    )
    db_session.add(task)
    await db_session.commit()

    git = MagicMock()
    git.diff_files = AsyncMock(
        return_value=[{"file_path": "src/app.ts", "change_type": "modified"}]
    )
    git.diff_file = AsyncMock(return_value="--- a/src/app.ts\n+++ b/src/app.ts\n-old\n+new")

    with patch("app.routers.agents.GitService", return_value=git):
        response = await agents_router.get_task_diff(task.id, db_session)

    git.diff_files.assert_awaited_once_with(base="main", head="agent/mission-123")
    git.diff_file.assert_awaited_once_with(
        "src/app.ts", base="main", head="agent/mission-123"
    )
    assert response.total_additions == 1
    assert response.total_deletions == 1


@pytest.mark.asyncio
async def test_approve_refuses_a_dirty_user_worktree(db_session) -> None:
    task = AgentTask(
        title="Mission",
        status="review",
        source_path="/tmp/repo",
        branch_name="agent/mission-123",
    )
    db_session.add(task)
    await db_session.commit()

    git = MagicMock()
    git.current_branch = AsyncMock(return_value="main")
    git.ensure_clean = AsyncMock(return_value=False)
    git.merge = AsyncMock(return_value=True)

    with (
        patch("app.routers.agents.GitService", return_value=git),
        pytest.raises(HTTPException) as exc_info,
    ):
        await agents_router.approve_task(task.id, db_session)

    assert exc_info.value.status_code == 409
    git.merge.assert_not_awaited()


@pytest.mark.asyncio
async def test_reject_does_not_claim_success_when_branch_deletion_fails(
    db_session,
) -> None:
    task = AgentTask(
        title="Mission",
        status="review",
        source_path="/tmp/repo",
        branch_name="agent/mission-123",
    )
    db_session.add(task)
    await db_session.commit()

    git = MagicMock()
    git.delete_branch = AsyncMock(return_value=False)

    with (
        patch("app.routers.agents.GitService", return_value=git),
        pytest.raises(HTTPException) as exc_info,
    ):
        await agents_router.reject_task(task.id, db_session)

    assert exc_info.value.status_code == 500
    await db_session.refresh(task)
    assert task.status == "review"


@pytest.mark.asyncio
async def test_cancel_endpoint_cancels_the_registered_backend_task(db_session) -> None:
    task = AgentTask(title="Mission", status="in_progress", source_path="/tmp/repo")
    db_session.add(task)
    await db_session.commit()
    running = asyncio.create_task(asyncio.sleep(60))
    agents_router._running_agent_tasks[task.id] = running

    try:
        response = await agents_router.cancel_task(task.id, db_session)
        assert response["status"] == "cancelling"
        with pytest.raises(asyncio.CancelledError):
            await running
    finally:
        agents_router._running_agent_tasks.pop(task.id, None)


@pytest.mark.asyncio
async def test_rollback_targets_a_merge_commit_with_main_parent() -> None:
    git = GitService("/tmp/repo")
    git._run = AsyncMock(return_value=(0, "", ""))  # type: ignore[method-assign]

    assert await git.rollback("abc123")
    git._run.assert_awaited_once_with("revert", "-m", "1", "--no-edit", "abc123")


@pytest.mark.asyncio
async def test_autonomous_profiles_are_exposed_read_only() -> None:
    profiles = await agents_router.list_profiles()

    for profile in profiles:
        assert "write_file" not in profile.tools
        assert "run_command" not in profile.tools


@pytest.mark.asyncio
async def test_openclaw_mutating_tool_is_disabled_before_any_api_call() -> None:
    with patch(
        "app.services.mcp_therese_server._call_therese_api",
        new=AsyncMock(),
    ) as api_call:
        result = await execute_tool(
            "send_email",
            {"to": "test@example.com", "subject": "Test", "body": "Bonjour"},
        )

    assert "désactivée" in result["error"]
    api_call.assert_not_awaited()


@pytest.mark.asyncio
async def test_openclaw_cancel_failure_keeps_session_running(db_session) -> None:
    agent_session = AgentSession(
        agent_name="katia",
        instruction="Mission externe",
        status="running",
        openclaw_session_id="remote-1",
    )
    db_session.add(agent_session)
    await db_session.commit()

    with (
        patch(
            "app.services.openclaw_bridge.cancel_session",
            new=AsyncMock(return_value=False),
        ),
        pytest.raises(HTTPException) as exc_info,
    ):
        await agents_router.cancel_openclaw_session(agent_session.id, db_session)

    assert exc_info.value.status_code == 502
    await db_session.refresh(agent_session)
    assert agent_session.status == "running"


@pytest.mark.asyncio
async def test_agent_request_persists_reconstructible_history(
    client,
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo-history"
    repo.mkdir()
    git = MagicMock()
    git.is_repo = AsyncMock(return_value=True)
    git.current_branch = AsyncMock(return_value="main")
    git.ensure_clean = AsyncMock(return_value=True)

    class FakeSwarm:
        def __init__(self, _source_path: str):
            pass

        async def process_request(self, _message: str, task_id: str):
            yield AgentStreamChunk(
                type="agent_start", agent="katia", content="Cadrage",
                task_id=task_id, phase="spec", model="claude-test",
            )
            yield AgentStreamChunk(
                type="handoff", agent="katia", content="Plan vérifiable",
                task_id=task_id, phase="analysis",
            )
            yield AgentStreamChunk(
                type="agent_start", agent="zezette", content="Réalisation",
                task_id=task_id, phase="implementation", model="gpt-test",
            )
            yield AgentStreamChunk(
                type="test_result", agent="zezette", content="3 tests passed",
                task_id=task_id, phase="testing",
            )
            yield AgentStreamChunk(
                type="review_ready", task_id=task_id, phase="review",
                branch="agent/history", base_branch="main", commit_hash="abc123def456",
                files_changed=["src/app.ts"], diff_summary="1 file changed",
            )
            yield AgentStreamChunk(
                type="explanation", agent="katia", content="Explication durable",
                task_id=task_id, phase="review",
            )
            yield AgentStreamChunk(
                type="agent_done", agent="katia", content="Sortie finale Katia",
                task_id=task_id, phase="review",
            )
            yield AgentStreamChunk(
                type="done", content="Terminé", task_id=task_id, phase="review",
            )

    with (
        patch("app.routers.agents._get_source_path", return_value=str(repo)),
        patch("app.routers.agents.GitService", return_value=git),
        patch("app.routers.agents.SwarmOrchestrator", FakeSwarm),
    ):
        response = await client.post(
            "/api/agents/request",
            json={"message": "Conserver tout l’historique de cette mission"},
        )

    assert response.status_code == 200, response.text
    done_line = next(
        line for line in response.text.splitlines()
        if '"type": "done"' in line
    )
    import json

    task_id = json.loads(done_line.removeprefix("data: "))["task_id"]
    task_response = await client.get(f"/api/agents/tasks/{task_id}")
    assert task_response.status_code == 200, task_response.text
    task = task_response.json()
    assert task["plan"] == "Plan vérifiable"
    assert task["test_results"] == ["3 tests passed"]
    assert task["explanation"] == "Explication durable"
    assert task["agent_outputs"]["katia"] == "Sortie finale Katia"
    assert json.loads(task["agent_model"]) == {
        "katia": "claude-test",
        "zezette": "gpt-test",
    }
    assert task["base_branch"] == "main"
    assert task["commit_hash"] == "abc123def456"
    assert task["run_phase"] == "review"
    assert task["events"]
