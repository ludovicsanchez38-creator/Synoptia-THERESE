/**
 * BUG-153 : la purge RGPD (« Supprimer toutes mes données ») effaçait SQLite,
 * Qdrant et les fichiers disque mais PAS la persistance frontend - les
 * anciennes conversations (localStorage therese-chat) étaient rechargées au
 * démarrage et leur contenu renvoyé au LLM.
 */
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { purgeLocalPersistence } from './purgeLocalData';

// Le setup global remplace localStorage par des vi.fn() SANS stockage : on
// installe ici un vrai stub en mémoire (key/length inclus, utilisés par le
// helper pour énumérer les clés).
function installRealLocalStorage(): void {
  const data = new Map<string, string>();
  Object.defineProperty(window, 'localStorage', {
    configurable: true,
    value: {
      getItem: (key: string) => (data.has(key) ? data.get(key)! : null),
      setItem: (key: string, value: string) => void data.set(key, String(value)),
      removeItem: (key: string) => void data.delete(key),
      clear: () => data.clear(),
      key: (index: number) => [...data.keys()][index] ?? null,
      get length() {
        return data.size;
      },
    },
  });
}

describe('purgeLocalPersistence (BUG-153)', () => {
  beforeEach(() => {
    installRealLocalStorage();
  });

  it('supprime toutes les clés therese-* du localStorage', () => {
    localStorage.setItem('therese-chat', '{"conversations":[{"title":"Rapid Pare-Brise"}]}');
    localStorage.setItem('therese-email-store', '{"currentAccountId":"acc-1"}');
    localStorage.setItem('therese-personalisation', '{"nickname":"Ludo"}');

    purgeLocalPersistence();

    expect(localStorage.getItem('therese-chat')).toBeNull();
    expect(localStorage.getItem('therese-email-store')).toBeNull();
    expect(localStorage.getItem('therese-personalisation')).toBeNull();
  });

  it('supprime aussi les stores persistés sous des clés SANS préfixe (crm, calendrier, tâches)', () => {
    localStorage.setItem('crm-storage', '{"pipeline":[{"name":"Client X"}]}');
    localStorage.setItem('calendar-storage', '{"currentCalendarId":"cal-1"}');
    localStorage.setItem('task-storage', '{"tasks":[]}');

    purgeLocalPersistence();

    expect(localStorage.getItem('crm-storage')).toBeNull();
    expect(localStorage.getItem('calendar-storage')).toBeNull();
    expect(localStorage.getItem('task-storage')).toBeNull();
  });

  it('ne touche pas aux clés étrangères', () => {
    localStorage.setItem('autre-app', 'conservée');

    purgeLocalPersistence();

    expect(localStorage.getItem('autre-app')).toBe('conservée');
  });

  it('recharge la fenêtre quand demandé (stores vierges garantis)', () => {
    const reload = vi.fn();

    purgeLocalPersistence({ reload });

    expect(reload).toHaveBeenCalledTimes(1);
  });
});
