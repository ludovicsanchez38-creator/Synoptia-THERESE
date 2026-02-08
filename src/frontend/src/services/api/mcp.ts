/**
 * THÉRÈSE v2 - MCP API Module
 *
 * Model Context Protocol - Gestion des serveurs et outils MCP.
 */

import { request } from './core';

export type MCPServerStatus = 'stopped' | 'starting' | 'running' | 'error';

export interface MCPTool {
  name: string;
  description: string;
  input_schema: Record<string, unknown>;
  server_id: string;
  server_name?: string;
}

export interface MCPServer {
  id: string;
  name: string;
  command: string;
  args: string[];
  env: Record<string, string>;
  enabled: boolean;
  status: MCPServerStatus;
  tools: MCPTool[];
  error: string | null;
  created_at: string;
}

export interface MCPServerCreate {
  name: string;
  command: string;
  args?: string[];
  env?: Record<string, string>;
  enabled?: boolean;
}

export interface MCPPreset {
  id: string;
  name: string;
  description: string;
  category?: string;
  popular?: boolean;
  url?: string;
  risk_level?: 'low' | 'medium' | 'high';
  risk_warning?: string;
  command: string;
  args: string[];
  env_required?: string[];
  installed: boolean;
}

export interface MCPStatus {
  total_servers: number;
  running_servers: number;
  total_tools: number;
  servers: Record<string, {
    name: string;
    status: MCPServerStatus;
    tools_count: number;
  }>;
}

export interface ToolCallResult {
  tool_name: string;
  server_id: string;
  success: boolean;
  result: unknown;
  error: string | null;
  execution_time_ms: number;
}

// MCP Servers
export async function listMCPServers(): Promise<MCPServer[]> {
  return request<MCPServer[]>('/api/mcp/servers');
}

export async function createMCPServer(server: MCPServerCreate): Promise<MCPServer> {
  return request<MCPServer>('/api/mcp/servers', {
    method: 'POST',
    body: JSON.stringify(server),
  });
}

export async function getMCPServer(serverId: string): Promise<MCPServer> {
  return request<MCPServer>(`/api/mcp/servers/${serverId}`);
}

export async function updateMCPServer(
  serverId: string,
  updates: Partial<MCPServerCreate>
): Promise<MCPServer> {
  return request<MCPServer>(`/api/mcp/servers/${serverId}`, {
    method: 'PUT',
    body: JSON.stringify(updates),
  });
}

export async function deleteMCPServer(serverId: string): Promise<void> {
  await request<{ deleted: boolean }>(`/api/mcp/servers/${serverId}`, {
    method: 'DELETE',
  });
}

export async function startMCPServer(serverId: string): Promise<MCPServer> {
  return request<MCPServer>(`/api/mcp/servers/${serverId}/start`, {
    method: 'POST',
  });
}

export async function stopMCPServer(serverId: string): Promise<MCPServer> {
  return request<MCPServer>(`/api/mcp/servers/${serverId}/stop`, {
    method: 'POST',
  });
}

export async function restartMCPServer(serverId: string): Promise<MCPServer> {
  return request<MCPServer>(`/api/mcp/servers/${serverId}/restart`, {
    method: 'POST',
  });
}

// MCP Tools
export async function listMCPTools(): Promise<MCPTool[]> {
  return request<MCPTool[]>('/api/mcp/tools');
}

export async function callMCPTool(
  toolName: string,
  args: Record<string, unknown> = {}
): Promise<ToolCallResult> {
  return request<ToolCallResult>('/api/mcp/tools/call', {
    method: 'POST',
    body: JSON.stringify({ tool_name: toolName, arguments: args }),
  });
}

// MCP Status
export async function getMCPStatus(): Promise<MCPStatus> {
  return request<MCPStatus>('/api/mcp/status');
}

// MCP Presets
export async function listMCPPresets(): Promise<MCPPreset[]> {
  return request<MCPPreset[]>('/api/mcp/presets');
}

export async function installMCPPreset(
  presetId: string,
  env?: Record<string, string>
): Promise<MCPServer> {
  return request<MCPServer>(`/api/mcp/presets/${presetId}/install`, {
    method: 'POST',
    body: JSON.stringify(env || {}),
  });
}
