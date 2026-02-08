/**
 * THÉRÈSE v2 - RGPD API Module
 *
 * Conformité RGPD : export, anonymisation, consentement, statistiques.
 */

import { API_BASE, apiFetch } from './core';

export type RGPDBaseLegale = 'consentement' | 'contrat' | 'interet_legitime' | 'obligation_legale';

export interface RGPDExportResponse {
  contact: Record<string, unknown>;
  activities: Record<string, unknown>[];
  projects: Record<string, unknown>[];
  tasks: Record<string, unknown>[];
  exported_at: string;
}

export interface RGPDAnonymizeResponse {
  success: boolean;
  message: string;
  contact_id: string;
}

export interface RGPDRenewConsentResponse {
  success: boolean;
  message: string;
  new_expiration: string;
}

export interface RGPDStatsResponse {
  total_contacts: number;
  par_base_legale: {
    consentement: number;
    contrat: number;
    interet_legitime: number;
    obligation_legale: number;
    non_defini: number;
  };
  sans_info_rgpd: number;
  expires_ou_bientot: number;
  avec_consentement: number;
}

export interface RGPDInferResponse {
  success: boolean;
  base_legale: RGPDBaseLegale;
  date_expiration: string;
}

export async function exportContactRGPD(contactId: string): Promise<RGPDExportResponse> {
  const response = await apiFetch(`${API_BASE}/api/rgpd/export/${contactId}`);
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || `RGPD export failed: ${response.statusText}`);
  }
  return response.json();
}

export async function anonymizeContact(contactId: string, reason: string): Promise<RGPDAnonymizeResponse> {
  const response = await apiFetch(`${API_BASE}/api/rgpd/anonymize/${contactId}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ reason }),
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || `RGPD anonymize failed: ${response.statusText}`);
  }
  return response.json();
}

export async function renewContactConsent(contactId: string): Promise<RGPDRenewConsentResponse> {
  const response = await apiFetch(`${API_BASE}/api/rgpd/renew-consent/${contactId}`, {
    method: 'POST',
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || `RGPD renew consent failed: ${response.statusText}`);
  }
  return response.json();
}

export async function updateContactRGPD(
  contactId: string,
  data: { rgpd_base_legale?: RGPDBaseLegale; rgpd_consentement?: boolean }
): Promise<{ success: boolean; message: string }> {
  const response = await apiFetch(`${API_BASE}/api/rgpd/${contactId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || `RGPD update failed: ${response.statusText}`);
  }
  return response.json();
}

export async function getRGPDStats(): Promise<RGPDStatsResponse> {
  const response = await apiFetch(`${API_BASE}/api/rgpd/stats`);
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || `RGPD stats failed: ${response.statusText}`);
  }
  return response.json();
}

export async function inferContactRGPD(contactId: string): Promise<RGPDInferResponse> {
  const response = await apiFetch(`${API_BASE}/api/rgpd/infer/${contactId}`, {
    method: 'POST',
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || `RGPD infer failed: ${response.statusText}`);
  }
  return response.json();
}
