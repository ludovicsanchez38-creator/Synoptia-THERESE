/** File durable des décisions : aucun envoi métier ne la dépasse. */
import type { CloudGrant, CloudPurpose } from './consent';

const OUTBOX = 'therese-cloud-consent-pending';
export const CONSENT_SAVE_ERROR = 'therese:cloud-consent-save-error';
interface Decision {
  event_id: string;
  purpose: CloudPurpose;
  provider: string;
  granted: boolean;
  text_version: '3';
  data_categories: string[];
  occurred_at: string;
}
let inFlight: Promise<void> | null = null;
function pending(): Decision[] {
  return JSON.parse(localStorage.getItem(OUTBOX) || '[]');
}

export function queueConsentDecision(purpose: CloudPurpose, provider: string, granted: boolean,
  dataCategories: string[] = [], occurredAt = new Date().toISOString()): void {
  const decisions = pending();
  decisions.push({ event_id: crypto.randomUUID(), purpose, provider: provider.trim().toLowerCase(),
    granted, text_version: '3', data_categories: dataCategories, occurred_at: occurredAt });
  localStorage.setItem(OUTBOX, JSON.stringify(decisions));
  void flushConsentDecisions().catch(() => window.dispatchEvent(new Event(CONSENT_SAVE_ERROR)));
}

export function flushConsentDecisions(): Promise<void> {
  if (inFlight) return inFlight;
  if (!pending().length) return Promise.resolve();
  inFlight = (async () => {
    const { request } = await import('../services/api/core');
    while (pending().length) {
      const decision = pending()[0];
      await request('/api/consents', { method: 'POST', body: JSON.stringify(decision) });
      localStorage.setItem(OUTBOX, JSON.stringify(pending().filter(d => d.event_id !== decision.event_id)));
    }
  })().finally(() => { inFlight = null; });
  return inFlight;
}

/** Appelé après l'isolation du profil local, avant de monter les écrans métier. */
export async function synchroniserConsentements(): Promise<void> {
  const { request } = await import('../services/api/core');
  const { CLOUD_CONSENT_KEY, listCloudConsents } = await import('./consent');
  const legacy = listCloudConsents().filter(g => !g.textVersion);
  await flushConsentDecisions();
  const result = await request<{ grants: CloudGrant[] }>('/api/consents/import', {
    method: 'POST', body: JSON.stringify({ grants: legacy }),
  });
  const grants = Object.fromEntries(result.grants.map(g => [`${g.purpose}:${g.provider.toLowerCase()}`, g]));
  localStorage.setItem(CLOUD_CONSENT_KEY, JSON.stringify({ version: '2', grants }));
}
