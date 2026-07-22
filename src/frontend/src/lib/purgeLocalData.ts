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

// Stores persistés sous des clés SANS préfixe therese- (pièges : le CRM
// contient le pipeline clients). Garder cette liste alignée sur les
// `name:` des middlewares persist des stores.
const UNPREFIXED_PERSIST_KEYS = ['crm-storage', 'calendar-storage', 'task-storage'];

export function purgeLocalPersistence(options?: { reload?: () => void }): void {
  const keys: string[] = [];
  for (let i = 0; i < localStorage.length; i += 1) {
    const key = localStorage.key(i);
    if (key && (key.startsWith('therese-') || UNPREFIXED_PERSIST_KEYS.includes(key))) {
      keys.push(key);
    }
  }
  for (const key of keys) {
    localStorage.removeItem(key);
  }
  options?.reload?.();
}
