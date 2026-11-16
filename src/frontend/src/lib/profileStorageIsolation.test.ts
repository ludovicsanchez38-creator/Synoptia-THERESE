import { beforeEach, describe, expect, it, vi } from 'vitest';
import {
  DATA_PROFILE_STORAGE_KEY,
  isolateDataProfilePersistence,
} from './profileStorageIsolation';
import { installLocalStorageStub } from '../test/localStorage-stub';

function makeMemoryStorage(): Storage {
  const data = new Map<string, string>();
  return {
    getItem: (key: string) => data.get(key) ?? null,
    setItem: (key: string, value: string) => void data.set(key, String(value)),
    removeItem: (key: string) => void data.delete(key),
    clear: () => data.clear(),
    key: (index: number) => [...data.keys()][index] ?? null,
    get length() {
      return data.size;
    },
  } as Storage;
}

describe('isolateDataProfilePersistence', () => {
  beforeEach(async () => {
    installLocalStorageStub();
    Object.defineProperty(window, 'sessionStorage', {
      configurable: true,
      value: makeMemoryStorage(),
    });
    localStorage.clear();
    sessionStorage.clear();
    const { __resetPersistenceForTests } = await import('./debouncedStorage');
    __resetPersistenceForTests();
  });

  it('conserve la migration du profil historique ~/.therese', () => {
    localStorage.setItem('therese-chat', '{"state":{"conversations":["historique"]}}');

    const result = isolateDataProfilePersistence('/Users/ludo/.therese');

    expect(result).toBe('initialized');
    expect(localStorage.getItem('therese-chat')).not.toBeNull();
    expect(localStorage.getItem(DATA_PROFILE_STORAGE_KEY)).toBe('/Users/ludo/.therese');
  });

  it('purge un cache historique avant d ouvrir un profil neuf non canonique', () => {
    const reload = vi.fn();
    localStorage.setItem('therese-chat', '{"state":{"conversations":["privee"]}}');
    localStorage.setItem('calendar-storage', '{"state":{"events":["prive"]}}');
    localStorage.setItem('therese-email-store', '{"state":{"accounts":["gmail"]}}');
    sessionStorage.setItem('therese:prompt-handoff', 'confidentiel');

    const result = isolateDataProfilePersistence('/tmp/therese-demo-neuf', { reload });

    expect(result).toBe('switched');
    expect(localStorage.getItem('therese-chat')).toBeNull();
    expect(localStorage.getItem('calendar-storage')).toBeNull();
    expect(localStorage.getItem('therese-email-store')).toBeNull();
    expect(sessionStorage.getItem('therese:prompt-handoff')).toBeNull();
    expect(localStorage.getItem(DATA_PROFILE_STORAGE_KEY)).toBe('/tmp/therese-demo-neuf');
    expect(reload).toHaveBeenCalledTimes(1);
  });

  it('purge lors du passage entre deux profils deja marques', () => {
    const reload = vi.fn();
    localStorage.setItem(DATA_PROFILE_STORAGE_KEY, '/Users/ludo/.therese');
    localStorage.setItem('task-storage', '{"state":{"tasks":["client"]}}');
    localStorage.setItem('crm-storage', '{"state":{"projects":["client"]}}');

    const result = isolateDataProfilePersistence('/tmp/therese-demo-neuf', { reload });

    expect(result).toBe('switched');
    expect(localStorage.getItem('task-storage')).toBeNull();
    expect(localStorage.getItem('crm-storage')).toBeNull();
    expect(localStorage.getItem(DATA_PROFILE_STORAGE_KEY)).toBe('/tmp/therese-demo-neuf');
    expect(reload).toHaveBeenCalledTimes(1);
  });

  it('ne purge ni ne recharge le profil courant', () => {
    const reload = vi.fn();
    localStorage.setItem(DATA_PROFILE_STORAGE_KEY, '/tmp/profil-a');
    localStorage.setItem('therese-chat', 'cache-a');

    const result = isolateDataProfilePersistence('/tmp/profil-a', { reload });

    expect(result).toBe('unchanged');
    expect(localStorage.getItem('therese-chat')).toBe('cache-a');
    expect(reload).not.toHaveBeenCalled();
  });

  it.each([
    ['/Users/exemple/.therese', '/Users/exemple/.therese/'],
    ['/Users/exemple/.therese/', '/Users/exemple/.therese'],
    ['/tmp/profil-a', ' /tmp/profil-a/ '],
    ['/tmp/profil-a/', '/tmp/profil-a'],
    ['/', '///'],
  ])('B-1868 conserve le cache du même dossier : %s puis %s', (ancien, courant) => {
    const reload = vi.fn();
    localStorage.setItem(DATA_PROFILE_STORAGE_KEY, ancien);
    localStorage.setItem('therese-chat', 'conversation à conserver');

    expect(isolateDataProfilePersistence(courant, { reload })).toBe('unchanged');

    expect(localStorage.getItem('therese-chat')).toBe('conversation à conserver');
    // Les accords en attente restent rattachés à cette identité persistée.
    expect(localStorage.getItem(DATA_PROFILE_STORAGE_KEY)).toBe(ancien);
    expect(reload).not.toHaveBeenCalled();
  });

  it('B-1868 : une racine de lecteur reste distincte du chemin relatif au lecteur', () => {
    const reload = vi.fn();
    localStorage.setItem(DATA_PROFILE_STORAGE_KEY, 'C:/');
    localStorage.setItem('therese-chat', 'cache de la racine');

    expect(isolateDataProfilePersistence('C:', { reload })).toBe('switched');

    expect(localStorage.getItem('therese-chat')).toBeNull();
    expect(reload).toHaveBeenCalledOnce();
  });

  it('R1-C1 : conserve le cache sous un ancien chemin avec .. vérifié par le moteur', () => {
    const ancien = '/profils/intermediaire/../A';
    const reload = vi.fn();
    const options = { reload, verifiedAliases: [ancien] };
    localStorage.setItem(DATA_PROFILE_STORAGE_KEY, ancien);
    localStorage.setItem('therese-chat', 'conversation à conserver');

    expect(isolateDataProfilePersistence('/profils/A', options)).toBe('unchanged');
    expect(localStorage.getItem('therese-chat')).toBe('conversation à conserver');
    expect(localStorage.getItem(DATA_PROFILE_STORAGE_KEY)).toBe(ancien);
    expect(reload).not.toHaveBeenCalled();
  });

  it('R1-C1 : sans preuve du moteur, .. ne suffit pas à fusionner deux profils', () => {
    localStorage.setItem(DATA_PROFILE_STORAGE_KEY, '/profils/lien/../A');
    localStorage.setItem('therese-chat', 'cache de l’autre dossier');
    const options = { verifiedAliases: ['/profils/intermediaire/../A'] };

    expect(isolateDataProfilePersistence('/profils/A', options)).toBe('switched');
    expect(localStorage.getItem('therese-chat')).toBeNull();
  });

  it('R1-C1 : un nouveau chemin avec .. garde le cache du dossier canonique', () => {
    localStorage.setItem(DATA_PROFILE_STORAGE_KEY, '/profils/A');
    localStorage.setItem('therese-chat', 'conversation à conserver');
    const options = { canonicalDataDir: '/profils/A', reload: vi.fn() };

    expect(isolateDataProfilePersistence('/profils/intermediaire/../A', options)).toBe('unchanged');
    expect(localStorage.getItem('therese-chat')).toBe('conversation à conserver');
    expect(localStorage.getItem(DATA_PROFILE_STORAGE_KEY)).toBe('/profils/A');
    expect(options.reload).not.toHaveBeenCalled();
  });

  it('R1-C1 : un profil historique lié conserve son cache sous son identité canonique', () => {
    const options = { canonicalDataDir: '/profils/A', reload: vi.fn() };
    localStorage.setItem('therese-chat', 'conversation historique');

    expect(isolateDataProfilePersistence('/profils/.therese', options)).toBe('initialized');
    expect(localStorage.getItem(DATA_PROFILE_STORAGE_KEY)).toBe('/profils/A');
    expect(localStorage.getItem('therese-chat')).toBe('conversation historique');
    expect(options.reload).not.toHaveBeenCalled();
  });
});
