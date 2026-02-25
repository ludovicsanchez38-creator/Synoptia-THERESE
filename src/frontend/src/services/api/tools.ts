/**
 * THÉRÈSE v2 - Tools API Module
 *
 * Client API pour les outils installés.
 */

import { request } from './core';

// Types

export interface ToolInput {
  name: string;
  type: string;
  label: string;
  required?: boolean;
  placeholder?: string;
  options?: string[];
  default?: string;
  help_text?: string;
}

export interface InstalledTool {
  id: string;
  skill_id: string;
  name: string;
  description: string;
  version: string;
  output_format: string;
  inputs: ToolInput[];
  source_model: string;
  created_at: string;
  generation_attempts: number;
}

export interface ToolInstallRequest {
  tool_id: string;
  name: string;
  description: string;
  output_format: string;
  code: string;
  inputs?: ToolInput[];
  test_input?: Record<string, unknown>;
  model?: string;
}

export interface ToolInstallResponse {
  success: boolean;
  tool_id?: string;
  tool_dir?: string;
  error?: string;
  attempts: number;
}

export interface ToolTestResponse {
  success: boolean;
  message: string;
}

// API Functions

export async function listInstalledTools(): Promise<InstalledTool[]> {
  return request<InstalledTool[]>('/api/tools');
}

export async function installTool(req: ToolInstallRequest): Promise<ToolInstallResponse> {
  return request<ToolInstallResponse>('/api/tools/install', {
    method: 'POST',
    body: JSON.stringify(req),
  });
}

export async function getToolManifest(toolId: string): Promise<Record<string, unknown>> {
  return request<Record<string, unknown>>(`/api/tools/${toolId}/manifest`);
}

export async function testTool(
  toolId: string,
  testInput?: Record<string, unknown>,
): Promise<ToolTestResponse> {
  return request<ToolTestResponse>(`/api/tools/${toolId}/test`, {
    method: 'POST',
    body: testInput ? JSON.stringify(testInput) : undefined,
  });
}

export async function deleteTool(toolId: string): Promise<{ success: boolean; message: string }> {
  return request<{ success: boolean; message: string }>(`/api/tools/${toolId}`, {
    method: 'DELETE',
  });
}
