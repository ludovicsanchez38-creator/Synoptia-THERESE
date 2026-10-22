/** R2 : les textes du chat sont repris dans SQLCipher, jamais réécrits en localStorage.
 * Inventaire hérité : conversations (id, titre, dates, portée, messages), et
 * métadonnées de messages (fichiers, sources, images). Le serveur garde les
 * messages déjà acquittés et importe les seuls messages locaux manquants.
 */
import { disableStorageKey, persistenceIsDisabled, registerPendingDiscard } from './debouncedStorage';
import { request } from '../services/api/core';

const CLE = 'therese-chat';
let sauvegardeActive = false;
let migration: Promise<void> | null = null;
let lecturesEnCours = 0;

/** Une réponse du serveur actualise le store sans redevenir une écriture. */
export function appliquerLectureChat<T>(lecture: () => T): T {
  lecturesEnCours += 1;
  try {
    return lecture();
  } finally {
    lecturesEnCours -= 1;
  }
}

export function activerSauvegardeChat(): void { sauvegardeActive = true; }

export function migrerCacheChat(): Promise<void> {
  if (migration) return migration;
  disableStorageKey(CLE);
  const brut = localStorage.getItem(CLE);
  if (!brut) return Promise.resolve();
  migration = (async () => {
    const ancien = JSON.parse(brut);
    const conversations = ancien?.state?.conversations;
    if (!Array.isArray(conversations)) throw new Error('Cache du chat illisible ; il reste conservé.');
    await request('/api/chat/cache-migration', { method: 'POST', body: JSON.stringify({ conversations }) });
    // Acquittement SQL obtenu. Aucune instance différée ne peut réécrire la clé.
    localStorage.removeItem(CLE);
  })().finally(() => { migration = null; });
  return migration;
}

export function createChatStorage(): Storage {
  disableStorageKey(CLE);
  let timer: ReturnType<typeof setTimeout> | null = null;
  let pending: string | null = null;
  let dernierEtat = JSON.stringify({ conversations: [], isStreaming: false });
  let controller: AbortController | null = null;
  registerPendingDiscard(() => {
    pending = null; if (timer) clearTimeout(timer); timer = null;
    controller?.abort(); sauvegardeActive = false;
  });
  const flush = async () => {
    timer = null;
    if (!pending || !sauvegardeActive || persistenceIsDisabled()) return;
    const valeur = pending;
    const state = JSON.parse(valeur).state;
    // Un flux vivant est déjà persisté par le serveur (texte partiel compris).
    // Ne pas en importer une seconde copie avant son acquittement.
    if (state.isStreaming) return;
    try {
      controller = new AbortController();
      await request('/api/chat/cache-migration', { method: 'POST', signal: controller.signal, body: JSON.stringify({ conversations: state.conversations }) });
      if (pending === valeur) pending = null;
    } catch {
      if (!persistenceIsDisabled()) window.dispatchEvent(new CustomEvent('therese:chat-save-error'));
    } finally {
      controller = null;
    }
  };
  return {
    getItem: key => localStorage.getItem(key), // copie héritée conservée jusqu'à son acquittement
    setItem: (_key, value) => {
      if (persistenceIsDisabled()) return;
      const { conversations, isStreaming = false } = JSON.parse(value).state;
      const etat = JSON.stringify({ conversations, isStreaming });
      const modifie = etat !== dernierEtat;
      dernierEtat = etat;
      // Zustand appelle aussi ce stockage après une lecture, une navigation
      // ou un changement de métadonnée non persistée. Seule une modification
      // locale doit armer une écriture. Une lecture laisse intacte une vraie
      // sauvegarde déjà en attente (y compris après un refus du serveur).
      if (lecturesEnCours > 0) return;
      if (modifie) pending = value;
      if (pending && !timer) timer = setTimeout(() => { void flush(); }, 400);
    },
    removeItem: key => { pending = null; if (timer) clearTimeout(timer); timer = null; localStorage.removeItem(key); },
    clear: () => { pending = null; if (timer) clearTimeout(timer); timer = null; },
    key: () => null,
    get length() { return 0; },
  };
}
