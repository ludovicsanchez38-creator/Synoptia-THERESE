/**
 * THÉRÈSE v2 - CRM API Module
 *
 * Endpoints specifiques au CRM (creation contact + push GSheets).
 */

import { request } from './core';
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

// B-1381 : l'import vCard du Pipeline est celui de Contacts (`importVCFFile`,
// services/api/memory.ts) ; la route `/api/crm/import/vcf` reste pour l'API.


export interface GoogleSheetResume {
  id: string;
  name: string;
  modified_time?: string | null;
  url?: string;
}

/**
 * B-354 : liste les feuilles Google Sheets existantes via le client API
 * (base d'URL et jeton de session), plus par un fetch relatif résolu sur
 * l'origine du frontend.
 */
export async function listGoogleSheets(): Promise<{ sheets: GoogleSheetResume[]; total: number; message?: string }> {
  return request<{ sheets: GoogleSheetResume[]; total: number; message?: string }>('/api/crm/google-sheets/list');
}
