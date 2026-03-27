/**
 * THÉRÈSE v2 - Agents API Module
 *
 * Communication avec le système d'agents IA embarqués (Atelier).
 * Pattern SSE identique à board.ts (streamDeliberation).
 */

import { API_BASE, apiFetch, ApiError, request } from './core';

// ============================================================
// Types
// ============================================================

export type AgentId = 'katia' | 'zezette';

export type MissionPhase = 'spec' | 'analysis' | 'implementation' | 'testing' | 'review' | 'done';

export interface AgentStreamChunk {
  type: 'agent_start' | 'agent_chunk' | 'agent_done' | 'handoff' | 'tool_use' | 'test_result' | 'review_ready' | 'explanation' | 'done' | 'error';
  agent?: AgentId;
  content: string;
  task_id?: string;
  phase?: MissionPhase;
  branch?: string;
  files_changed?: string[];
  tool_name?: string;
  diff_summary?: string;
}

export interface AgentTaskResponse {
  id: string;
  title: string;
  description?: string;
  status: string;
  branch_name?: string;
  diff_summary?: string;
  files_changed?: string[];
  agent_model?: string;
  tokens_used: number;
  cost_eur: number;
  error?: string;
  created_at: string;
  updated_at: string;
  merged_at?: string;
}

export interface AgentTaskListResponse {
  tasks: AgentTaskResponse[];
  total: number;
}

export interface DiffFile {
  file_path: string;
  change_type: string;
  diff_hunk?: string;
  explanation?: string;
  additions: number;
  deletions: number;
}

export interface DiffResponse {
  task_id: string;
  branch_name?: string;
  summary?: string;
  files: DiffFile[];
  total_additions: number;
  total_deletions: number;
}

export interface AgentModelInfo {
  id: string;
  name: string;
  provider: string;
  recommended?: boolean;
}

export interface AgentConfigResponse {
  katia_enabled: boolean;
  zezette_enabled: boolean;
  katia_model: string;
  zezette_model: string;
  source_path?: string;
  available_models: AgentModelInfo[];
}

export interface AgentStatusResponse {
  git_available: boolean;
  repo_detected: boolean;
  repo_path?: string;
  current_branch?: string;
  active_tasks: number;
  katia_ready: boolean;
  zezette_ready: boolean;
}

// ============================================================
// Streaming - SSE (pattern board.ts)
// ============================================================

export async function* streamAgentRequest(
  message: string,
  sourcePath?: string,
  signal?: AbortSignal,
): AsyncGenerator<AgentStreamChunk> {
  const url = `${API_BASE}/api/agents/request`;
  const body: Record<string, string> = { message };
  if (sourcePath) body.source_path = sourcePath;

  const response = await apiFetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
    signal,
  });

  if (!response.ok) {
    const errorText = await response.text().catch(() => null);
    let message = errorText || undefined;
    if (errorText) {
      try {
        const data = JSON.parse(errorText);
        message = data.detail || data.message || errorText;
      } catch {
        // Garder le texte brut
      }
    }
    throw new ApiError(response.status, response.statusText, message);
  }

  const reader = response.body?.getReader();
  if (!reader) throw new Error('No response body');

  const decoder = new TextDecoder();
  let buffer = '';

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6).trim();
          if (!data || data === '[DONE]') continue;
          try {
            const chunk = JSON.parse(data) as AgentStreamChunk;
            yield chunk;
            if (chunk.type === 'done' || chunk.type === 'error') {
              return;
            }
          } catch {
            // Ignore parse errors
          }
        }
      }
    }
  } finally {
    reader.releaseLock();
  }
}

// ============================================================
// Tasks CRUD
// ============================================================

export async function listAgentTasks(
  limit = 50,
  status?: string,
): Promise<AgentTaskListResponse> {
  const params = new URLSearchParams({ limit: String(limit) });
  if (status) params.set('status', status);
  return request<AgentTaskListResponse>(`/api/agents/tasks?${params}`);
}

export async function getAgentTask(taskId: string): Promise<AgentTaskResponse> {
  return request<AgentTaskResponse>(`/api/agents/tasks/${taskId}`);
}

export async function getTaskDiff(taskId: string): Promise<DiffResponse> {
  return request<DiffResponse>(`/api/agents/tasks/${taskId}/diff`);
}

// ============================================================
// Review actions
// ============================================================

export async function approveTask(taskId: string): Promise<{ status: string }> {
  return request<{ status: string }>(`/api/agents/tasks/${taskId}/approve`, {
    method: 'POST',
  });
}

export async function rejectTask(taskId: string): Promise<{ status: string }> {
  return request<{ status: string }>(`/api/agents/tasks/${taskId}/reject`, {
    method: 'POST',
  });
}

export async function rollbackTask(taskId: string): Promise<{ status: string }> {
  return request<{ status: string }>(`/api/agents/tasks/${taskId}/rollback`, {
    method: 'POST',
  });
}

// ============================================================
// Config & Status
// ============================================================

export async function getAgentConfig(): Promise<AgentConfigResponse> {
  return request<AgentConfigResponse>('/api/agents/config');
}

export async function updateAgentConfig(
  config: Partial<AgentConfigResponse>,
): Promise<AgentConfigResponse> {
  return request<AgentConfigResponse>('/api/agents/config', {
    method: 'PUT',
    body: JSON.stringify(config),
  });
}

export async function getAgentStatus(): Promise<AgentStatusResponse> {
  return request<AgentStatusResponse>('/api/agents/status');
}

// ============================================================
// OpenClaw Integration (US-001)
// ============================================================

export interface AgentSessionResponse {
  id: string;
  agent_name: string;
  instruction: string;
  status: 'running' | 'done' | 'error' | 'cancelled';
  openclaw_session_id?: string;
  created_at: string;
  finished_at?: string;
  result_summary?: string;
  actions_count: number;
}

export interface AgentSessionListResponse {
  sessions: AgentSessionResponse[];
  total: number;
}

export interface SessionMessageResponse {
  role: string;
  content: string;
  timestamp?: string;
}

export interface OpenClawStatusResponse {
  connected: boolean;
  agents: Array<{ id?: string; name?: string; status?: string }>;
  url: string;
}

/**
 * Lance un agent OpenClaw depuis l Atelier.
 */
export async function dispatchToOpenClaw(
  instruction: string,
  agentName: string = 'katia',
): Promise<AgentSessionResponse> {
  return request<AgentSessionResponse>('/api/agents/dispatch', {
    method: 'POST',
    body: JSON.stringify({ instruction, agent_name: agentName }),
  });
}

/**
 * Liste les sessions OpenClaw.
 */
export async function listOpenClawSessions(
  limit = 50,
  status?: string,
): Promise<AgentSessionListResponse> {
  const params = new URLSearchParams({ limit: String(limit) });
  if (status) params.set(status, status);
  return request<AgentSessionListResponse>(`/api/agents/sessions?${params}`);
}

/**
 * Detail d une session OpenClaw.
 */
export async function getOpenClawSession(
  sessionId: string,
): Promise<AgentSessionResponse> {
  return request<AgentSessionResponse>(`/api/agents/sessions/${sessionId}`);
}

/**
 * Messages d une session OpenClaw.
 */
export async function getOpenClawSessionMessages(
  sessionId: string,
): Promise<SessionMessageResponse[]> {
  return request<SessionMessageResponse[]>(`/api/agents/sessions/${sessionId}/messages`);
}

/**
 * Envoie un message a un agent dans une session.
 */
export async function sendToOpenClawSession(
  sessionId: string,
  content: string,
): Promise<Record<string, unknown>> {
  return request<Record<string, unknown>>(`/api/agents/sessions/${sessionId}/send`, {
    method: 'POST',
    body: JSON.stringify({ content }),
  });
}

/**
 * Annule une session OpenClaw.
 */
export async function cancelOpenClawSession(
  sessionId: string,
): Promise<{ status: string }> {
  return request<{ status: string }>(`/api/agents/sessions/${sessionId}/cancel`, {
    method: 'POST',
  });
}

/**
 * Statut de la connexion OpenClaw.
 */
export async function getOpenClawStatus(): Promise<OpenClawStatusResponse> {
  return request<OpenClawStatusResponse>('/api/agents/openclaw/status');
}
