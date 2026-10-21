import { afterEach, beforeEach, expect, it, vi } from 'vitest';
import { createChatStorage, migrerCacheChat, activerSauvegardeChat } from './chatPersistence';
import { createDebouncedStorage, __resetPersistenceForTests } from './debouncedStorage';

const poster = vi.fn();
vi.mock('../services/api/core', () => ({ request: (...args: unknown[]) => poster(...args) }));
beforeEach(() => {
  vi.useFakeTimers();
  const donnees = new Map<string, string>();
  Object.defineProperty(window, 'localStorage', { configurable: true, value: {
    getItem: (k: string) => donnees.get(k) ?? null,
    setItem: (k: string, v: string) => donnees.set(k, v),
    removeItem: (k: string) => donnees.delete(k), clear: () => donnees.clear(),
  } });
  poster.mockReset(); __resetPersistenceForTests();
});
afterEach(() => vi.useRealTimers());

it('synchronise le cache hérité avant de le retirer et neutralise son écriture différée', async () => {
  const ancien = createDebouncedStorage(400);
  const valeur = JSON.stringify({ state: { conversations: [{ id: 'conv', title: 'Titre privé', messages: [{ content: 'Fiche privée' }] }] } });
  localStorage.setItem('therese-chat', valeur);
  ancien.setItem('therese-chat', valeur);
  const storage = createChatStorage();
  expect(storage.getItem('therese-chat')).toBe(valeur);
  let acquitter!: () => void;
  poster.mockImplementation(() => new Promise<void>(r => { acquitter = r; }));
  const migration = migrerCacheChat();
  expect(localStorage.getItem('therese-chat')).toBe(valeur);
  acquitter();
  await migration;
  await vi.advanceTimersByTimeAsync(1000);
  expect(localStorage.getItem('therese-chat')).toBeNull();
});

it('garde le cache et autorise une reprise si la base refuse la migration', async () => {
  const valeur = JSON.stringify({ state: { conversations: [{ id: 'conv', messages: [{ content: 'Tour non acquitté' }] }] } });
  localStorage.setItem('therese-chat', valeur);
  poster.mockRejectedValueOnce(new Error('indisponible')).mockResolvedValue({});
  await expect(migrerCacheChat()).rejects.toThrow();
  expect(localStorage.getItem('therese-chat')).toBe(valeur);
  await migrerCacheChat();
  expect(localStorage.getItem('therese-chat')).toBeNull();
});

it('les nouveaux textes sont sauvegardés côté base et jamais dans le navigateur', async () => {
  poster.mockResolvedValue({});
  const storage = createChatStorage();
  activerSauvegardeChat();
  storage.setItem('therese-chat', JSON.stringify({ state: { conversations: [{ id: 'conv', title: 'Privé', messages: [{ content: 'Texte privé' }] }], isStreaming: false } }));
  await vi.advanceTimersByTimeAsync(500);
  expect(poster).toHaveBeenCalledWith('/api/chat/cache-migration', expect.objectContaining({ method: 'POST' }));
  expect(localStorage.getItem('therese-chat')).toBeNull();
});

it('une purge désarme aussi les sauvegardes de textes encore différées', async () => {
  const { discardAllPendingWrites } = await import('./debouncedStorage');
  poster.mockResolvedValue({});
  const storage = createChatStorage();
  activerSauvegardeChat();
  storage.setItem('therese-chat', JSON.stringify({ state: { conversations: [{ id: 'conv', title: 'À purger', messages: [] }], isStreaming: false } }));
  discardAllPendingWrites();
  await vi.advanceTimersByTimeAsync(1000);
  expect(poster).not.toHaveBeenCalled();
});
