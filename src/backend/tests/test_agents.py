"""
Tests pour le système d'agents IA embarqués (Atelier).
"""

from pathlib import Path
from unittest.mock import AsyncMock

import pytest

# ============================================================
# Config
# ============================================================


class TestAgentConfig:
    """Tests pour le chargement de configuration des agents."""

    def test_load_katia_config(self):
        from app.services.agents.config import load_agent_config

        config = load_agent_config("katia")
        assert config.id == "katia"
        assert config.name == "Katia"
        assert config.default_model == "claude-sonnet-4-6"
        assert len(config.tools) > 0
        assert config.system_prompt  # SOUL.md non vide
        assert "PM" in config.system_prompt or "Guide" in config.system_prompt

    def test_load_zezette_config(self):
        from app.services.agents.config import load_agent_config

        config = load_agent_config("zezette")
        assert config.id == "zezette"
        assert config.name == "Zézette"
        assert config.default_model == "claude-sonnet-4-6"
        assert "write_file" in config.tools
        assert "run_command" in config.tools
        assert config.system_prompt
        assert "Développeuse" in config.system_prompt or "Dev" in config.system_prompt

    def test_load_unknown_agent_raises(self):
        from app.services.agents.config import load_agent_config

        with pytest.raises(FileNotFoundError):
            load_agent_config("agent_inexistant")

    def test_get_agent_config_cache(self):
        from app.services.agents.config import get_agent_config, reload_agent_configs

        reload_agent_configs()
        c1 = get_agent_config("katia")
        c2 = get_agent_config("katia")
        assert c1 is c2  # Même instance (cache)

    def test_reload_clears_cache(self):
        from app.services.agents.config import get_agent_config, reload_agent_configs

        c1 = get_agent_config("katia")
        reload_agent_configs()
        c2 = get_agent_config("katia")
        assert c1 is not c2  # Nouvelle instance après reload


# ============================================================
# Bus
# ============================================================


class TestAgentMessageBus:
    """Tests pour le bus de messages inter-agents."""

    @pytest.mark.asyncio
    async def test_send_and_receive(self):
        from app.services.agents.bus import AgentMessage, AgentMessageBus

        bus = AgentMessageBus()
        msg = AgentMessage(
            sender="katia",
            recipient="zezette",
            type="spec",
            content="Implémenter X",
        )
        await bus.send(msg)
        received = await bus.receive("zezette", timeout=1.0)
        assert received is not None
        assert received.sender == "katia"
        assert received.content == "Implémenter X"

    @pytest.mark.asyncio
    async def test_receive_timeout(self):
        from app.services.agents.bus import AgentMessageBus

        bus = AgentMessageBus()
        result = await bus.receive("nobody", timeout=0.1)
        assert result is None

    @pytest.mark.asyncio
    async def test_stop_signal(self):
        from app.services.agents.bus import AgentMessageBus

        bus = AgentMessageBus()
        await bus.stop("katia")
        result = await bus.receive("katia", timeout=1.0)
        assert result is None

    def test_clear(self):
        from app.services.agents.bus import AgentMessageBus

        bus = AgentMessageBus()
        bus._get_queue("test")
        assert "test" in bus._queues
        bus.clear()
        assert len(bus._queues) == 0


# ============================================================
# Tools
# ============================================================


class TestAgentTools:
    """Tests pour les outils des agents."""

    @pytest.mark.asyncio
    async def test_read_file(self, tmp_path: Path):
        from app.services.agents.tools import AgentToolExecutor

        test_file = tmp_path / "test.py"
        test_file.write_text("print('hello')\n")

        executor = AgentToolExecutor(str(tmp_path))
        result = await executor.read_file("test.py")
        assert "print('hello')" in result

    @pytest.mark.asyncio
    async def test_read_file_not_found(self, tmp_path: Path):
        from app.services.agents.tools import AgentToolExecutor

        executor = AgentToolExecutor(str(tmp_path))
        result = await executor.read_file("inexistant.py")
        assert "introuvable" in result.lower() or "erreur" in result.lower()

    @pytest.mark.asyncio
    async def test_list_directory(self, tmp_path: Path):
        from app.services.agents.tools import AgentToolExecutor

        (tmp_path / "fichier.py").touch()
        (tmp_path / "dossier").mkdir()

        executor = AgentToolExecutor(str(tmp_path))
        result = await executor.list_directory(".")
        assert "fichier.py" in result
        assert "dossier" in result

    @pytest.mark.asyncio
    async def test_path_traversal_blocked(self, tmp_path: Path):
        from app.services.agents.tools import AgentToolExecutor

        executor = AgentToolExecutor(str(tmp_path))
        with pytest.raises(PermissionError):
            executor._validate_path("../../etc/passwd")

    @pytest.mark.asyncio
    async def test_write_file_blocked_without_branch(self, tmp_path: Path):
        from app.services.agents.tools import AgentToolExecutor

        # Simuler un git service qui retourne une branche non-agent
        mock_git = AsyncMock()
        mock_git.current_branch = AsyncMock(return_value="main")

        executor = AgentToolExecutor(str(tmp_path), git_service=mock_git)
        result = await executor.write_file("test.txt", "contenu")
        assert "permission" in result.lower() or "interdite" in result.lower()

    @pytest.mark.asyncio
    async def test_write_file_allowed_on_agent_branch(self, tmp_path: Path):
        from app.services.agents.tools import AgentToolExecutor

        mock_git = AsyncMock()
        mock_git.current_branch = AsyncMock(return_value="agent/abc123-test")

        executor = AgentToolExecutor(str(tmp_path), git_service=mock_git)
        result = await executor.write_file("test.txt", "contenu")
        assert "écrit" in result.lower() or "test.txt" in result

        written = (tmp_path / "test.txt").read_text()
        assert written == "contenu"

    @pytest.mark.asyncio
    async def test_run_command_blocked(self, tmp_path: Path):
        from app.services.agents.tools import AgentToolExecutor

        mock_git = AsyncMock()
        mock_git.current_branch = AsyncMock(return_value="agent/test")

        executor = AgentToolExecutor(str(tmp_path), git_service=mock_git)
        result = await executor.run_command("rm -rf /")
        assert "non autorisée" in result.lower() or "erreur" in result.lower()

    @pytest.mark.asyncio
    async def test_clarify_returns_marker(self, tmp_path: Path):
        from app.services.agents.tools import AgentToolExecutor

        executor = AgentToolExecutor(str(tmp_path))
        result = await executor.clarify("Quel format ?")
        assert result.startswith("[CLARIFY]")
        assert "Quel format" in result

    @pytest.mark.asyncio
    async def test_create_spec_returns_marker(self, tmp_path: Path):
        from app.services.agents.tools import AgentToolExecutor

        executor = AgentToolExecutor(str(tmp_path))
        result = await executor.create_spec("Titre", "Description")
        assert result.startswith("[SPEC]")
        assert "Titre" in result

    def test_tools_schema_count(self):
        from app.services.agents.tools import THERESE_TOOLS, ZEZETTE_TOOLS

        assert len(THERESE_TOOLS) == 6
        assert len(ZEZETTE_TOOLS) == 7

        # Vérifier les noms
        therese_names = {t["function"]["name"] for t in THERESE_TOOLS}
        assert "clarify" in therese_names
        assert "create_spec" in therese_names
        assert "read_file" in therese_names

        zezette_names = {t["function"]["name"] for t in ZEZETTE_TOOLS}
        assert "write_file" in zezette_names
        assert "run_command" in zezette_names
        assert "git_diff" in zezette_names


# ============================================================
# Git Service
# ============================================================


class TestGitService:
    """Tests pour le service git."""

    @pytest.mark.asyncio
    async def test_is_repo_false(self, tmp_path: Path):
        from app.services.agents.git_service import GitService

        git = GitService(tmp_path)
        assert not await git.is_repo()

    @pytest.mark.asyncio
    async def test_init_and_is_repo(self, tmp_path: Path):
        from app.services.agents.git_service import GitService

        git = GitService(tmp_path)
        result = await git.init()
        assert result
        assert await git.is_repo()

    @pytest.mark.asyncio
    async def test_create_branch_and_current(self, tmp_path: Path):
        from app.services.agents.git_service import GitService

        git = GitService(tmp_path)
        await git.init()

        # Créer un commit initial (git nécessite au moins 1 commit pour les branches)
        (tmp_path / "README.md").write_text("# Test")
        await git.commit("Initial commit")

        result = await git.create_branch("agent/test-123")
        assert result
        branch = await git.current_branch()
        assert branch == "agent/test-123"

    @pytest.mark.asyncio
    async def test_status_clean(self, tmp_path: Path):
        from app.services.agents.git_service import GitService

        git = GitService(tmp_path)
        await git.init()
        (tmp_path / "file.txt").write_text("content")
        await git.commit("init")

        status = await git.status()
        assert status.strip() == ""

    @pytest.mark.asyncio
    async def test_ensure_clean(self, tmp_path: Path):
        from app.services.agents.git_service import GitService

        git = GitService(tmp_path)
        await git.init()
        (tmp_path / "file.txt").write_text("content")
        await git.commit("init")

        assert await git.ensure_clean()

        # Ajouter un fichier non suivi
        (tmp_path / "dirty.txt").write_text("dirty")
        assert not await git.ensure_clean()


# ============================================================
# Entities
# ============================================================


class TestAgentEntities:
    """Tests pour les modèles de données agents."""

    def test_agent_task_defaults(self):
        from app.models.entities_agents import AgentTask

        task = AgentTask(title="Test")
        assert task.status == "pending"
        assert task.tokens_used == 0
        assert task.cost_eur == 0.0
        assert task.id  # UUID généré

    def test_agent_message_fields(self):
        from app.models.entities_agents import AgentMessage

        msg = AgentMessage(
            task_id="task-1",
            agent="katia",
            role="assistant",
            content="Bonjour",
        )
        assert msg.agent == "katia"
        assert msg.role == "assistant"

    def test_code_change_fields(self):
        from app.models.entities_agents import CodeChange

        change = CodeChange(
            task_id="task-1",
            file_path="src/main.py",
            change_type="modified",
        )
        assert change.approved is None  # En attente par défaut


# ============================================================
# Schemas
# ============================================================


class TestAgentSchemas:
    """Tests pour les schemas Pydantic."""

    def test_agent_request(self):
        from app.models.schemas_agents import AgentRequest

        req = AgentRequest(message="Ajouter un filtre")
        assert req.message == "Ajouter un filtre"
        assert req.source_path is None

    def test_agent_stream_chunk(self):
        from app.models.schemas_agents import AgentStreamChunk

        chunk = AgentStreamChunk(
            type="agent_chunk",
            agent="katia",
            content="Analyse...",
            task_id="123",
        )
        data = chunk.model_dump(exclude_none=True)
        assert data["type"] == "agent_chunk"
        assert data["agent"] == "katia"
        assert "content" in data

    def test_agent_status_response(self):
        from app.models.schemas_agents import AgentStatusResponse

        status = AgentStatusResponse()
        assert status.git_available is False
        assert status.katia_ready is False


# ============================================================
# Swarm (slugify)
# ============================================================


class TestSwarmHelpers:
    """Tests pour les helpers du swarm."""

    def test_slugify_basic(self):
        from app.services.agents.swarm import _slugify

        assert _slugify("Ajouter un filtre") == "ajouter-un-filtre"

    def test_slugify_accents(self):
        from app.services.agents.swarm import _slugify

        assert _slugify("Améliorer le résumé") == "ameliorer-le-resume"

    def test_slugify_max_length(self):
        from app.services.agents.swarm import _slugify

        result = _slugify("x" * 100)
        assert len(result) <= 40

    def test_slugify_special_chars(self):
        from app.services.agents.swarm import _slugify

        result = _slugify("Fix BUG-123: erreur/crash")
        assert "/" not in result
        assert ":" not in result
