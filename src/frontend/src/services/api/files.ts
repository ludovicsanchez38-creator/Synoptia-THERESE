/**
 * THÉRÈSE v2 - Files API Module
 *
 * File management and indexing.
 * Sprint 2 - PERF-2.2: Extracted from monolithic api.ts
 */

import { request } from './core';

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
