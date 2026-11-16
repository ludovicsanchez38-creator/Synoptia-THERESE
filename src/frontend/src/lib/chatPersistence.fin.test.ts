import { expect, it, vi } from 'vitest';
import { activerSauvegardeChat, createChatStorage } from './chatPersistence';
import { __resetPersistenceForTests } from './debouncedStorage';

const poster = vi.fn().mockResolvedValue({});
vi.mock('../services/api/core', () => ({ request: (...args: unknown[]) => poster(...args) }));

it('arme une sauvegarde avant la fin du test', () => {
  __resetPersistenceForTests();
  const storage = createChatStorage();
  activerSauvegardeChat();
  storage.setItem('therese-chat', JSON.stringify({ state: {
    conversations: [{ id: 'fin-test', messages: [] }], isStreaming: false,
  } }));
  expect(poster).not.toHaveBeenCalled();
});

it('aucune sauvegarde du test précédent ne part après son démontage', async () => {
  await new Promise(resolve => setTimeout(resolve, 550));
  expect(poster).not.toHaveBeenCalled();
});

it('une requête déjà partie peut échouer après disparition de la fenêtre', async () => {
  __resetPersistenceForTests();
  vi.useFakeTimers();
  poster.mockClear();
  let rejeter!: (raison: Error) => void;
  poster.mockImplementationOnce(() => new Promise((_resolve, reject) => { rejeter = reject; }));
  try {
    const storage = createChatStorage();
    activerSauvegardeChat();
    storage.setItem('therese-chat', JSON.stringify({ state: {
      conversations: [{ id: 'en-cours', messages: [] }], isStreaming: false,
    } }));
    await vi.advanceTimersByTimeAsync(500);
    expect(poster).toHaveBeenCalledOnce();
    vi.stubGlobal('window', undefined);
    rejeter(new Error('Moteur indisponible'));
    await Promise.resolve();
    await Promise.resolve();
  } finally {
    vi.unstubAllGlobals();
    vi.useRealTimers();
  }
});
