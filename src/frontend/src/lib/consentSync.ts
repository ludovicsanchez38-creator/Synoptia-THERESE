/** File durable des décisions : aucun envoi métier ne la dépasse. */
import type { CloudGrant, CloudPurpose } from './consent';

export const CONSENT_OUTBOX_PREFIX = 'therese-cloud-consent-pending';
export const UNIDENTIFIED_CONSENT_OUTBOX = 'therese:unidentified-consent-outbox';
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
  if (!legacy) return;
  // Le marqueur posé au premier démarrage n'est pas une preuve rétroactive.
  // Une file globale n'est jamais créée avec une identité native connue.
  if (!id || id.startsWith('directory:')) {
    localStorage.setItem(UNIDENTIFIED_CONSENT_OUTBOX, 'true');
  }
  if (localStorage.getItem(UNIDENTIFIED_CONSENT_OUTBOX)) return;
  const decisions: Decision[] = JSON.parse(legacy);
  const known = pending(id);
  localStorage.setItem(outbox(id), JSON.stringify(mergeConsentDecisions([decisions, known])));
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

export function isUnidentifiedDataProfile(id: string, current: string): boolean {
  return !id.startsWith('directory:')
    // Les identités numériques antérieures au nonce restent ambiguës lors
    // du passage au format durable : un inode a pu être réutilisé.
    || (/^directory:\d+:\d+:[a-f0-9]{32}$/.test(current) && /^directory:\d+:\d+:\d+$/.test(id));
}

export function hasUnidentifiedConsentDecisions(): boolean {
  const unresolved = (id: string) => {
    try {
      const decisions = pending(id);
      return !Array.isArray(decisions) || decisions.length > 0;
    } catch {
      return true;
    }
  };
  return Boolean(profile()) && (unresolved('') || (profile().startsWith('directory:')
    && storedDataProfiles().some(id => isUnidentifiedDataProfile(id, profile()) && unresolved(id))));
}

function checkIdentifiedDecisions(): void {
  if (hasUnidentifiedConsentDecisions()) {
    throw new Error('Des accords attendent dans un profil non identifié. Leur appartenance doit être établie avant de les synchroniser.');
  }
}

function mergeConsentDecisions(queues: Decision[][]): Decision[] {
  const decisions = new Map<string, Decision>();
  const predecessors = new Map<string, Set<string>>();
  for (const queue of queues) {
    let previous: string | undefined;
    for (const decision of queue) {
      if (!decisions.has(decision.event_id)) {
        decisions.set(decision.event_id, decision);
        predecessors.set(decision.event_id, new Set());
      }
      if (previous && previous !== decision.event_id) predecessors.get(decision.event_id)!.add(previous);
      previous = decision.event_id;
    }
  }
  function precedes(a: string, b: string): boolean {
    const todo = [...predecessors.get(b)!];
    const seen = new Set<string>();
    while (todo.length) {
      const id = todo.pop()!;
      if (id === a) return true;
      if (seen.has(id)) continue;
      seen.add(id);
      todo.push(...predecessors.get(id)!);
    }
    return false;
  }
  // Les dates murales ne prouvent aucun ordre. Les files et leurs événements
  // communs le prouvent ; sinon, un retrait doit gagner sur un accord concurrent.
  const prudence: [string, string][] = [];
  for (const accord of decisions.values()) {
    if (!accord.granted) continue;
    for (const retrait of decisions.values()) {
      if (!retrait.granted && retrait.purpose === accord.purpose
        && retrait.provider.toLowerCase() === accord.provider.toLowerCase()
        && !precedes(accord.event_id, retrait.event_id) && !precedes(retrait.event_id, accord.event_id)) {
        prudence.push([accord.event_id, retrait.event_id]);
      }
    }
  }
  for (const [accord, retrait] of prudence) predecessors.get(retrait)!.add(accord);
  const remaining = new Set(decisions.keys());
  const merged: Decision[] = [];
  while (remaining.size) {
    const id = [...remaining].find(candidate => [...predecessors.get(candidate)!].every(p => !remaining.has(p)));
    if (id === undefined) throw new Error('L’ordre des accords est ambigu. Les files ont été conservées sans envoi.');
    merged.push(decisions.get(id)!);
    remaining.delete(id);
  }
  return merged;
}

/** Réunit seulement les identités reconnues comme celles du profil actif. */
export function reconcileConsentOutboxes(id: string, aliases: string[]): void {
  const sources = aliases.filter(alias => alias !== id && localStorage.getItem(outbox(alias)) !== null);
  if (!sources.length) return;
  const merged = mergeConsentDecisions([pending(id), ...sources.map(pending)]);
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
  try { checkIdentifiedDecisions(); } catch (err) { return Promise.reject(err); }
  if (inFlight.has(id)) return inFlight.get(id)!;
  if (!pending(id).length) return Promise.resolve();
  const flight = (async () => {
    const { request } = await import('../services/api/core');
    checkProfile(id);
    while (pending(id).length) {
      checkProfile(id);
      checkIdentifiedDecisions();
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
    checkIdentifiedDecisions();
    if (localStorage.getItem(`${outbox(id)}:revision`) !== revision) continue;
    // Un retrait arrivé pendant l'import gagne aussi sur sa réponse périmée.
    const retraits = new Set(pending(id).filter(d => !d.granted).map(d => `${d.purpose}:${d.provider}`));
    const grants = Object.fromEntries(result.grants.filter(g => !retraits.has(`${g.purpose}:${g.provider.toLowerCase()}`)).map(g => [`${g.purpose}:${g.provider.toLowerCase()}`, g]));
    localStorage.setItem(CLOUD_CONSENT_KEY, JSON.stringify({ version: '2', grants }));
    return;
  }
}
