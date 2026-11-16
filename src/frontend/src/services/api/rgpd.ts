import { notifyMemoryChange } from './memoryCards';
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
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || `L’export des données personnelles a échoué (erreur ${response.status}).`);
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
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || `L’anonymisation du contact a échoué (erreur ${response.status}).`);
  }
  const resultat = await response.json();
  notifyMemoryChange();
  return resultat;
}

export async function renewContactConsent(contactId: string): Promise<RGPDRenewConsentResponse> {
  const response = await apiFetch(`${API_BASE}/api/rgpd/renew-consent/${contactId}`, {
    method: 'POST',
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || `Le renouvellement du consentement a échoué (erreur ${response.status}).`);
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
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || `La mise à jour des informations de confidentialité a échoué (erreur ${response.status}).`);
  }
  return response.json();
}

export async function getRGPDStats(): Promise<RGPDStatsResponse> {
  const response = await apiFetch(`${API_BASE}/api/rgpd/stats`);
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || `Le chargement des statistiques de confidentialité a échoué (erreur ${response.status}).`);
  }
  return response.json();
}

export async function inferContactRGPD(contactId: string): Promise<RGPDInferResponse> {
  const response = await apiFetch(`${API_BASE}/api/rgpd/infer/${contactId}`, {
    method: 'POST',
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || `La détermination de la base légale a échoué (erreur ${response.status}).`);
  }
  return response.json();
}


// ============================================================
// Purge RGPD automatique (US-017)
// ============================================================

export interface PurgeSettingsResponse {
  enabled: boolean;
  months: number;
}

export async function getPurgeSettings(): Promise<PurgeSettingsResponse> {
  const response = await apiFetch(`${API_BASE}/api/rgpd/purge/settings`);
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || `La lecture des réglages de suppression automatique a échoué (erreur ${response.status}).`);
  }
  return response.json();
}

export async function updatePurgeSettings(
  enabled: boolean,
  months: number,
): Promise<PurgeSettingsResponse> {
  const response = await apiFetch(
    `${API_BASE}/api/rgpd/purge/settings?enabled=${enabled}&months=${months}`,
    { method: 'PUT' },
  );
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || `L’enregistrement des réglages de suppression automatique a échoué (erreur ${response.status}).`);
  }
  return response.json();
}

export async function togglePurgeExclude(
  contactId: string,
): Promise<{ success: boolean; purge_excluded: boolean; message: string }> {
  const response = await apiFetch(`${API_BASE}/api/rgpd/contacts/${contactId}/purge-exclude`, {
    method: 'PATCH',
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || `La modification de la protection du contact contre la suppression automatique a échoué (erreur ${response.status}).`);
  }
  return response.json();
}
