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

  it('R1-C1 : conserve le cache du chemin avec .. dont l’identité a été enregistrée', () => {
    const ancien = '/profils/intermediaire/../A';
    const reload = vi.fn();
    const options = { reload, verifiedAliases: [ancien], profileIdentity: 'directory:1:1:0' };
    localStorage.setItem(DATA_PROFILE_STORAGE_KEY, options.profileIdentity);
    localStorage.setItem('therese-chat', 'conversation à conserver');

    expect(isolateDataProfilePersistence('/profils/A', options)).toBe('unchanged');
    expect(localStorage.getItem('therese-chat')).toBe('conversation à conserver');
    expect(localStorage.getItem(DATA_PROFILE_STORAGE_KEY)).toBe(options.profileIdentity);
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

  it('R2-C2 : un ancien lien réorienté ne prouve pas à qui appartenaient le cache et les accords', () => {
    const ancien = '/profils/lien';
    const file = `therese-cloud-consent-pending:${encodeURIComponent(ancien)}`;
    const decisions = '[{"event_id":"accord-A","granted":true}]';
    localStorage.setItem(DATA_PROFILE_STORAGE_KEY, ancien);
    localStorage.setItem('therese-chat', 'cache A');
    localStorage.setItem(file, decisions);
    const options = { canonicalDataDir: '/profils/B', verifiedAliases: [ancien],
      profileIdentity: 'directory:1:2:0', reload: vi.fn() };

    expect(isolateDataProfilePersistence('/profils/lien', options)).toBe('switched');

    expect(localStorage.getItem('therese-chat')).toBeNull();
    expect(localStorage.getItem(file)).toBe(decisions);
    expect(localStorage.getItem(DATA_PROFILE_STORAGE_KEY)).toBe(options.profileIdentity);
    expect(options.reload).toHaveBeenCalledOnce();
  });

  it('R2-C2 : l’identité enregistrée conserve les graphies du même dossier puis sépare un lien réorienté', () => {
    const identiteA = 'directory:1:1:0';
    const identiteB = 'directory:1:2:0';
    isolateDataProfilePersistence('/profils/lien', { canonicalDataDir: '/profils/A', profileIdentity: identiteA });
    localStorage.setItem('therese-chat', 'cache A');
    const file = `therese-cloud-consent-pending:${encodeURIComponent(identiteA)}`;
    localStorage.setItem(file, '[{"event_id":"retrait-A","granted":false}]');
    expect(isolateDataProfilePersistence('/PROFILS/a', { profileIdentity: identiteA })).toBe('unchanged');
    expect(localStorage.getItem('therese-chat')).toBe('cache A');

    expect(isolateDataProfilePersistence('/profils/lien', {
      canonicalDataDir: '/profils/B', profileIdentity: identiteB, verifiedAliases: ['/profils/lien'],
    })).toBe('switched');

    expect(localStorage.getItem('therese-chat')).toBeNull();
    expect(localStorage.getItem(DATA_PROFILE_STORAGE_KEY)).toBe(identiteB);
    expect(localStorage.getItem(file)).toContain('retrait-A');
    expect(localStorage.getItem(`therese-cloud-consent-pending:${encodeURIComponent(identiteB)}`)).toBeNull();
  });

  it('R2-C2 : une ancienne graphie reste ambiguë même sans identité fournie par le moteur', () => {
    localStorage.setItem(DATA_PROFILE_STORAGE_KEY, '/profils/lien');
    localStorage.setItem('therese-chat', 'cache A');
    expect(isolateDataProfilePersistence('/profils/B', { verifiedAliases: ['/profils/lien'] })).toBe('switched');
    expect(localStorage.getItem('therese-chat')).toBeNull();
  });

  it('R2-C3 : les espaces du dossier canonique restent significatifs', () => {
    localStorage.setItem(DATA_PROFILE_STORAGE_KEY, '/profils/A');
    localStorage.setItem('therese-chat', 'cache A');
    const options = { canonicalDataDir: '/profils/A ', verifiedAliases: [], reload: vi.fn() };

    expect(isolateDataProfilePersistence('/profils/A ', options)).toBe('switched');

    expect(localStorage.getItem('therese-chat')).toBeNull();
    expect(localStorage.getItem(DATA_PROFILE_STORAGE_KEY)).toBe('/profils/A ');
    expect(options.reload).toHaveBeenCalledOnce();
  });

  it('R2-C3 : les espaces autour d’un chemin ne sont pas une variante du même dossier', () => {
    localStorage.setItem(DATA_PROFILE_STORAGE_KEY, '/tmp/profil-a');
    localStorage.setItem('therese-chat', 'cache A');
    const reload = vi.fn();
    expect(isolateDataProfilePersistence(' /tmp/profil-a/ ', { reload })).toBe('switched');
    expect(localStorage.getItem('therese-chat')).toBeNull();
    expect(localStorage.getItem(DATA_PROFILE_STORAGE_KEY)).toBe(' /tmp/profil-a/ ');
    expect(reload).toHaveBeenCalledOnce();
  });

  it('R2-C3 : une normalisation lexicale ne passe pas outre le refus du moteur', () => {
    localStorage.setItem(DATA_PROFILE_STORAGE_KEY, '/profils/A/');
    localStorage.setItem('therese-chat', 'cache A');
    expect(isolateDataProfilePersistence('/profils/A', { verifiedAliases: [] })).toBe('switched');
    expect(localStorage.getItem('therese-chat')).toBeNull();
  });

  it.each(['/profils/A', '/profils/lien', null])('R3-C1 : garde les données anciennes de %s en attente avec les options de App', (ancien) => {
    if (ancien) localStorage.setItem(DATA_PROFILE_STORAGE_KEY, ancien);
    const conversations = '{"state":{"conversations":[{"id":"locale-a"}]}}';
    localStorage.setItem('therese-chat', conversations);
    localStorage.setItem('therese-email-draft:1', 'brouillon local');
    localStorage.setItem('crm-storage', 'clients locaux');
    sessionStorage.setItem('therese:prompt-handoff', 'texte en attente');
    const options = { canonicalDataDir: '/profils/A', verifiedAliases: ancien ? [ancien] : [],
      profileIdentity: 'directory:1:1:0', reload: vi.fn() };

    expect(isolateDataProfilePersistence('/profils/A', options)).toBe('switched');
    const sauvegarde = localStorage.getItem('therese:unassigned-profile-data');
    expect(sauvegarde, 'Les données anciennes doivent rester récupérables').not.toBeNull();
    expect(JSON.parse(sauvegarde!)).toEqual([{
      previousProfile: ancien,
      local: { 'therese-chat': conversations, 'therese-email-draft:1': 'brouillon local', 'crm-storage': 'clients locaux' },
      session: { 'therese:prompt-handoff': 'texte en attente' },
    }]);
    expect(localStorage.getItem('therese-chat')).toBeNull();
    expect(localStorage.getItem('therese-email-draft:1')).toBeNull();
    expect(sessionStorage.getItem('therese:prompt-handoff')).toBeNull();
    expect(options.reload).toHaveBeenCalledOnce();
    expect(isolateDataProfilePersistence('/profils/A', options)).toBe('unchanged');
    isolateDataProfilePersistence('/profils/B', { ...options, profileIdentity: 'directory:1:2:0' });
    expect(localStorage.getItem('therese:unassigned-profile-data')).toBe(sauvegarde);
  });

  it('R3-C1 : refuse la purge si la mise en attente ne peut pas être écrite', () => {
    localStorage.setItem(DATA_PROFILE_STORAGE_KEY, '/profils/A');
    localStorage.setItem('therese-email-draft:1', 'brouillon local');
    const ecrire = vi.mocked(localStorage.setItem).getMockImplementation()!;
    vi.mocked(localStorage.setItem).mockImplementation((key, value) => {
      if (key === 'therese:unassigned-profile-data') throw new Error('Stockage plein');
      ecrire(key, value);
    });
    const reload = vi.fn();
    expect(() => isolateDataProfilePersistence('/profils/A', {
      canonicalDataDir: '/profils/A', verifiedAliases: ['/profils/A'], profileIdentity: 'directory:1:1:0', reload,
    })).toThrow('Stockage plein');
    expect(localStorage.getItem('therese-email-draft:1')).toBe('brouillon local');
    expect(localStorage.getItem(DATA_PROFILE_STORAGE_KEY)).toBe('/profils/A');
    expect(reload).not.toHaveBeenCalled();
  });

  it('R3-C4 : la transition depuis une identité fondée sur l’inode conserve aussi les données', () => {
    localStorage.setItem(DATA_PROFILE_STORAGE_KEY, 'directory:7:42:0');
    localStorage.setItem('therese-chat', 'conversation avant nonce');
    isolateDataProfilePersistence('/profils/A', {
      profileIdentity: 'directory:7:42:0123456789abcdef0123456789abcdef', canonicalDataDir: '/profils/A', verifiedAliases: [],
    });
    expect(localStorage.getItem('therese:unassigned-profile-data')).toContain('conversation avant nonce');
    expect(localStorage.getItem('therese-chat')).toBeNull();
  });
});
