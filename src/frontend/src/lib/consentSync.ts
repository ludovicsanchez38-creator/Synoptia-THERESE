/** File durable des décisions : aucun envoi métier ne la dépasse. */
import type { CloudGrant, CloudPurpose } from './consent';

export const CONSENT_OUTBOX_PREFIX = 'therese-cloud-consent-pending';
const PROFILE = 'therese:data-profile';
function profile(): string {
  return localStorage.getItem(PROFILE) || '';
}
function outbox(id: string): string {
  return `${CONSENT_OUTBOX_PREFIX}:${encodeURIComponent(id)}`;
}

/** Identités à faire vérifier par le moteur, y compris celles des files inactives. */
export function storedDataProfiles(): string[] {
  const ids = new Set(profile() ? [profile()] : []);
  const prefix = `${CONSENT_OUTBOX_PREFIX}:`;
  for (let i = 0; i < localStorage.length; i += 1) {
    const key = localStorage.key(i);
    if (!key?.startsWith(prefix) || key.endsWith(':revision')) continue;
    const id = decodeURIComponent(key.slice(prefix.length));
    if (id) ids.add(id);
  }
  return [...ids];
}

/** Appelé avant toute purge, quand l’identité du profil précédent est encore connue. */
export function migrateConsentOutbox(id: string): void {
  const legacy = localStorage.getItem(CONSENT_OUTBOX_PREFIX);
  if (!legacy || !id) return;
  const decisions: Decision[] = JSON.parse(legacy);
  const known = pending(id);
  localStorage.setItem(outbox(id), JSON.stringify([
    ...decisions.filter(d => !known.some(k => k.event_id === d.event_id)), ...known]));
  localStorage.removeItem(CONSENT_OUTBOX_PREFIX);
}
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
const inFlight = new Map<string, Promise<void>>();
function pending(id: string): Decision[] {
  return JSON.parse(localStorage.getItem(id ? outbox(id) : CONSENT_OUTBOX_PREFIX) || '[]');
}

/** Réunit seulement les identités reconnues comme celles du profil actif. */
export function reconcileConsentOutboxes(id: string, aliases: string[]): void {
  const sources = aliases.filter(alias => alias !== id && localStorage.getItem(outbox(alias)) !== null);
  if (!sources.length) return;
  const decisions = new Map(pending(id).map(d => [d.event_id, d]));
  for (const alias of sources) {
    for (const decision of pending(alias)) {
      if (!decisions.has(decision.event_id)) decisions.set(decision.event_id, decision);
    }
  }
  const merged = [...decisions.values()].sort((a, b) => Date.parse(a.occurred_at) - Date.parse(b.occurred_at));
  // Écrire la destination avant de retirer les sources : une panne du stockage
  // laisse des copies dédoublonnables, jamais un retrait perdu.
  localStorage.setItem(outbox(id), JSON.stringify(merged));
  const revisionKey = `${outbox(id)}:revision`;
  localStorage.setItem(revisionKey, String(Number(localStorage.getItem(revisionKey) || '0') + 1));
  for (const alias of sources) {
    localStorage.removeItem(outbox(alias));
    localStorage.removeItem(`${outbox(alias)}:revision`);
  }
}

function checkProfile(id: string): void {
  if (!id || profile() !== id) {
    throw new Error('Le profil a changé. Reviens au profil concerné pour enregistrer tes accords avant de réessayer.');
  }
}

/** L'effacement des données retire aussi les accords encore en attente d'écriture. */
export function revokePendingConsentGrants(): void {
  const latest = new Map(pending(profile()).map(d => [`${d.purpose}:${d.provider}`, d]));
  for (const decision of latest.values()) {
    if (decision.granted) queueConsentDecision(decision.purpose, decision.provider, false);
  }
}

export function queueConsentDecision(purpose: CloudPurpose, provider: string, granted: boolean,
  dataCategories: string[] = [], occurredAt = new Date().toISOString()): void {
  const id = profile();
  const decisions = pending(id);
  decisions.push({ event_id: crypto.randomUUID(), purpose, provider: provider.trim().toLowerCase(),
    granted, text_version: '3', data_categories: dataCategories, occurred_at: occurredAt });
  localStorage.setItem(id ? outbox(id) : CONSENT_OUTBOX_PREFIX, JSON.stringify(decisions));
  const revisionKey = `${outbox(id)}:revision`;
  localStorage.setItem(revisionKey, String(Number(localStorage.getItem(revisionKey) || '0') + 1));
  void flushConsentDecisions().catch(() => window.dispatchEvent(new Event(CONSENT_SAVE_ERROR)));
}

export function flushConsentDecisions(): Promise<void> {
  const id = profile();
  if (inFlight.has(id)) return inFlight.get(id)!;
  if (id && JSON.parse(localStorage.getItem(CONSENT_OUTBOX_PREFIX) || '[]').length) {
    return Promise.reject(new Error('Des accords attendent dans un profil non identifié. Rouvre ton profil habituel pour les synchroniser avant de réessayer.'));
  }
  if (!pending(id).length) return Promise.resolve();
  const flight = (async () => {
    const { request } = await import('../services/api/core');
    checkProfile(id);
    while (pending(id).length) {
      checkProfile(id);
      const decision = pending(id)[0];
      await request('/api/consents', { method: 'POST',
        body: JSON.stringify({ ...decision, data_profile: id }) });
      // Une réponse tardive acquitte seulement la file de son profil d'origine.
      localStorage.setItem(outbox(id), JSON.stringify(pending(id).filter(d => d.event_id !== decision.event_id)));
    }
  })().finally(() => { inFlight.delete(id); });
  inFlight.set(id, flight);
  return flight;
}

/**
 * Appelé après l'isolation du profil local, avant de monter les écrans métier.
 *
 * Correctifs 0.83 : l'import n'écrit que s'il reste des accords v2 sans version
 * de texte, et une seule fois ; sinon on relit le moteur (`GET`). Toute erreur
 * remonte sans toucher au cache : les accords anciens restent en place et la
 * reprise est retentée au démarrage suivant. L'appelant ne bloque pas dessus.
 */
export async function synchroniserConsentements(): Promise<void> {
  const id = profile();
  const { request } = await import('../services/api/core');
  checkProfile(id);
  const { CLOUD_CONSENT_KEY, listCloudConsents } = await import('./consent');
  const legacy = listCloudConsents().filter(g => !g.textVersion);
  let importer = legacy.length > 0;
  for (;;) {
    await flushConsentDecisions();
    checkProfile(id);
    const revision = localStorage.getItem(`${outbox(id)}:revision`);
    const result = importer
      ? await request<{ grants: CloudGrant[] }>('/api/consents/import', {
        method: 'POST', body: JSON.stringify({ grants: legacy, data_profile: id }),
      })
      : await request<{ grants: CloudGrant[] }>('/api/consents');
    // Import acquitté : si une décision est arrivée entre-temps, une relecture suffit.
    importer = false;
    checkProfile(id);
    if (localStorage.getItem(`${outbox(id)}:revision`) !== revision) continue;
    // Un retrait arrivé pendant l'import gagne aussi sur sa réponse périmée.
    const retraits = new Set(pending(id).filter(d => !d.granted).map(d => `${d.purpose}:${d.provider}`));
    const grants = Object.fromEntries(result.grants.filter(g => !retraits.has(`${g.purpose}:${g.provider.toLowerCase()}`)).map(g => [`${g.purpose}:${g.provider.toLowerCase()}`, g]));
    localStorage.setItem(CLOUD_CONSENT_KEY, JSON.stringify({ version: '2', grants }));
    return;
  }
}
