/**
 * THÉRÈSE v2 - CRM API Module
 *
 * Endpoints specifiques au CRM (creation contact + push GSheets).
 */

import { API_BASE, apiFetch, request } from './core';
import type { ContactResponse } from './crm-extended';

export interface CreateCRMContactRequest {
  first_name: string;
  last_name?: string;
  company?: string;
  email?: string;
  phone?: string;
  source?: string;
  stage?: string;
}

/**
 * Cree un contact via le CRM endpoint.
 * Le backend le cree localement avec source='THERESE' et tente de l'ajouter au Google Sheets.
 */
export async function createCRMContact(
  data: CreateCRMContactRequest
): Promise<ContactResponse> {
  return request<ContactResponse>('/api/crm/contacts', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function importVCFContacts(file: File, updateExisting = true): Promise<{ created: number; updated: number; message: string }> {
  const formData = new FormData();
  formData.append('file', file);
  const response = await apiFetch(`${API_BASE}/api/crm/import/vcf?update_existing=${updateExisting}`, {
    method: 'POST',
    body: formData,
  });
  if (!response.ok) { const d = await response.json().catch(() => ({})); throw new Error(d.detail || d.message || `Erreur ${response.status}`); }
  return response.json();
}
