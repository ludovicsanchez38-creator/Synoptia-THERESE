/**
 * THÉRÈSE v2 - Memory API Module
 *
 * Contacts, projects, and memory search.
 * Sprint 2 - PERF-2.2: Extracted from monolithic api.ts
 */

import { request } from './core';

// Types
export interface Contact {
  id: string;
  first_name: string | null;
  last_name: string | null;
  company: string | null;
  email: string | null;
  phone: string | null;
  notes: string | null;
  tags: string | null;
  created_at: string;
  updated_at: string;
  // RGPD fields (Phase 6)
  rgpd_base_legale?: string | null;
  rgpd_date_collecte?: string | null;
  rgpd_date_expiration?: string | null;
  rgpd_consentement?: boolean;
}

export interface Project {
  id: string;
  name: string;
  description: string | null;
  contact_id: string | null;
  status: string;
  budget: number | null;
  notes: string | null;
  tags: string | null;
  created_at: string;
  updated_at: string;
}

// E3-05: Memory Scope Types
export type MemoryScope = 'global' | 'project' | 'conversation';

export interface ScopeFilter {
  scope?: MemoryScope;
  scope_id?: string;
  include_global?: boolean;
}

// E3-06: Delete Response
export interface DeleteResponse {
  deleted: boolean;
  id: string;
  cascade_deleted: Record<string, number>;
}

// Contacts
export async function listContacts(
  offset = 0,
  limit = 50
): Promise<Contact[]> {
  return request<Contact[]>(`/api/memory/contacts?offset=${offset}&limit=${limit}`);
}

export async function getContact(id: string): Promise<Contact> {
  return request<Contact>(`/api/memory/contacts/${id}`);
}

export async function createContact(
  data: Partial<Contact>
): Promise<Contact> {
  return request<Contact>('/api/memory/contacts', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function updateContact(
  id: string,
  data: Partial<Contact>
): Promise<Contact> {
  return request<Contact>(`/api/memory/contacts/${id}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  });
}

export async function deleteContact(id: string): Promise<void> {
  await request<{ ok: boolean }>(`/api/memory/contacts/${id}`, {
    method: 'DELETE',
  });
}

// E3-05: List contacts with scope filter
export async function listContactsWithScope(
  offset = 0,
  limit = 50,
  scopeFilter?: ScopeFilter
): Promise<Contact[]> {
  const params = new URLSearchParams({
    offset: offset.toString(),
    limit: limit.toString(),
  });

  if (scopeFilter?.scope) {
    params.set('scope', scopeFilter.scope);
  }
  if (scopeFilter?.scope_id) {
    params.set('scope_id', scopeFilter.scope_id);
  }
  if (scopeFilter?.include_global !== undefined) {
    params.set('include_global', scopeFilter.include_global.toString());
  }

  return request<Contact[]>(`/api/memory/contacts?${params.toString()}`);
}

// E3-06: Delete contact with cascade option
export async function deleteContactWithCascade(
  id: string,
  cascade = false
): Promise<DeleteResponse> {
  return request<DeleteResponse>(
    `/api/memory/contacts/${id}?cascade=${cascade}`,
    { method: 'DELETE' }
  );
}

// Projects
export async function listProjects(
  offset = 0,
  limit = 50
): Promise<Project[]> {
  return request<Project[]>(`/api/memory/projects?offset=${offset}&limit=${limit}`);
}

export async function getProject(id: string): Promise<Project> {
  return request<Project>(`/api/memory/projects/${id}`);
}

export async function createProject(
  data: Partial<Project>
): Promise<Project> {
  return request<Project>('/api/memory/projects', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function updateProject(
  id: string,
  data: Partial<Project>
): Promise<Project> {
  return request<Project>(`/api/memory/projects/${id}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  });
}

export async function deleteProject(id: string): Promise<void> {
  await request<{ ok: boolean }>(`/api/memory/projects/${id}`, {
    method: 'DELETE',
  });
}

// E3-05: List projects with scope filter
export async function listProjectsWithScope(
  offset = 0,
  limit = 50,
  scopeFilter?: ScopeFilter
): Promise<Project[]> {
  const params = new URLSearchParams({
    offset: offset.toString(),
    limit: limit.toString(),
  });

  if (scopeFilter?.scope) {
    params.set('scope', scopeFilter.scope);
  }
  if (scopeFilter?.scope_id) {
    params.set('scope_id', scopeFilter.scope_id);
  }
  if (scopeFilter?.include_global !== undefined) {
    params.set('include_global', scopeFilter.include_global.toString());
  }

  return request<Project[]>(`/api/memory/projects?${params.toString()}`);
}

// E3-06: Delete project with cascade option
export async function deleteProjectWithCascade(
  id: string,
  cascade = false
): Promise<DeleteResponse> {
  return request<DeleteResponse>(
    `/api/memory/projects/${id}?cascade=${cascade}`,
    { method: 'DELETE' }
  );
}

// Memory Search
export async function searchMemory(
  query: string,
  types: string[] = ['contacts', 'projects']
): Promise<{ contacts?: Contact[]; projects?: Project[] }> {
  return request('/api/memory/search', {
    method: 'POST',
    body: JSON.stringify({ query, types }),
  });
}
