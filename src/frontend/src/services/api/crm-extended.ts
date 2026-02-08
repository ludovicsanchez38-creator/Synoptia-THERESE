/**
 * THÉRÈSE v2 - CRM Extended API Module
 *
 * Activités, livrables, pipeline, CRM sync Google Sheets.
 */

import { API_BASE, apiFetch } from './core';
import type { Contact } from './memory';

// ContactResponse = Contact (les champs CRM sont dans Contact)
export type ContactResponse = Contact;

export interface ActivityResponse {
  id: string;
  contact_id: string;
  type: string;
  title: string;
  description: string | null;
  extra_data: string | null;
  created_at: string;
}

export interface DeliverableResponse {
  id: string;
  project_id: string;
  title: string;
  description: string | null;
  status: string;
  due_date: string | null;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface PipelineStats {
  total_contacts: number;
  stages: Record<string, { count: number; avg_score: number }>;
}

// CRM Sync types
export interface CRMSyncConfig {
  spreadsheet_id: string | null;
  last_sync: string | null;
  has_token: boolean;
  configured: boolean;
}

export interface CRMSyncStats {
  contacts_created: number;
  contacts_updated: number;
  projects_created: number;
  projects_updated: number;
  deliverables_created: number;
  deliverables_updated: number;
  errors: string[];
  total_synced: number;
}

export interface CRMSyncResponse {
  success: boolean;
  message: string;
  stats: CRMSyncStats | null;
  sync_time: string | null;
}

// Activities API
export async function listActivities(params: {
  contact_id?: string;
  type?: string;
  skip?: number;
  limit?: number;
}): Promise<ActivityResponse[]> {
  const query = new URLSearchParams();
  if (params.contact_id) query.append('contact_id', params.contact_id);
  if (params.type) query.append('type', params.type);
  if (params.skip) query.append('skip', params.skip.toString());
  if (params.limit) query.append('limit', params.limit.toString());

  const response = await apiFetch(`${API_BASE}/crm/activities?${query}`);
  if (!response.ok) { const d = await response.json().catch(() => ({})); throw new Error(d.detail || d.message || `Erreur ${response.status}`); }
  return response.json();
}

export async function createActivity(data: {
  contact_id: string;
  type: string;
  title: string;
  description?: string;
  extra_data?: string;
}): Promise<ActivityResponse> {
  const response = await apiFetch(`${API_BASE}/crm/activities`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!response.ok) { const d = await response.json().catch(() => ({})); throw new Error(d.detail || d.message || `Erreur ${response.status}`); }
  return response.json();
}

export async function deleteActivity(activityId: string): Promise<void> {
  const response = await apiFetch(`${API_BASE}/crm/activities/${activityId}`, {
    method: 'DELETE',
  });
  if (!response.ok) { const d = await response.json().catch(() => ({})); throw new Error(d.detail || d.message || `Erreur ${response.status}`); }
}

// Deliverables API
export async function listDeliverables(params: {
  project_id?: string;
  status?: string;
}): Promise<DeliverableResponse[]> {
  const query = new URLSearchParams();
  if (params.project_id) query.append('project_id', params.project_id);
  if (params.status) query.append('status', params.status);

  const response = await apiFetch(`${API_BASE}/crm/deliverables?${query}`);
  if (!response.ok) { const d = await response.json().catch(() => ({})); throw new Error(d.detail || d.message || `Erreur ${response.status}`); }
  return response.json();
}

export async function createDeliverable(data: {
  project_id: string;
  title: string;
  description?: string;
  status?: string;
  due_date?: string;
}): Promise<DeliverableResponse> {
  const response = await apiFetch(`${API_BASE}/crm/deliverables`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!response.ok) { const d = await response.json().catch(() => ({})); throw new Error(d.detail || d.message || `Erreur ${response.status}`); }
  return response.json();
}

export async function updateDeliverable(
  deliverableId: string,
  data: Partial<{
    title: string;
    description: string;
    status: string;
    due_date: string;
  }>
): Promise<DeliverableResponse> {
  const response = await apiFetch(`${API_BASE}/crm/deliverables/${deliverableId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!response.ok) { const d = await response.json().catch(() => ({})); throw new Error(d.detail || d.message || `Erreur ${response.status}`); }
  return response.json();
}

export async function deleteDeliverable(deliverableId: string): Promise<void> {
  const response = await apiFetch(`${API_BASE}/crm/deliverables/${deliverableId}`, {
    method: 'DELETE',
  });
  if (!response.ok) { const d = await response.json().catch(() => ({})); throw new Error(d.detail || d.message || `Erreur ${response.status}`); }
}

// Pipeline API
export async function updateContactStage(
  contactId: string,
  stage: string
): Promise<ContactResponse> {
  const response = await apiFetch(`${API_BASE}/crm/contacts/${contactId}/stage`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ stage }),
  });
  if (!response.ok) { const d = await response.json().catch(() => ({})); throw new Error(d.detail || d.message || `Erreur ${response.status}`); }
  return response.json();
}

export async function recalculateContactScore(contactId: string): Promise<{
  contact_id: string;
  old_score: number;
  new_score: number;
  reason: string;
}> {
  const response = await apiFetch(`${API_BASE}/crm/contacts/${contactId}/recalculate-score`, {
    method: 'POST',
  });
  if (!response.ok) { const d = await response.json().catch(() => ({})); throw new Error(d.detail || d.message || `Erreur ${response.status}`); }
  return response.json();
}

export async function getPipelineStats(): Promise<PipelineStats> {
  const response = await apiFetch(`${API_BASE}/crm/pipeline/stats`);
  if (!response.ok) { const d = await response.json().catch(() => ({})); throw new Error(d.detail || d.message || `Erreur ${response.status}`); }
  return response.json();
}

// CRM Sync (Google Sheets)
export async function getCRMSyncConfig(): Promise<CRMSyncConfig> {
  const response = await apiFetch(`${API_BASE}/api/crm/sync/config`);
  if (!response.ok) { const d = await response.json().catch(() => ({})); throw new Error(d.detail || d.message || `Erreur ${response.status}`); }
  return response.json();
}

export async function setCRMSpreadsheetId(spreadsheetId: string): Promise<CRMSyncConfig> {
  const response = await apiFetch(`${API_BASE}/api/crm/sync/config`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ spreadsheet_id: spreadsheetId }),
  });
  if (!response.ok) { const d = await response.json().catch(() => ({})); throw new Error(d.detail || d.message || `Erreur ${response.status}`); }
  return response.json();
}

export async function initiateCRMOAuth(): Promise<{
  auth_url: string;
  state: string;
  message: string;
}> {
  const response = await apiFetch(`${API_BASE}/api/crm/sync/connect`, {
    method: 'POST',
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || `Failed to initiate OAuth: ${response.statusText}`);
  }
  return response.json();
}

export async function handleCRMOAuthCallback(state: string, code: string): Promise<{
  success: boolean;
  message: string;
}> {
  const params = new URLSearchParams({ state, code });
  const response = await apiFetch(`${API_BASE}/api/crm/sync/callback?${params}`);
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || `OAuth callback failed: ${response.statusText}`);
  }
  return response.json();
}

export async function syncCRM(): Promise<CRMSyncResponse> {
  const response = await apiFetch(`${API_BASE}/api/crm/sync`, {
    method: 'POST',
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || `CRM sync failed: ${response.statusText}`);
  }
  return response.json();
}
