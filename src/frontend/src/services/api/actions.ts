/**
 * THERESE v2 - Actions API Client
 *
 * Client API pour le endpoint /api/actions (agents actionnables).
 */

import { request } from './core';

export interface ActionAgentParam {
  id: string;
  label: string;
  type: string;
  required: boolean;
  placeholder: string;
  options: string[];
}

export interface ActionAgent {
  id: string;
  name: string;
  description: string;
  icon: string;
  category: string;
  steps_count: number;
  tools: string[];
  params: ActionAgentParam[];
}

export interface TaskStep {
  step_id: string;
  label: string;
  status: 'pending' | 'running' | 'completed' | 'skipped' | 'error';
  content: string;
  started_at: string | null;
  completed_at: string | null;
  error: string | null;
}

export interface TaskState {
  task_id: string;
  agent_id: string;
  agent_name: string;
  status: 'pending' | 'running' | 'completed' | 'cancelled' | 'error';
  params: Record<string, string>;
  steps: TaskStep[];
  result: string;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
  error: string | null;
  progress: number;
}

/**
 * Liste tous les agents actions disponibles.
 */
export async function fetchActions(): Promise<ActionAgent[]> {
  return request<ActionAgent[]>('/api/actions');
}

/**
 * Recupere les details d'un agent action.
 */
export async function fetchAction(agentId: string): Promise<ActionAgent> {
  return request<ActionAgent>(`/api/actions/${encodeURIComponent(agentId)}`);
}

/**
 * Lance l'execution d'un agent action.
 */
export async function runAction(
  agentId: string,
  params: Record<string, string> = {},
): Promise<TaskState> {
  return request<TaskState>(`/api/actions/${encodeURIComponent(agentId)}/run`, {
    method: 'POST',
    body: JSON.stringify({ params }),
  });
}

/**
 * Recupere le statut d'une tache.
 */
export async function fetchTask(taskId: string): Promise<TaskState> {
  return request<TaskState>(`/api/actions/tasks/${encodeURIComponent(taskId)}`);
}

/**
 * Liste toutes les taches.
 */
export async function fetchTasks(): Promise<TaskState[]> {
  return request<TaskState[]>('/api/actions/tasks/list');
}

/**
 * Annule une tache en cours.
 */
export async function cancelTask(taskId: string): Promise<void> {
  await request(`/api/actions/tasks/${encodeURIComponent(taskId)}`, {
    method: 'DELETE',
  });
}
