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

// Stores persistés sous des clés SANS préfixe therese- (pièges : le CRM
// contient le pipeline clients). Garder cette liste alignée sur les
// `name:` des middlewares persist des stores.
const UNPREFIXED_PERSIST_KEYS = ['crm-storage', 'calendar-storage', 'task-storage'];

function isThereseKey(key: string): boolean {
  // therese- (stores, brouillons, consentements) ET therese: (handoff classic)
  return key.startsWith('therese-') || key.startsWith('therese:') || UNPREFIXED_PERSIST_KEYS.includes(key);
}

function purgeStorage(storage: Storage): void {
  const keys: string[] = [];
  for (let i = 0; i < storage.length; i += 1) {
    const key = storage.key(i);
    if (key && isThereseKey(key)) {
      keys.push(key);
    }
  }
  for (const key of keys) {
    storage.removeItem(key);
  }
}

export function purgeLocalPersistence(options?: { reload?: () => void }): void {
  // F1 revue : désarmer d'abord le stockage débouncé zustand, sinon le flush
  // de fermeture (pagehide, déclenché par le reload) réécrit les écritures en
  // attente APRÈS la purge - et toute écriture ultérieure (stream encore
  // vivant) est ignorée jusqu'au redémarrage.
  discardAllPendingWrites();
  purgeStorage(localStorage);
  // F2 revue : le handoff classic (sessionStorage) survit au reload
  purgeStorage(sessionStorage);
  options?.reload?.();
}
