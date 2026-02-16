/**
 * THÉRÈSE v2 - Files API Module
 *
 * File management and indexing.
 * Sprint 2 - PERF-2.2: Extracted from monolithic api.ts
 */

import { request, apiFetch, API_BASE, ApiError } from './core';

// Types
export interface FileMetadata {
  id: string;
  path: string;
  name: string;
  extension: string;
  size: number;
  mime_type: string | null;
  chunk_count: number | null;
  indexed_at: string | null;
  created_at: string;
}

// Files API
export async function listFiles(
  limit = 50,
  offset = 0
): Promise<FileMetadata[]> {
  return request<FileMetadata[]>(`/api/files/?limit=${limit}&offset=${offset}`);
}

export async function indexFile(path: string): Promise<FileMetadata> {
  return request<FileMetadata>('/api/files/index', {
    method: 'POST',
    body: JSON.stringify({ path }),
  });
}

export async function getFile(id: string): Promise<FileMetadata> {
  return request<FileMetadata>(`/api/files/${id}`);
}

export async function getFileContent(
  id: string
): Promise<{ id: string; path: string; name: string; content: string; truncated: boolean }> {
  return request(`/api/files/${id}/content`);
}

export async function deleteFile(id: string): Promise<void> {
  await request<{ deleted: boolean }>(`/api/files/${id}`, {
    method: 'DELETE',
  });
}

/**
 * Upload un fichier vers un projet.
 * Utilise FormData (pas de Content-Type explicite, le browser ajoute le boundary).
 */
export async function uploadProjectFile(
  file: File,
  projectId: string,
): Promise<FileMetadata> {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('project_id', projectId);

  const response = await apiFetch(`${API_BASE}/api/files/upload`, {
    method: 'POST',
    body: formData,
    // Pas de Content-Type header : le browser le met automatiquement avec boundary
  });

  if (!response.ok) {
    const data = await response.json().catch(() => null);
    const message = data?.detail || `Erreur ${response.status}`;
    throw new ApiError(response.status, response.statusText, message);
  }

  return response.json();
}

/**
 * Liste les fichiers associés à un projet.
 */
export async function listProjectFiles(
  projectId: string,
): Promise<FileMetadata[]> {
  return request<FileMetadata[]>(`/api/memory/projects/${projectId}/files`);
}
