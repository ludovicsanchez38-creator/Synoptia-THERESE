/**
 * THÉRÈSE v2 - Consentement transfert cloud (US-003 / RGPD-4)
 *
 * Le consentement au transfert de données vers les providers LLM cloud, donné
 * à l'onboarding, était un simple état React non persisté (pas de trace). On
 * le persiste désormais, horodaté et versionné, pour la démontrabilité.
 */
export const CLOUD_CONSENT_KEY = 'therese-cloud-consent';
export const CLOUD_CONSENT_VERSION = '1';

export interface CloudConsentRecord {
  accepted: boolean;
  version: string;
  timestamp: string;
}

export function recordCloudConsent(
  timestamp: string = new Date().toISOString()
): CloudConsentRecord {
  const record: CloudConsentRecord = {
    accepted: true,
    version: CLOUD_CONSENT_VERSION,
    timestamp,
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
