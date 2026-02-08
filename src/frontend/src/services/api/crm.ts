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
