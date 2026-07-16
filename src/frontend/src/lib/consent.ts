/**
 * THÉRÈSE v2 - Consentement transfert cloud (US-003 / RGPD-4)
 *
 * Le consentement n'est demandé que lorsqu'un fournisseur cloud est actif :
 * à l'onboarding s'il est configuré, sinon au premier usage réel. La trace
 * persistée nomme le fournisseur et les catégories de données annoncées.
 */
export const CLOUD_CONSENT_KEY = 'therese-cloud-consent';
export const CLOUD_CONSENT_VERSION = '1';

export interface CloudConsentRecord {
  accepted: boolean;
  version: string;
  timestamp: string;
  provider?: string;
  dataCategories?: string[];
}

export interface CloudConsentDetails {
  provider: string;
  dataCategories: string[];
}

export function recordCloudConsent(
  timestamp: string = new Date().toISOString(),
  details?: CloudConsentDetails,
): CloudConsentRecord {
  const record: CloudConsentRecord = {
    accepted: true,
    version: CLOUD_CONSENT_VERSION,
    timestamp,
    ...details,
  };
  localStorage.setItem(CLOUD_CONSENT_KEY, JSON.stringify(record));
  return record;
}

export function getCloudConsent(): CloudConsentRecord | null {
  const raw = localStorage.getItem(CLOUD_CONSENT_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as CloudConsentRecord;
  } catch {
    return null;
  }
}
