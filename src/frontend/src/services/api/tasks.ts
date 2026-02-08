/**
 * THÉRÈSE v2 - Tasks API Module
 *
 * Gestion des tâches utilisateur.
 */

import { API_BASE, apiFetch } from './core';

export interface Task {
  id: string;
  title: string;
  description: string | null;
  status: 'todo' | 'in_progress' | 'done' | 'cancelled';
  priority: 'low' | 'medium' | 'high' | 'urgent';
  due_date: string | null;
  project_id: string | null;
  tags: string[] | null;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface CreateTaskRequest {
  title: string;
  description?: string;
  status?: string;
  priority?: string;
  due_date?: string;
  project_id?: string;
  tags?: string[];
}

export interface UpdateTaskRequest {
  title?: string;
  description?: string;
  status?: string;
  priority?: string;
  due_date?: string;
  project_id?: string;
  tags?: string[];
}

export async function listTasks(params?: {
  status?: string;
  priority?: string;
  project_id?: string;
}): Promise<Task[]> {
  const queryParams = new URLSearchParams();
  if (params?.status) queryParams.set('status', params.status);
  if (params?.priority) queryParams.set('priority', params.priority);
  if (params?.project_id) queryParams.set('project_id', params.project_id);

  const response = await apiFetch(`${API_BASE}/api/tasks?${queryParams}`);
  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    throw new Error(data.detail || data.message || `Erreur ${response.status}`);
  }
  return response.json();
}

export async function getTask(taskId: string): Promise<Task> {
  const response = await apiFetch(`${API_BASE}/api/tasks/${taskId}`);
  if (!response.ok) { const d = await response.json().catch(() => ({})); throw new Error(d.detail || d.message || `Erreur ${response.status}`); }
  return response.json();
}

export async function createTask(req: CreateTaskRequest): Promise<Task> {
  const response = await apiFetch(`${API_BASE}/api/tasks`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  });
  if (!response.ok) { const d = await response.json().catch(() => ({})); throw new Error(d.detail || d.message || `Erreur ${response.status}`); }
  return response.json();
}

export async function updateTask(taskId: string, req: UpdateTaskRequest): Promise<Task> {
  const response = await apiFetch(`${API_BASE}/api/tasks/${taskId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  });
  if (!response.ok) { const d = await response.json().catch(() => ({})); throw new Error(d.detail || d.message || `Erreur ${response.status}`); }
  return response.json();
}

export async function deleteTask(taskId: string): Promise<any> {
  const response = await apiFetch(`${API_BASE}/api/tasks/${taskId}`, {
    method: 'DELETE',
  });
  if (!response.ok) { const d = await response.json().catch(() => ({})); throw new Error(d.detail || d.message || `Erreur ${response.status}`); }
  return response.json();
}

export async function completeTask(taskId: string): Promise<Task> {
  const response = await apiFetch(`${API_BASE}/api/tasks/${taskId}/complete`, {
    method: 'PATCH',
  });
  if (!response.ok) { const d = await response.json().catch(() => ({})); throw new Error(d.detail || d.message || `Erreur ${response.status}`); }
  return response.json();
}

export async function uncompleteTask(taskId: string): Promise<Task> {
  const response = await apiFetch(`${API_BASE}/api/tasks/${taskId}/uncomplete`, {
    method: 'PATCH',
  });
  if (!response.ok) { const d = await response.json().catch(() => ({})); throw new Error(d.detail || d.message || `Erreur ${response.status}`); }
  return response.json();
}
