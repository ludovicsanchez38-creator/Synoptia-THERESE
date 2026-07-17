/**
 * THÉRÈSE v2 - Consentement transfert cloud (US-003 / RGPD-4)
 *
 * V2 (revue 0.40) : un consentement par FINALITÉ et par FOURNISSEUR. La v1 ne
 * stockait qu'un enregistrement global : consentir aux images écrasait le
 * fournisseur LLM, et la dictée cloud (qui exige Groq) devenait indéblocable.
 * RGPD art. 7 : un consentement donné pour une finalité (ex. messages vers
 * OpenAI) ne vaut pas pour une autre (audio vers Groq).
 */
export const CLOUD_CONSENT_KEY = 'therese-cloud-consent';
export const CLOUD_CONSENT_VERSION = '2';

export type CloudPurpose = 'llm' | 'voice' | 'images';

export interface CloudGrant {
  purpose: CloudPurpose;
  provider: string;
  timestamp: string;
  dataCategories?: string[];
}

interface CloudConsentStoreV2 {
  version: '2';
  grants: Record<string, CloudGrant>;
}

function grantKey(purpose: CloudPurpose, provider: string): string {
  return `${purpose}:${provider.trim().toLowerCase()}`;
}

function loadStore(): CloudConsentStoreV2 {
  const empty: CloudConsentStoreV2 = { version: '2', grants: {} };
  const raw = localStorage.getItem(CLOUD_CONSENT_KEY);
  if (!raw) return empty;
  try {
    const parsed = JSON.parse(raw);
    if (parsed?.version === '2' && parsed.grants && typeof parsed.grants === 'object') {
      return parsed as CloudConsentStoreV2;
    }
    // Revue 0.40.1 (F5/F6) : PAS de migration automatique du v1. L'ancien
    // enregistrement était global et ambigu (posé indifféremment par
    // l'onboarding LLM, le Board ou le Studio Images, tantôt avec un label,
    // tantôt un id) : le reclasser dans une finalité serait deviner un
    // consentement jamais donné. On repart de zéro - chaque finalité redemande
    // UNE fois son accord précis au prochain usage.
    return empty;
  } catch {
    return empty;
  }
}

function saveStore(store: CloudConsentStoreV2): void {
  localStorage.setItem(CLOUD_CONSENT_KEY, JSON.stringify(store));
}

export function grantCloudConsent(
  purpose: CloudPurpose,
  provider: string,
  dataCategories?: string[],
  timestamp: string = new Date().toISOString(),
): CloudGrant {
  const store = loadStore();
  const grant: CloudGrant = { purpose, provider, timestamp, dataCategories };
  store.grants[grantKey(purpose, provider)] = grant;
  saveStore(store);
  return grant;
}

export function hasCloudConsent(purpose: CloudPurpose, provider?: string): boolean {
  const store = loadStore();
  if (provider !== undefined) {
    return grantKey(purpose, provider) in store.grants;
  }
  return Object.values(store.grants).some((g) => g.purpose === purpose);
}

export function revokeCloudConsent(purpose: CloudPurpose, provider: string): void {
  const store = loadStore();
  delete store.grants[grantKey(purpose, provider)];
  saveStore(store);
}

export function listCloudConsents(): CloudGrant[] {
  return Object.values(loadStore().grants);
}
