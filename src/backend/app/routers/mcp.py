"""
THÉRÈSE v2 - MCP Router

API endpoints for managing MCP servers and tools.
"""

import logging
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.mcp_service import get_mcp_service, MCPServerStatus

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================
# Schemas
# ============================================================


class MCPServerCreate(BaseModel):
    """Create MCP server request."""
    name: str
    command: str
    args: list[str] = []
    env: dict[str, str] = {}
    enabled: bool = True


class MCPServerUpdate(BaseModel):
    """Update MCP server request."""
    name: str | None = None
    command: str | None = None
    args: list[str] | None = None
    env: dict[str, str] | None = None
    enabled: bool | None = None


class MCPToolCall(BaseModel):
    """Tool call request."""
    tool_name: str
    arguments: dict[str, Any] = {}


class MCPServerResponse(BaseModel):
    """MCP server response."""
    id: str
    name: str
    command: str
    args: list[str]
    env: dict[str, str]
    enabled: bool
    status: str
    tools: list[dict]
    error: str | None
    created_at: str


class MCPToolResponse(BaseModel):
    """MCP tool response."""
    name: str
    description: str
    input_schema: dict
    server_id: str
    server_name: str


class ToolCallResultResponse(BaseModel):
    """Tool call result response."""
    tool_name: str
    server_id: str
    success: bool
    result: Any = None
    error: str | None = None
    execution_time_ms: float


# ============================================================
# Endpoints
# ============================================================


@router.get("/servers")
async def list_servers() -> list[MCPServerResponse]:
    """List all configured MCP servers."""
    service = get_mcp_service()
    servers = service.list_servers()
    return [MCPServerResponse(**s) for s in servers]


@router.post("/servers")
async def create_server(request: MCPServerCreate) -> MCPServerResponse:
    """Add a new MCP server configuration."""
    from app.services.encryption import encrypt_value, is_value_encrypted

    service = get_mcp_service()

    # Chiffrer les env vars (Phase 5 - MCP Security)
    encrypted_env = {}
    for key, value in request.env.items():
        if not is_value_encrypted(value):
            encrypted_env[key] = encrypt_value(value)
        else:
            encrypted_env[key] = value

    server = service.add_server(
        name=request.name,
        command=request.command,
        args=request.args,
        env=encrypted_env,
        enabled=request.enabled,
    )

    # Auto-start if enabled
    if request.enabled:
        await service.start_server(server.id)

    return MCPServerResponse(**server.to_dict())


@router.get("/servers/{server_id}")
async def get_server(server_id: str) -> MCPServerResponse:
    """Get a specific MCP server."""
    service = get_mcp_service()

    if server_id not in service.servers:
        raise HTTPException(status_code=404, detail="Server not found")

    return MCPServerResponse(**service.servers[server_id].to_dict())


@router.put("/servers/{server_id}")
async def update_server(server_id: str, request: MCPServerUpdate) -> MCPServerResponse:
    """Update an MCP server configuration."""
    from app.services.encryption import encrypt_value, is_value_encrypted

    service = get_mcp_service()

    if server_id not in service.servers:
        raise HTTPException(status_code=404, detail="Server not found")

    server = service.servers[server_id]
    was_running = server.status == MCPServerStatus.RUNNING

    # Update fields
    if request.name is not None:
        server.name = request.name
    if request.command is not None:
        server.command = request.command
    if request.args is not None:
        server.args = request.args
    if request.env is not None:
        # Chiffrer les env vars (Phase 5 - MCP Security)
        encrypted_env = {}
        for key, value in request.env.items():
            if not is_value_encrypted(value):
                encrypted_env[key] = encrypt_value(value)
            else:
                encrypted_env[key] = value
        server.env = encrypted_env
    if request.enabled is not None:
        server.enabled = request.enabled

    # Restart if running and config changed
    if was_running and (request.command is not None or request.args is not None or request.env is not None):
        await service.stop_server(server_id)
        await service.start_server(server_id)
    elif request.enabled is True and not was_running:
        await service.start_server(server_id)
    elif request.enabled is False and was_running:
        await service.stop_server(server_id)

    await service._save_config()

    return MCPServerResponse(**server.to_dict())


@router.delete("/servers/{server_id}")
async def delete_server(server_id: str):
    """Remove an MCP server."""
    service = get_mcp_service()

    if server_id not in service.servers:
        raise HTTPException(status_code=404, detail="Server not found")

    await service.remove_server(server_id)

    return {"deleted": True, "server_id": server_id}


@router.post("/servers/{server_id}/start")
async def start_server(server_id: str) -> MCPServerResponse:
    """Start an MCP server."""
    service = get_mcp_service()

    if server_id not in service.servers:
        raise HTTPException(status_code=404, detail="Server not found")

    success = await service.start_server(server_id)
    if not success:
        server = service.servers[server_id]
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start server: {server.error}"
        )

    return MCPServerResponse(**service.servers[server_id].to_dict())


@router.post("/servers/{server_id}/stop")
async def stop_server(server_id: str) -> MCPServerResponse:
    """Stop an MCP server."""
    service = get_mcp_service()

    if server_id not in service.servers:
        raise HTTPException(status_code=404, detail="Server not found")

    await service.stop_server(server_id)

    return MCPServerResponse(**service.servers[server_id].to_dict())


@router.post("/servers/{server_id}/restart")
async def restart_server(server_id: str) -> MCPServerResponse:
    """Restart an MCP server."""
    service = get_mcp_service()

    if server_id not in service.servers:
        raise HTTPException(status_code=404, detail="Server not found")

    await service.stop_server(server_id)
    await service.start_server(server_id)

    return MCPServerResponse(**service.servers[server_id].to_dict())


@router.get("/tools")
async def list_tools() -> list[MCPToolResponse]:
    """List all available tools from all running servers."""
    service = get_mcp_service()
    tools = service.get_all_tools()

    return [
        MCPToolResponse(
            name=t.name,
            description=t.description,
            input_schema=t.input_schema,
            server_id=t.server_id,
            server_name=service.servers[t.server_id].name if t.server_id in service.servers else "unknown",
        )
        for t in tools
    ]


@router.get("/tools/llm-format")
async def get_tools_for_llm():
    """Get tools formatted for LLM function calling."""
    service = get_mcp_service()
    return service.get_tools_for_llm()


@router.post("/tools/call")
async def call_tool(request: MCPToolCall) -> ToolCallResultResponse:
    """
    Execute a tool call.

    Tool name can be in two formats:
    - Simple: "tool_name" (will search all servers)
    - Qualified: "server_id__tool_name" (specific server)
    """
    service = get_mcp_service()

    if "__" in request.tool_name:
        # Qualified name
        result = await service.execute_tool_call(request.tool_name, request.arguments)
    else:
        # Search for tool in all servers
        tool = None
        for t in service.get_all_tools():
            if t.name == request.tool_name:
                tool = t
                break

        if not tool:
            raise HTTPException(status_code=404, detail=f"Tool not found: {request.tool_name}")

        result = await service.call_tool(tool.server_id, tool.name, request.arguments)

    return ToolCallResultResponse(
        tool_name=result.tool_name,
        server_id=result.server_id,
        success=result.success,
        result=result.result,
        error=result.error,
        execution_time_ms=result.execution_time_ms,
    )


@router.get("/status")
async def get_status():
    """Get overall MCP service status."""
    service = get_mcp_service()

    servers = list(service.servers.values())
    running = [s for s in servers if s.status == MCPServerStatus.RUNNING]
    tools = service.get_all_tools()

    return {
        "total_servers": len(servers),
        "running_servers": len(running),
        "total_tools": len(tools),
        "servers": {
            s.id: {
                "name": s.name,
                "status": s.status.value,
                "tools_count": len(s.tools),
            }
            for s in servers
        },
    }


# ============================================================
# Preset MCP Servers
# ============================================================


PRESET_SERVERS = [
    # ============================================================
    # Tier 1 - Sans API Key (Priorité max)
    # ============================================================
    {
        "id": "filesystem",
        "name": "Filesystem",
        "description": "Write, move, copy files (complète les features natives)",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-filesystem", "{WORKING_DIRECTORY}"],
    },
    {
        "id": "fetch",
        "name": "Fetch",
        "description": "Récupère le contenu d'URLs (HTTP GET)",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-fetch"],
    },
    {
        "id": "git",
        "name": "Git",
        "description": "Opérations Git locales (status, diff, log, commit, push)",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-git"],
    },
    {
        "id": "time",
        "name": "Time",
        "description": "Conversions timezone, dates, horloge mondiale",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-time"],
    },
    {
        "id": "sequential-thinking",
        "name": "Sequential Thinking",
        "description": "Raisonnement étape par étape structuré",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-sequential-thinking"],
    },

    # ============================================================
    # Tier 2 - Google Workspace
    # ============================================================
    {
        "id": "google-workspace",
        "name": "Google Workspace",
        "description": "Gmail, Drive, Calendar, Docs (alternative au natif)",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-google-workspace"],
        "env_required": ["GOOGLE_OAUTH_CLIENT_ID", "GOOGLE_OAUTH_CLIENT_SECRET"],
    },

    # ============================================================
    # Tier 3 - Providers Externes
    # ============================================================
    {
        "id": "github",
        "name": "GitHub",
        "description": "Manage repos, PRs, issues",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-github"],
        "env_required": ["GITHUB_TOKEN"],
    },
    {
        "id": "slack",
        "name": "Slack",
        "description": "Send messages, read channels",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-slack"],
        "env_required": ["SLACK_BOT_TOKEN"],
    },
    {
        "id": "notion",
        "name": "Notion",
        "description": "Read/write Notion databases and pages",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-notion"],
        "env_required": ["NOTION_API_KEY"],
    },
    {
        "id": "airtable",
        "name": "Airtable",
        "description": "CRUD Airtable bases and records",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-airtable"],
        "env_required": ["AIRTABLE_API_KEY"],
    },
    {
        "id": "zapier",
        "name": "Zapier",
        "description": "Trigger Zapier zaps",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-zapier"],
        "env_required": ["ZAPIER_API_KEY"],
    },
    {
        "id": "make",
        "name": "Make (Integromat)",
        "description": "Trigger Make scenarios",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-make"],
        "env_required": ["MAKE_API_KEY"],
    },
    {
        "id": "linear",
        "name": "Linear",
        "description": "Manage Linear issues and projects",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-linear"],
        "env_required": ["LINEAR_API_KEY"],
    },
]


@router.get("/presets")
async def list_presets():
    """List available preset MCP servers."""
    service = get_mcp_service()
    installed_ids = {s.name.lower().replace(" ", "-") for s in service.servers.values()}

    return [
        {
            **preset,
            "installed": preset["id"] in installed_ids,
        }
        for preset in PRESET_SERVERS
    ]


@router.post("/presets/{preset_id}/install")
async def install_preset(preset_id: str, env: dict[str, str] | None = None) -> MCPServerResponse:
    """Install a preset MCP server."""
    preset = next((p for p in PRESET_SERVERS if p["id"] == preset_id), None)

    if not preset:
        raise HTTPException(status_code=404, detail=f"Preset not found: {preset_id}")

    service = get_mcp_service()

    # Replace placeholders in args (SEC-006)
    import os
    home_dir = os.path.expanduser("~")

    # Resolve WORKING_DIRECTORY from DB preference, fallback to HOME/Documents
    working_directory = os.path.join(home_dir, "Documents")
    try:
        from sqlmodel import select as sql_select
        from app.models.entities import Preference
        from app.models.database import get_session as _get_session
        import asyncio

        async def _get_working_dir():
            from app.models.database import AsyncSessionLocal
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    sql_select(Preference).where(Preference.key == "working_directory")
                )
                pref = result.scalar_one_or_none()
                if pref and os.path.isdir(pref.value):
                    return pref.value
            return os.path.join(home_dir, "Documents")

        try:
            loop = asyncio.get_running_loop()
            # We are inside an async context, use await
            working_directory = await _get_working_dir()
        except RuntimeError:
            # No running loop, create one
            working_directory = asyncio.run(_get_working_dir())
    except Exception as e:
        logger.warning(f"Could not resolve working directory from DB: {e}. Using fallback: {working_directory}")

    args = [
        arg.replace("{HOME}", home_dir).replace("{WORKING_DIRECTORY}", working_directory)
        for arg in preset["args"]
    ]

    # Check required env vars
    env_vars = env or {}
    if "env_required" in preset:
        for var in preset["env_required"]:
            if var not in env_vars and not os.environ.get(var):
                raise HTTPException(
                    status_code=400,
                    detail=f"Missing required environment variable: {var}"
                )

    server = service.add_server(
        name=preset["name"],
        command=preset["command"],
        args=args,
        env=env_vars,
        enabled=True,
    )

    await service.start_server(server.id)

    return MCPServerResponse(**server.to_dict())
