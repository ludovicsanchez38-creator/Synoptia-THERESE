"""
THÉRÈSE v2 - MCP (Model Context Protocol) Service

Manages MCP servers, their tools, and tool execution.
"""

import asyncio
import json
import logging
import os
import shutil
import subprocess
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Whitelist commandes MCP autorisees (SEC-001)
ALLOWED_MCP_COMMANDS = {
    "npx", "node", "python", "python3", "uvx", "uv", "docker",
    "deno", "bun",
}

BLOCKED_COMMANDS = {
    "rm", "rmdir", "dd", "mkfs", "fdisk", "sh", "bash", "zsh",
    "curl", "wget", "nc", "ncat", "telnet", "ssh", "scp",
    "chmod", "chown", "sudo", "su", "kill", "killall",
}

# Operateurs shell dangereux dans les arguments (SEC-001)
SHELL_OPERATORS = {";", "|", "&&", "||", "`", "$", ">", "<"}


def validate_mcp_command(command: str, args: list[str] | None = None) -> None:
    """Valide que la commande MCP est dans la whitelist et que les args sont surs."""
    # Resolve symlinks via shutil.which() (SEC-001)
    resolved = shutil.which(command)
    if resolved:
        cmd_name = Path(resolved).name
    else:
        cmd_name = Path(command).name

    if cmd_name in BLOCKED_COMMANDS:
        raise ValueError(f"Commande MCP bloquee : '{cmd_name}' est interdite pour des raisons de securite")

    if cmd_name not in ALLOWED_MCP_COMMANDS:
        logger.warning(f"Commande MCP non whitelistee : '{cmd_name}'. Autorisees : {ALLOWED_MCP_COMMANDS}")
        raise ValueError(
            f"Commande MCP non autorisee : '{cmd_name}'. "
            f"Commandes autorisees : {', '.join(sorted(ALLOWED_MCP_COMMANDS))}"
        )

    # Valider les arguments contre les operateurs shell (SEC-001)
    if args:
        for arg in args:
            for op in SHELL_OPERATORS:
                if op in arg:
                    raise ValueError(
                        f"Argument MCP invalide : contient l'operateur shell '{op}'. "
                        f"Les operateurs shell ne sont pas autorises dans les arguments MCP."
                    )


class MCPServerStatus(str, Enum):
    """MCP server status."""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    ERROR = "error"


@dataclass
class MCPTool:
    """A tool exposed by an MCP server."""
    name: str
    description: str
    input_schema: dict
    server_id: str


@dataclass
class MCPServer:
    """MCP server configuration and state."""
    id: str
    name: str
    command: str
    args: list[str] = field(default_factory=list)
    env: dict[str, str] = field(default_factory=dict)
    enabled: bool = True
    status: MCPServerStatus = MCPServerStatus.STOPPED
    tools: list[MCPTool] = field(default_factory=list)
    error: str | None = None
    process: subprocess.Popen | None = field(default=None, repr=False)
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "command": self.command,
            "args": self.args,
            "env": self.env,
            "enabled": self.enabled,
            "status": self.status.value,
            "tools": [
                {
                    "name": t.name,
                    "description": t.description,
                    "input_schema": t.input_schema,
                }
                for t in self.tools
            ],
            "error": self.error,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class ToolCallResult:
    """Result of a tool call."""
    tool_name: str
    server_id: str
    success: bool
    result: Any = None
    error: str | None = None
    execution_time_ms: float = 0


class MCPService:
    """
    Service for managing MCP servers and executing tools.

    Uses stdio transport to communicate with MCP servers.
    """

    def __init__(self, config_path: Path | None = None):
        """Initialize MCP service."""
        self.config_path = config_path or Path.home() / ".therese" / "mcp_servers.json"
        self.servers: dict[str, MCPServer] = {}
        self._processes: dict[str, asyncio.subprocess.Process] = {}
        self._request_id = 0
        self._pending_requests: dict[int, asyncio.Future] = {}
        self._pending_timestamps: dict[int, float] = {}  # Sprint 2 - PERF-2.14
        self._reader_tasks: dict[str, asyncio.Task] = {}
        self._stderr_reader_tasks: dict[str, asyncio.Task] = {}  # Sprint 2 - PERF-2.8
        self._cleanup_task: asyncio.Task | None = None  # Sprint 2 - PERF-2.14

    async def initialize(self):
        """Load saved servers and start enabled ones."""
        await self._load_config()
        # Start cleanup task for pending requests (Sprint 2 - PERF-2.14)
        self._cleanup_task = asyncio.create_task(self._cleanup_pending_requests())
        for server in self.servers.values():
            if server.enabled:
                await self.start_server(server.id)

    async def _load_config(self):
        """Load server configurations from disk."""
        if not self.config_path.exists():
            logger.info("No MCP config found, starting fresh")
            return

        try:
            with open(self.config_path) as f:
                data = json.load(f)

            for server_data in data.get("servers", []):
                server = MCPServer(
                    id=server_data["id"],
                    name=server_data["name"],
                    command=server_data["command"],
                    args=server_data.get("args", []),
                    env=server_data.get("env", {}),
                    enabled=server_data.get("enabled", True),
                    created_at=datetime.fromisoformat(server_data.get("created_at", datetime.utcnow().isoformat())),
                )
                self.servers[server.id] = server
                logger.info(f"Loaded MCP server config: {server.name}")

        except Exception as e:
            logger.error(f"Failed to load MCP config: {e}")

    async def _save_config(self):
        """Save server configurations to disk."""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "servers": [
                {
                    "id": s.id,
                    "name": s.name,
                    "command": s.command,
                    "args": s.args,
                    "env": s.env,
                    "enabled": s.enabled,
                    "created_at": s.created_at.isoformat(),
                }
                for s in self.servers.values()
            ]
        }

        with open(self.config_path, "w") as f:
            json.dump(data, f, indent=2)

    def add_server(
        self,
        name: str,
        command: str,
        args: list[str] | None = None,
        env: dict[str, str] | None = None,
        enabled: bool = True,
    ) -> MCPServer:
        """Add a new MCP server configuration."""
        # Detect duplicates (same command + args)
        check_args = args or []
        for existing in self.servers.values():
            if existing.command == command and existing.args == check_args:
                raise ValueError(
                    f"Un serveur MCP avec la meme commande existe deja : '{existing.name}' (id: {existing.id})"
                )

        server_id = str(uuid.uuid4())[:8]
        server = MCPServer(
            id=server_id,
            name=name,
            command=command,
            args=args or [],
            env=env or {},
            enabled=enabled,
        )
        self.servers[server_id] = server
        asyncio.create_task(self._save_config())
        logger.info(f"Added MCP server: {name} ({server_id})")
        return server

    async def remove_server(self, server_id: str) -> bool:
        """Remove an MCP server."""
        if server_id not in self.servers:
            return False

        await self.stop_server(server_id)
        del self.servers[server_id]
        await self._save_config()
        logger.info(f"Removed MCP server: {server_id}")
        return True

    async def start_server(self, server_id: str) -> bool:
        """Start an MCP server process."""
        if server_id not in self.servers:
            logger.error(f"Server not found: {server_id}")
            return False

        server = self.servers[server_id]

        if server.status == MCPServerStatus.RUNNING:
            logger.warning(f"Server already running: {server.name}")
            return True

        server.status = MCPServerStatus.STARTING
        server.error = None

        try:
            # Validate command and args (SEC-001)
            validate_mcp_command(server.command, server.args)

            # Build command
            cmd = [server.command] + server.args

            # Merge environment et dechiffrer les env vars (Phase 5 - MCP Security)
            from app.services.encryption import decrypt_value, is_value_encrypted

            # Env minimal pour subprocess MCP (SEC-005)
            # Ne PAS copier tout os.environ pour eviter de leaker les cles API
            env = {
                "PATH": os.environ.get("PATH", ""),
                "HOME": os.environ.get("HOME", ""),
                "USER": os.environ.get("USER", ""),
                "LANG": os.environ.get("LANG", "en_US.UTF-8"),
                "TERM": os.environ.get("TERM", "xterm-256color"),
                "NODE_PATH": os.environ.get("NODE_PATH", ""),
                "TMPDIR": os.environ.get("TMPDIR", "/tmp"),
            }
            # Ajouter npm/node paths si presents
            for key in ["NVM_DIR", "NVM_BIN", "NPM_CONFIG_PREFIX"]:
                if key in os.environ:
                    env[key] = os.environ[key]
            decrypted_env = {}
            for key, value in server.env.items():
                if is_value_encrypted(value):
                    try:
                        decrypted_env[key] = decrypt_value(value)
                    except Exception as e:
                        logger.error(f"Failed to decrypt env var {key}: {e}")
                        decrypted_env[key] = value
                else:
                    decrypted_env[key] = value
            env.update(decrypted_env)

            # Start process with stdio transport
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
            )

            self._processes[server_id] = process
            server.status = MCPServerStatus.RUNNING
            logger.info(f"Started MCP server: {server.name} (PID {process.pid})")

            # Start reader tasks (stdout and stderr)
            self._reader_tasks[server_id] = asyncio.create_task(
                self._read_server_output(server_id)
            )
            # Sprint 2 - PERF-2.8: Read stderr to log errors without blocking
            self._stderr_reader_tasks[server_id] = asyncio.create_task(
                self._read_server_stderr(server_id)
            )

            # Initialize the server (send initialize request)
            await self._initialize_server(server_id)

            # Get available tools
            await self._list_tools(server_id)

            return True

        except FileNotFoundError:
            server.status = MCPServerStatus.ERROR
            server.error = f"Command not found: {server.command}"
            logger.error(f"Failed to start {server.name}: {server.error}")
            return False
        except Exception as e:
            server.status = MCPServerStatus.ERROR
            server.error = str(e)
            logger.error(f"Failed to start {server.name}: {e}")
            return False

    async def stop_server(self, server_id: str) -> bool:
        """Stop an MCP server process."""
        if server_id not in self._processes:
            return False

        process = self._processes[server_id]

        try:
            process.terminate()
            await asyncio.wait_for(process.wait(), timeout=5.0)
        except asyncio.TimeoutError:
            try:
                process.kill()
                await process.wait()
            except ProcessLookupError:
                # Process already dead, that's fine
                pass
        except ProcessLookupError:
            # Process already dead, that's fine
            pass

        # Cancel reader tasks
        if server_id in self._reader_tasks:
            self._reader_tasks[server_id].cancel()
            del self._reader_tasks[server_id]

        # Cancel stderr reader task (Sprint 2 - PERF-2.8)
        if server_id in self._stderr_reader_tasks:
            self._stderr_reader_tasks[server_id].cancel()
            del self._stderr_reader_tasks[server_id]

        del self._processes[server_id]

        if server_id in self.servers:
            self.servers[server_id].status = MCPServerStatus.STOPPED
            self.servers[server_id].tools = []

        logger.info(f"Stopped MCP server: {server_id}")
        return True

    async def _read_server_output(self, server_id: str):
        """Read and process output from MCP server."""
        process = self._processes.get(server_id)
        if not process or not process.stdout:
            return

        try:
            while True:
                line = await process.stdout.readline()
                if not line:
                    break

                try:
                    message = json.loads(line.decode())
                    await self._handle_server_message(server_id, message)
                except json.JSONDecodeError:
                    logger.debug(f"Non-JSON output from {server_id}: {line.decode().strip()}")

        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Error reading from {server_id}: {e}")
            if server_id in self.servers:
                self.servers[server_id].status = MCPServerStatus.ERROR
                self.servers[server_id].error = str(e)

    async def _read_server_stderr(self, server_id: str):
        """
        Read and log stderr output from MCP server (Sprint 2 - PERF-2.8).

        This prevents stderr buffer from filling up and blocking the process.
        Errors are logged but don't interrupt server operation.
        """
        process = self._processes.get(server_id)
        if not process or not process.stderr:
            return

        server_name = self.servers.get(server_id, MCPServer(id=server_id, name=server_id, command="")).name

        try:
            while True:
                line = await process.stderr.readline()
                if not line:
                    break

                stderr_text = line.decode().strip()
                if stderr_text:
                    # Log at appropriate level based on content
                    lower_text = stderr_text.lower()
                    if "error" in lower_text or "fatal" in lower_text:
                        logger.error(f"[MCP:{server_name}] {stderr_text}")
                    elif "warn" in lower_text:
                        logger.warning(f"[MCP:{server_name}] {stderr_text}")
                    else:
                        logger.debug(f"[MCP:{server_name}] {stderr_text}")

        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.warning(f"Error reading stderr from {server_id}: {e}")

    async def _cleanup_pending_requests(self):
        """
        Periodically clean up stale pending requests (Sprint 2 - PERF-2.14).

        Requests older than 60 seconds are cancelled to prevent memory leaks.
        """
        import time
        CLEANUP_INTERVAL = 30  # Check every 30 seconds
        REQUEST_TIMEOUT = 60  # Cancel requests older than 60 seconds

        try:
            while True:
                await asyncio.sleep(CLEANUP_INTERVAL)

                now = time.time()
                stale_ids = []

                for request_id, timestamp in list(self._pending_timestamps.items()):
                    if now - timestamp > REQUEST_TIMEOUT:
                        stale_ids.append(request_id)

                for request_id in stale_ids:
                    if request_id in self._pending_requests:
                        future = self._pending_requests.pop(request_id)
                        self._pending_timestamps.pop(request_id, None)
                        if not future.done():
                            future.set_exception(
                                asyncio.TimeoutError(f"Request {request_id} timed out after {REQUEST_TIMEOUT}s")
                            )
                        logger.warning(f"Cleaned up stale pending request: {request_id}")

                if stale_ids:
                    logger.info(f"Cleaned up {len(stale_ids)} stale MCP pending requests")

        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Error in pending requests cleanup: {e}")

    async def _handle_server_message(self, server_id: str, message: dict):
        """Handle a message from an MCP server."""
        msg_id = message.get("id")

        if msg_id and msg_id in self._pending_requests:
            # This is a response to a request
            future = self._pending_requests.pop(msg_id)
            self._pending_timestamps.pop(msg_id, None)  # Sprint 2 - PERF-2.14
            if "error" in message:
                future.set_exception(Exception(message["error"].get("message", "Unknown error")))
            else:
                future.set_result(message.get("result"))

    async def _send_request(self, server_id: str, method: str, params: dict | None = None) -> Any:
        """Send a JSON-RPC request to an MCP server."""
        import time

        if server_id not in self._processes:
            raise RuntimeError(f"Server not running: {server_id}")

        process = self._processes[server_id]
        if not process.stdin:
            raise RuntimeError(f"No stdin for server: {server_id}")

        self._request_id += 1
        request_id = self._request_id

        request = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
        }
        if params:
            request["params"] = params

        # Create future for response
        future: asyncio.Future = asyncio.Future()
        self._pending_requests[request_id] = future
        self._pending_timestamps[request_id] = time.time()  # Sprint 2 - PERF-2.14

        # Send request
        request_line = json.dumps(request) + "\n"
        process.stdin.write(request_line.encode())
        await process.stdin.drain()

        # Wait for response with timeout
        try:
            result = await asyncio.wait_for(future, timeout=30.0)
            return result
        except asyncio.TimeoutError:
            self._pending_requests.pop(request_id, None)
            self._pending_timestamps.pop(request_id, None)  # Sprint 2 - PERF-2.14
            raise RuntimeError(f"Request timeout: {method}")

    async def _initialize_server(self, server_id: str):
        """Send initialize request to MCP server."""
        try:
            result = await self._send_request(server_id, "initialize", {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {},
                },
                "clientInfo": {
                    "name": "THERESE",
                    "version": "2.0",
                },
            })
            logger.info(f"Initialized MCP server {server_id}: {result}")

            # Send initialized notification
            await self._send_notification(server_id, "notifications/initialized", {})

        except Exception as e:
            logger.error(f"Failed to initialize {server_id}: {e}")
            raise

    async def _send_notification(self, server_id: str, method: str, params: dict | None = None):
        """Send a JSON-RPC notification (no response expected)."""
        if server_id not in self._processes:
            return

        process = self._processes[server_id]
        if not process.stdin:
            return

        notification = {
            "jsonrpc": "2.0",
            "method": method,
        }
        if params:
            notification["params"] = params

        notification_line = json.dumps(notification) + "\n"
        process.stdin.write(notification_line.encode())
        await process.stdin.drain()

    async def _list_tools(self, server_id: str):
        """Get list of available tools from MCP server."""
        try:
            result = await self._send_request(server_id, "tools/list", {})
            tools = result.get("tools", [])

            server = self.servers[server_id]
            server.tools = [
                MCPTool(
                    name=t["name"],
                    description=t.get("description", ""),
                    input_schema=t.get("inputSchema", {}),
                    server_id=server_id,
                )
                for t in tools
            ]
            logger.info(f"Server {server.name} has {len(server.tools)} tools")

        except Exception as e:
            logger.error(f"Failed to list tools for {server_id}: {e}")

    async def call_tool(
        self,
        server_id: str,
        tool_name: str,
        arguments: dict | None = None,
    ) -> ToolCallResult:
        """Execute a tool on an MCP server."""
        import time
        start_time = time.time()

        if server_id not in self.servers:
            return ToolCallResult(
                tool_name=tool_name,
                server_id=server_id,
                success=False,
                error="Server not found",
            )

        if self.servers[server_id].status != MCPServerStatus.RUNNING:
            return ToolCallResult(
                tool_name=tool_name,
                server_id=server_id,
                success=False,
                error="Server not running",
            )

        try:
            result = await self._send_request(server_id, "tools/call", {
                "name": tool_name,
                "arguments": arguments or {},
            })

            execution_time = (time.time() - start_time) * 1000

            return ToolCallResult(
                tool_name=tool_name,
                server_id=server_id,
                success=True,
                result=result,
                execution_time_ms=execution_time,
            )

        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            logger.error(f"Tool call failed: {tool_name} on {server_id}: {e}")
            return ToolCallResult(
                tool_name=tool_name,
                server_id=server_id,
                success=False,
                error=str(e),
                execution_time_ms=execution_time,
            )

    def get_all_tools(self) -> list[MCPTool]:
        """Get all tools from all running servers."""
        tools = []
        for server in self.servers.values():
            if server.status == MCPServerStatus.RUNNING:
                tools.extend(server.tools)
        return tools

    def get_tools_for_llm(self) -> list[dict]:
        """
        Get tools formatted for LLM function calling.

        Returns tools in OpenAI/Anthropic compatible format.
        """
        tools = []
        for tool in self.get_all_tools():
            tools.append({
                "type": "function",
                "function": {
                    "name": f"{tool.server_id}__{tool.name}",  # Prefix with server ID
                    "description": tool.description,
                    "parameters": tool.input_schema,
                },
            })
        return tools

    async def execute_tool_call(self, tool_call_name: str, arguments: dict) -> ToolCallResult:
        """
        Execute a tool call from LLM response.

        Tool name format: {server_id}__{tool_name}
        """
        if "__" not in tool_call_name:
            return ToolCallResult(
                tool_name=tool_call_name,
                server_id="unknown",
                success=False,
                error="Invalid tool name format",
            )

        server_id, tool_name = tool_call_name.split("__", 1)
        return await self.call_tool(server_id, tool_name, arguments)

    def list_servers(self) -> list[dict]:
        """Get list of all configured servers."""
        return [s.to_dict() for s in self.servers.values()]

    async def shutdown(self):
        """Stop all servers and cleanup."""
        # Cancel cleanup task (Sprint 2 - PERF-2.14)
        if self._cleanup_task:
            self._cleanup_task.cancel()
            self._cleanup_task = None

        for server_id in list(self._processes.keys()):
            await self.stop_server(server_id)

        # Clear any remaining pending requests
        for future in self._pending_requests.values():
            if not future.done():
                future.cancel()
        self._pending_requests.clear()
        self._pending_timestamps.clear()

        logger.info("MCP service shut down")


# Global instance
_mcp_service: MCPService | None = None


def get_mcp_service() -> MCPService:
    """Get global MCP service instance."""
    global _mcp_service
    if _mcp_service is None:
        _mcp_service = MCPService()
    return _mcp_service


async def initialize_mcp_service():
    """Initialize the global MCP service."""
    service = get_mcp_service()
    await service.initialize()
    return service
