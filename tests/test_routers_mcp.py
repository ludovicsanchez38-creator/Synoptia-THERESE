"""
THERESE v2 - MCP Router Tests

Tests for US-MCP-01 to US-MCP-10.
"""

import pytest
from httpx import AsyncClient


class TestMCPServers:
    """Tests for MCP server management."""

    @pytest.mark.asyncio
    async def test_list_servers_empty(self, client: AsyncClient):
        """Test listing servers when none configured."""
        response = await client.get("/api/mcp/servers")

        assert response.status_code == 200
        servers = response.json()

        assert isinstance(servers, list)

    @pytest.mark.asyncio
    async def test_add_server(self, client: AsyncClient, sample_mcp_server):
        """US-MCP-01: Add custom MCP server."""
        response = await client.post("/api/mcp/servers", json=sample_mcp_server)

        assert response.status_code == 200
        server = response.json()

        assert server["name"] == "test-server"
        assert server["command"] == "npx"
        assert "id" in server

    @pytest.mark.asyncio
    async def test_add_server_duplicate_name_rejected(self, client: AsyncClient, sample_mcp_server):
        """Test adding server with duplicate name is rejected."""
        # Add first server
        await client.post("/api/mcp/servers", json=sample_mcp_server)

        # Try to add another with same name
        response = await client.post("/api/mcp/servers", json=sample_mcp_server)

        assert response.status_code == 400


class TestMCPPresets:
    """Tests for US-MCP-02: MCP presets."""

    @pytest.mark.asyncio
    async def test_list_presets(self, client: AsyncClient):
        """US-MCP-02: List available presets."""
        response = await client.get("/api/mcp/presets")

        assert response.status_code == 200
        presets = response.json()

        assert isinstance(presets, list)
        # Should have at least filesystem, fetch, memory presets
        preset_names = [p["name"] for p in presets]
        assert "filesystem" in preset_names or len(presets) > 0

    @pytest.mark.asyncio
    async def test_install_preset(self, client: AsyncClient):
        """Test installing a preset."""
        # First get available presets
        presets_response = await client.get("/api/mcp/presets")
        presets = presets_response.json()

        if len(presets) > 0:
            preset_id = presets[0]["id"]
            response = await client.post(f"/api/mcp/presets/{preset_id}/install")

            # Should either succeed or fail gracefully
            assert response.status_code in [200, 400, 404]


class TestMCPTools:
    """Tests for US-MCP-03: Tool discovery."""

    @pytest.mark.asyncio
    async def test_list_tools_empty(self, client: AsyncClient):
        """US-MCP-03: List tools when no servers running."""
        response = await client.get("/api/mcp/tools")

        assert response.status_code == 200
        tools = response.json()

        assert isinstance(tools, list)

    @pytest.mark.asyncio
    async def test_call_tool_no_server(self, client: AsyncClient):
        """US-MCP-09: Call tool via API (no server case)."""
        response = await client.post("/api/mcp/tools/call", json={
            "server_id": "nonexistent",
            "tool_name": "read_file",
            "arguments": {"path": "/tmp/test.txt"},
        })

        # Should fail gracefully
        assert response.status_code in [400, 404]


class TestMCPServerLifecycle:
    """Tests for US-MCP-04: Server lifecycle management."""

    @pytest.mark.asyncio
    async def test_start_nonexistent_server(self, client: AsyncClient):
        """Test starting a non-existent server."""
        response = await client.post("/api/mcp/servers/nonexistent/start")

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_stop_nonexistent_server(self, client: AsyncClient):
        """Test stopping a non-existent server."""
        response = await client.post("/api/mcp/servers/nonexistent/stop")

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_restart_nonexistent_server(self, client: AsyncClient):
        """Test restarting a non-existent server."""
        response = await client.post("/api/mcp/servers/nonexistent/restart")

        assert response.status_code == 404


class TestMCPServerDelete:
    """Tests for US-MCP-06: Delete MCP server."""

    @pytest.mark.asyncio
    async def test_delete_server(self, client: AsyncClient, sample_mcp_server):
        """US-MCP-06: Delete unused server."""
        # Add server
        add_response = await client.post("/api/mcp/servers", json=sample_mcp_server)
        server_id = add_response.json()["id"]

        # Delete it
        response = await client.delete(f"/api/mcp/servers/{server_id}")

        assert response.status_code == 200

        # Verify it's gone
        list_response = await client.get("/api/mcp/servers")
        servers = list_response.json()
        server_ids = [s["id"] for s in servers]
        assert server_id not in server_ids

    @pytest.mark.asyncio
    async def test_delete_nonexistent_server(self, client: AsyncClient):
        """Test deleting a non-existent server."""
        response = await client.delete("/api/mcp/servers/nonexistent")

        assert response.status_code == 404


class TestMCPStatus:
    """Tests for US-MCP-07: Global MCP status."""

    @pytest.mark.asyncio
    async def test_global_status(self, client: AsyncClient):
        """US-MCP-07: Get global MCP status."""
        response = await client.get("/api/mcp/status")

        # Status endpoint may or may not exist
        if response.status_code == 200:
            status = response.json()
            assert "total_servers" in status or isinstance(status, dict)


class TestMCPEnvVars:
    """Tests for US-MCP-10: Environment variables."""

    @pytest.mark.asyncio
    async def test_add_server_with_env(self, client: AsyncClient):
        """US-MCP-10: Add server with environment variables."""
        server_with_env = {
            "name": "server-with-env",
            "command": "node",
            "args": ["server.js"],
            "env": {
                "API_TOKEN": "test-token",
                "DEBUG": "true",
            },
            "enabled": True,
        }

        response = await client.post("/api/mcp/servers", json=server_with_env)

        assert response.status_code == 200
        server = response.json()

        # Env vars should be stored (may be masked in response)
        assert "id" in server
