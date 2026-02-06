"""
THÉRÈSE v2 - Schemas MCP

Request/Response models pour la gestion des serveurs et outils MCP.
"""

from typing import Any

from pydantic import BaseModel


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
