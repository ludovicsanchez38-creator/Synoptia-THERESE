"""
Tests pour le service MCP (Model Context Protocol) de THÉRÈSE v2.

Utilise pytest et pytest-asyncio avec mocking de subprocess.
"""

import asyncio
import json
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from app.services.mcp_service import (
    ALLOWED_MCP_COMMANDS,
    BLOCKED_COMMANDS,
    MCPServer,
    MCPServerStatus,
    MCPService,
    MCPTool,
    ToolCallResult,
    get_mcp_service,
    validate_mcp_command,
)


class TestValidateMCPCommand:
    """Tests pour la validation des commandes MCP."""

    def test_validate_mcp_command_allowed(self):
        """Les commandes whitelist doivent passer."""
        for cmd in ALLOWED_MCP_COMMANDS:
            # Ne doit pas lever d'exception
            validate_mcp_command(cmd)

    def test_validate_mcp_command_allowed_with_path(self):
        """Les commandes whitelist avec chemin doivent passer."""
        validate_mcp_command("/usr/bin/npx")
        validate_mcp_command("./node")
        validate_mcp_command("/opt/python3")

    def test_validate_mcp_command_blocked(self):
        """Les commandes bloquées doivent lever ValueError."""
        for cmd in BLOCKED_COMMANDS:
            with pytest.raises(ValueError, match="Commande MCP bloquee"):
                validate_mcp_command(cmd)

    def test_validate_mcp_command_blocked_with_path(self):
        """Les commandes bloquées avec chemin doivent lever ValueError."""
        with pytest.raises(ValueError, match="Commande MCP bloquee"):
            validate_mcp_command("/bin/rm")

    def test_validate_mcp_command_unknown(self):
        """Les commandes inconnues doivent lever ValueError."""
        with pytest.raises(ValueError, match="Commande MCP non autorisee"):
            validate_mcp_command("unknown_command")

    def test_validate_mcp_command_unknown_with_path(self):
        """Les commandes inconnues avec chemin doivent lever ValueError."""
        with pytest.raises(ValueError, match="Commande MCP non autorisee"):
            validate_mcp_command("/usr/bin/unknown_cmd")


class TestMCPServerStatus:
    """Tests pour l'énumération MCPServerStatus."""

    def test_mcp_server_status_enum(self):
        """MCPServerStatus a les bonnes valeurs."""
        assert MCPServerStatus.STOPPED.value == "stopped"
        assert MCPServerStatus.STARTING.value == "starting"
        assert MCPServerStatus.RUNNING.value == "running"
        assert MCPServerStatus.ERROR.value == "error"

    def test_mcp_server_status_all_values(self):
        """Vérifier que toutes les valeurs d'énumération sont présentes."""
        statuses = [s.value for s in MCPServerStatus]
        assert len(statuses) == 4
        assert "stopped" in statuses
        assert "starting" in statuses
        assert "running" in statuses
        assert "error" in statuses


class TestMCPTool:
    """Tests pour la dataclass MCPTool."""

    def test_mcp_tool_dataclass(self):
        """MCPTool a tous les champs requis."""
        tool = MCPTool(
            name="test_tool",
            description="A test tool",
            input_schema={"type": "object", "properties": {}},
            server_id="server123",
        )

        assert tool.name == "test_tool"
        assert tool.description == "A test tool"
        assert tool.input_schema == {"type": "object", "properties": {}}
        assert tool.server_id == "server123"


class TestMCPServer:
    """Tests pour la dataclass MCPServer."""

    def test_mcp_server_defaults(self):
        """MCPServer a les bonnes valeurs par défaut."""
        server = MCPServer(
            id="srv123",
            name="Test Server",
            command="npx",
        )

        assert server.id == "srv123"
        assert server.name == "Test Server"
        assert server.command == "npx"
        assert server.args == []
        assert server.env == {}
        assert server.enabled is True
        assert server.status == MCPServerStatus.STOPPED
        assert server.tools == []
        assert server.error is None
        assert server.process is None

    def test_mcp_server_to_dict(self):
        """MCPServer.to_dict() sérialise correctement."""
        server = MCPServer(
            id="srv123",
            name="Test Server",
            command="npx",
            args=["@claud/mcp-sse"],
            env={"VAR": "value"},
            enabled=True,
            status=MCPServerStatus.RUNNING,
            tools=[
                MCPTool(
                    name="tool1",
                    description="Tool 1",
                    input_schema={"type": "object"},
                    server_id="srv123",
                )
            ],
            error=None,
        )

        result = server.to_dict()

        assert result["id"] == "srv123"
        assert result["name"] == "Test Server"
        assert result["command"] == "npx"
        assert result["args"] == ["@claud/mcp-sse"]
        assert result["env"] == {"VAR": "value"}
        assert result["enabled"] is True
        assert result["status"] == "running"
        assert len(result["tools"]) == 1
        assert result["tools"][0]["name"] == "tool1"
        assert result["error"] is None
        assert "created_at" in result


class TestMCPService:
    """Tests pour MCPService."""

    @pytest.fixture
    def mcp_service(self, tmp_path):
        """Créer une instance MCPService avec chemin temporaire."""
        config_path = tmp_path / "mcp_servers.json"
        service = MCPService(config_path=config_path)
        return service

    @pytest.fixture
    def mock_save_config(self):
        """Mocker asyncio.create_task pour éviter 'no running event loop'."""
        with patch("app.services.mcp_service.asyncio.create_task"):
            yield

    def test_add_server(self, mcp_service, mock_save_config):
        """add_server() crée un serveur avec bon ID."""
        server = mcp_service.add_server(
            name="Test Server",
            command="npx",
            args=["@test/mcp"],
            enabled=True,
        )

        assert server.id is not None
        assert len(server.id) == 8
        assert server.name == "Test Server"
        assert server.command == "npx"
        assert server.args == ["@test/mcp"]
        assert server in mcp_service.servers.values()

    def test_add_server_generates_unique_ids(self, mcp_service, mock_save_config):
        """add_server() génère des IDs uniques pour chaque serveur."""
        server1 = mcp_service.add_server("Server 1", "npx")
        server2 = mcp_service.add_server("Server 2", "node")

        assert server1.id != server2.id

    def test_remove_server_not_found(self, mcp_service):
        """remove_server() avec ID invalide retourne False."""
        result = asyncio.run(mcp_service.remove_server("invalid_id"))
        assert result is False

    def test_remove_server_existing(self, mcp_service, mock_save_config):
        """remove_server() supprime un serveur existant."""
        server = mcp_service.add_server("Test", "npx")
        server_id = server.id

        result = asyncio.run(mcp_service.remove_server(server_id))

        assert result is True
        assert server_id not in mcp_service.servers

    @patch("app.services.mcp_service.asyncio.create_subprocess_exec")
    def test_start_server_not_found(self, mock_subprocess, mcp_service):
        """start_server() avec ID invalide retourne False."""
        result = asyncio.run(mcp_service.start_server("invalid_id"))
        assert result is False
        mock_subprocess.assert_not_called()

    @patch("app.services.mcp_service.asyncio.create_subprocess_exec")
    def test_start_server_blocked_command(self, mock_subprocess, mcp_service, mock_save_config):
        """start_server() avec commande bloquée échoue."""
        server = mcp_service.add_server("Bad Server", "rm", args=["-rf", "/"])
        result = asyncio.run(mcp_service.start_server(server.id))

        assert result is False
        mock_subprocess.assert_not_called()

    @pytest.mark.asyncio
    @patch("app.services.mcp_service.asyncio.create_subprocess_exec")
    async def test_start_server_creates_subprocess(self, mock_subprocess, mcp_service, mock_save_config):
        """start_server() crée un subprocess avec la bonne commande."""
        # Mock du processus
        mock_process = AsyncMock()
        mock_process.pid = 12345
        mock_process.stdout = AsyncMock()
        mock_process.stdout.readline = AsyncMock(return_value=b"")
        mock_process.stdin = AsyncMock()
        mock_process.stderr = AsyncMock()
        mock_process.stdin.drain = AsyncMock()
        mock_process.stdin.write = MagicMock()

        mock_subprocess.return_value = mock_process

        server = mcp_service.add_server("Test Server", "npx", args=["@test/mcp"])

        # Mocker _initialize_server et _list_tools pour éviter le timeout 30s
        with patch.object(mcp_service, "_initialize_server", new_callable=AsyncMock), \
             patch.object(mcp_service, "_list_tools", new_callable=AsyncMock):
            await mcp_service.start_server(server.id)

        # Vérifie que subprocess a été appelé avec les bons arguments
        mock_subprocess.assert_called_once()
        call_args = mock_subprocess.call_args
        assert call_args[0] == ("npx", "@test/mcp")  # commande + args

    @patch("app.services.mcp_service.asyncio.create_subprocess_exec")
    def test_stop_server_not_running(self, mock_subprocess, mcp_service, mock_save_config):
        """stop_server() sur serveur non démarré retourne False."""
        server = mcp_service.add_server("Test Server", "npx")
        result = asyncio.run(mcp_service.stop_server(server.id))

        assert result is False

    def test_call_tool_server_not_found(self, mcp_service):
        """call_tool() avec serveur inconnu retourne erreur."""
        result = asyncio.run(
            mcp_service.call_tool("invalid_id", "test_tool", {"arg": "value"})
        )

        assert result.success is False
        assert result.error == "Server not found"
        assert result.tool_name == "test_tool"
        assert result.server_id == "invalid_id"

    def test_call_tool_server_not_running(self, mcp_service, mock_save_config):
        """call_tool() avec serveur arrêté retourne erreur."""
        server = mcp_service.add_server("Test Server", "npx")
        server.status = MCPServerStatus.STOPPED

        result = asyncio.run(
            mcp_service.call_tool(server.id, "test_tool", {"arg": "value"})
        )

        assert result.success is False
        assert result.error == "Server not running"

    def test_get_all_tools_empty(self, mcp_service):
        """get_all_tools() sans serveurs retourne liste vide."""
        tools = mcp_service.get_all_tools()
        assert tools == []

    def test_get_all_tools_running_servers_only(self, mcp_service, mock_save_config):
        """get_all_tools() retourne uniquement les tools des serveurs running."""
        server1 = mcp_service.add_server("Server 1", "npx")
        server1.status = MCPServerStatus.RUNNING
        server1.tools = [
            MCPTool("tool1", "Tool 1", {}, server1.id),
            MCPTool("tool2", "Tool 2", {}, server1.id),
        ]

        server2 = mcp_service.add_server("Server 2", "node")
        server2.status = MCPServerStatus.STOPPED
        server2.tools = [MCPTool("tool3", "Tool 3", {}, server2.id)]

        tools = mcp_service.get_all_tools()

        assert len(tools) == 2
        assert all(t.server_id == server1.id for t in tools)

    def test_get_tools_for_llm_format(self, mcp_service, mock_save_config):
        """get_tools_for_llm() retourne le format correct."""
        server = mcp_service.add_server("Test Server", "npx")
        server.status = MCPServerStatus.RUNNING
        server.tools = [
            MCPTool(
                name="test_tool",
                description="A test tool",
                input_schema={"type": "object", "properties": {"arg": {"type": "string"}}},
                server_id=server.id,
            )
        ]

        tools = mcp_service.get_tools_for_llm()

        assert len(tools) == 1
        assert tools[0]["type"] == "function"
        assert "function" in tools[0]
        assert tools[0]["function"]["name"] == f"{server.id}__test_tool"
        assert tools[0]["function"]["description"] == "A test tool"
        assert "parameters" in tools[0]["function"]

    def test_execute_tool_call_invalid_format(self, mcp_service):
        """execute_tool_call() sans __ retourne erreur."""
        result = asyncio.run(
            mcp_service.execute_tool_call("invalid_format", {})
        )

        assert result.success is False
        assert result.error == "Invalid tool name format"
        assert result.tool_name == "invalid_format"

    def test_execute_tool_call_valid_format(self, mcp_service):
        """execute_tool_call() avec format valide sépare server_id et tool_name."""
        result = asyncio.run(
            mcp_service.execute_tool_call("server123__tool_name", {"arg": "value"})
        )

        # Le résultat aura success=False car le serveur n'existe pas
        # mais l'important est que le parsing s'est fait correctement
        assert result.tool_name == "tool_name"
        assert result.server_id == "server123"

    def test_list_servers_empty(self, mcp_service):
        """list_servers() sans serveurs retourne liste vide."""
        servers = mcp_service.list_servers()
        assert servers == []

    def test_list_servers_multiple(self, mcp_service, mock_save_config):
        """list_servers() retourne les serveurs configurés."""
        server1 = mcp_service.add_server("Server 1", "npx")
        server2 = mcp_service.add_server("Server 2", "node")

        servers = mcp_service.list_servers()

        assert len(servers) == 2
        assert servers[0]["name"] == "Server 1"
        assert servers[1]["name"] == "Server 2"


class TestMCPServiceSingleton:
    """Tests pour le singleton MCPService."""

    def test_get_mcp_service_singleton(self):
        """get_mcp_service() retourne un singleton."""
        # Réinitialiser le singleton pour le test
        import app.services.mcp_service as mcp_module
        original_service = mcp_module._mcp_service
        mcp_module._mcp_service = None

        try:
            service1 = get_mcp_service()
            service2 = get_mcp_service()

            assert service1 is service2
            assert isinstance(service1, MCPService)
        finally:
            # Restaurer l'état original
            mcp_module._mcp_service = original_service

    def test_get_mcp_service_creates_instance(self):
        """get_mcp_service() crée une instance si aucune n'existe."""
        import app.services.mcp_service as mcp_module
        original_service = mcp_module._mcp_service
        mcp_module._mcp_service = None

        try:
            service = get_mcp_service()
            assert isinstance(service, MCPService)
            assert mcp_module._mcp_service is not None
        finally:
            mcp_module._mcp_service = original_service


class TestToolCallResult:
    """Tests pour ToolCallResult."""

    def test_tool_call_result_success(self):
        """ToolCallResult avec succès."""
        result = ToolCallResult(
            tool_name="test_tool",
            server_id="srv123",
            success=True,
            result={"output": "success"},
            execution_time_ms=150.5,
        )

        assert result.tool_name == "test_tool"
        assert result.server_id == "srv123"
        assert result.success is True
        assert result.result == {"output": "success"}
        assert result.error is None
        assert result.execution_time_ms == 150.5

    def test_tool_call_result_failure(self):
        """ToolCallResult avec erreur."""
        result = ToolCallResult(
            tool_name="test_tool",
            server_id="srv123",
            success=False,
            error="Tool execution failed",
            execution_time_ms=50.0,
        )

        assert result.success is False
        assert result.error == "Tool execution failed"
        assert result.result is None


class TestMCPServiceConfiguration:
    """Tests pour la configuration et sauvegarde MCPService."""

    @pytest.fixture
    def mcp_service_with_config(self, tmp_path):
        """MCPService avec fichier de config."""
        config_path = tmp_path / "mcp_servers.json"
        return MCPService(config_path=config_path), config_path

    def test_config_path_default(self):
        """Le chemin config par défaut est ~/.therese/mcp_servers.json."""
        service = MCPService()
        expected = Path.home() / ".therese" / "mcp_servers.json"
        assert service.config_path == expected

    def test_config_path_custom(self, tmp_path):
        """Un chemin config personnalisé peut être utilisé."""
        custom_path = tmp_path / "custom_config.json"
        service = MCPService(config_path=custom_path)
        assert service.config_path == custom_path

    @pytest.mark.asyncio
    async def test_load_config_no_file(self, mcp_service_with_config):
        """_load_config() sans fichier ne lève pas d'erreur."""
        service, config_path = mcp_service_with_config

        await service._load_config()

        assert len(service.servers) == 0

    @pytest.mark.asyncio
    async def test_load_config_existing_file(self, tmp_path):
        """_load_config() charge les serveurs existants."""
        config_path = tmp_path / "mcp_servers.json"
        config_data = {
            "servers": [
                {
                    "id": "srv123",
                    "name": "Test Server",
                    "command": "npx",
                    "args": ["@test/mcp"],
                    "env": {},
                    "enabled": True,
                    "created_at": datetime.now(UTC).isoformat(),
                }
            ]
        }

        with open(config_path, "w") as f:
            json.dump(config_data, f)

        service = MCPService(config_path=config_path)
        await service._load_config()

        assert len(service.servers) == 1
        assert "srv123" in service.servers
        assert service.servers["srv123"].name == "Test Server"

    @pytest.mark.asyncio
    async def test_save_config(self, tmp_path):
        """_save_config() sauvegarde les serveurs dans le fichier."""
        config_path = tmp_path / "mcp_servers.json"
        service = MCPService(config_path=config_path)

        server = service.add_server("Test Server", "npx", args=["@test/mcp"])

        await service._save_config()

        assert config_path.exists()

        with open(config_path) as f:
            data = json.load(f)

        assert len(data["servers"]) == 1
        assert data["servers"][0]["name"] == "Test Server"
        assert data["servers"][0]["command"] == "npx"
