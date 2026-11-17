/**
 * BUG-153 - Purge RGPD côté frontend.
 *
 * « Supprimer toutes mes données » effaçait SQLite, Qdrant et les fichiers
 * disque, mais PAS la persistance zustand du navigateur : les anciennes
 * conversations (therese-chat) étaient rechargées au démarrage et leur
 * contenu renvoyé au LLM, y compris cloud. On purge donc TOUTES les clés
 * persistées puis on recharge la fenêtre : les stores repartent vierges et
 * aucun état en mémoire ne peut réécrire dans le localStorage.
 */

import { discardAllPendingWrites } from './debouncedStorage';
import { CONSENT_OUTBOX_PREFIX, UNIDENTIFIED_CONSENT_OUTBOX, migrateConsentOutbox, revokePendingConsentGrants } from './consentSync';

// Stores persistés sous des clés SANS préfixe therese- (pièges : le CRM
// contient le pipeline clients). Garder cette liste alignée sur les
// `name:` des middlewares persist des stores.
const UNPREFIXED_PERSIST_KEYS = ['crm-storage', 'calendar-storage', 'task-storage'];
const UNASSIGNED_PROFILE_STORAGE_KEY = 'therese:unassigned-profile-data';

function isThereseKey(key: string): boolean {
  // therese- (stores, brouillons, consentements), therese: (handoff classic)
  // ET therese. : une cle ecrite avec un point survivait a la purge, faute
  // d'etre reconnue. Les trois separateurs valent le meme prefixe.
  return (
    key.startsWith('therese-') ||
    key.startsWith('therese:') ||
    key.startsWith('therese.') ||
    UNPREFIXED_PERSIST_KEYS.includes(key)
  );
}

function persistenceKeys(storage: Storage): string[] {
  const keys: string[] = [];
  for (let i = 0; i < storage.length; i += 1) {
    const key = storage.key(i);
    if (key && isThereseKey(key)
      && key !== UNIDENTIFIED_CONSENT_OUTBOX
      && key !== CONSENT_OUTBOX_PREFIX && !key.startsWith(`${CONSENT_OUTBOX_PREFIX}:`)) {
      keys.push(key);
    }
  }
  return keys;
}

function purgeStorage(storage: Storage, profileSwitch = false): void {
  const keys = persistenceKeys(storage);
  for (const key of keys) {
    if (profileSwitch && key === UNASSIGNED_PROFILE_STORAGE_KEY) continue;
    storage.removeItem(key);
  }
}

export function purgeLocalPersistence(options?: {
  reload?: () => void; profileSwitch?: boolean; unidentifiedProfile?: string | null;
}): void {
  if (options?.unidentifiedProfile !== undefined) {
    const snapshot = (storage: Storage) => Object.fromEntries(persistenceKeys(storage)
      .filter(key => key !== UNASSIGNED_PROFILE_STORAGE_KEY && key !== 'therese:data-profile')
      .map(key => [key, storage.getItem(key)]));
    const local = snapshot(localStorage);
    const session = snapshot(sessionStorage);
    if (Object.keys(local).length || Object.keys(session).length) {
      const saved = JSON.parse(localStorage.getItem(UNASSIGNED_PROFILE_STORAGE_KEY) || '[]');
      // Une graphie résolue aujourd'hui ne prouve pas l'appartenance passée.
      // Conserver les octets hors des stores actifs, AVANT toute suppression.
      localStorage.setItem(UNASSIGNED_PROFILE_STORAGE_KEY, JSON.stringify([
        ...saved, { previousProfile: options.unidentifiedProfile, local, session },
      ]));
    }
  }
  // F1 revue : désarmer d'abord le stockage débouncé zustand, sinon le flush
  // de fermeture (pagehide, déclenché par le reload) réécrit les écritures en
  // attente APRÈS la purge - et toute écriture ultérieure (stream encore
  // vivant) est ignorée jusqu'au redémarrage.
  migrateConsentOutbox(localStorage.getItem('therese:data-profile') || '');
  if (!options?.profileSwitch) revokePendingConsentGrants();
  discardAllPendingWrites();
  purgeStorage(localStorage, options?.profileSwitch);
  // F2 revue : le handoff classic (sessionStorage) survit au reload
  purgeStorage(sessionStorage, options?.profileSwitch);
  options?.reload?.();
}
