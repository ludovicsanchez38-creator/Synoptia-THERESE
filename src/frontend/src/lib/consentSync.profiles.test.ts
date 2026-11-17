import { beforeEach, expect, it, vi } from 'vitest';
import { installLocalStorageStub } from '../test/localStorage-stub';
const request = vi.hoisted(() => vi.fn());
vi.mock('../services/api/core', () => ({ request }));
import { flushConsentDecisions, reconcileConsentOutboxes, synchroniserConsentements } from './consentSync';
import { grantCloudConsent, hasCloudConsent, revokeCloudConsent } from './consent';
import { DATA_PROFILE_STORAGE_KEY, isolateDataProfilePersistence } from './profileStorageIsolation';
import { purgeLocalPersistence } from './purgeLocalData';

beforeEach(async () => {
  request.mockResolvedValue({ grants: [] });
  await flushConsentDecisions().catch(() => {});
  installLocalStorageStub();
  sessionStorage.clear();
  request.mockClear();
});

it('garde le retrait hors ligne dans A après A → B → A sans le transmettre à B', async () => {
  let moteur = '/profils/A';
  let horsLigne = true;
  let accordA = true;
  const decisions: { profil: string; granted: boolean }[] = [];
  localStorage.setItem(DATA_PROFILE_STORAGE_KEY, moteur);
  request.mockImplementation(async (path, options) => {
    if (horsLigne) throw new Error('Moteur indisponible');
    // Correctifs 0.83 : sans accord ancien, le démarrage relit le moteur par un GET sans corps.
    const body = options?.body ? JSON.parse(options.body) : {};
    if (path === '/api/consents' && options?.method === 'POST') {
      if (body.data_profile && body.data_profile !== moteur) throw new Error('Profil incorrect');
      decisions.push({ profil: moteur, granted: body.granted });
      if (moteur === '/profils/A') accordA = body.granted;
    }
    return { grants: moteur === '/profils/A' && accordA
      ? [{ purpose: 'llm', provider: 'openai', timestamp: '2026-10-01T00:00:00Z', textVersion: '3' }] : [] };
  });
  revokeCloudConsent('llm', 'openai');
  await expect(flushConsentDecisions()).rejects.toThrow('indisponible');
  moteur = '/profils/B';
  horsLigne = false;
  isolateDataProfilePersistence(moteur);
  await synchroniserConsentements();
  expect(decisions).toEqual([]);
  moteur = '/profils/A';
  isolateDataProfilePersistence(moteur);
  await synchroniserConsentements();
  expect(decisions).toEqual([{ profil: '/profils/A', granted: false }]);
  expect(hasCloudConsent('llm', 'openai')).toBe(false);
});

it.each(['/profils/A/', '/profils/intermediaire/../A'])('R1-C2 : reprend le retrait sous %s après A → B → A avant de relire les accords', async (ancien) => {
  const identiteA = 'directory:1:1:0';
  const identiteB = 'directory:1:2:0';
  const options = { verifiedAliases: [ancien], profileIdentity: identiteA };
  isolateDataProfilePersistence(ancien, options);
  const cle = `therese-cloud-consent-pending:${encodeURIComponent(identiteA)}`;
  request.mockRejectedValue(new Error('Hors ligne'));
  revokeCloudConsent('llm', 'openai');
  await expect(flushConsentDecisions()).rejects.toThrow('Hors ligne');
  const [retrait] = JSON.parse(localStorage.getItem(cle)!);
  expect(isolateDataProfilePersistence('/profils/A', options)).toBe('unchanged');

  let moteur = identiteB;
  let accordA = true;
  const decisions: unknown[] = [];
  request.mockImplementation(async (_path, options) => {
    if (options?.method === 'POST') {
      const decision = JSON.parse(options.body);
      expect(decision.data_profile).toBe(moteur);
      decisions.push(decision);
      if (moteur === identiteA) accordA = decision.granted;
    }
    return { grants: moteur === identiteA && accordA
      ? [{ purpose: 'llm', provider: 'openai', timestamp: '2026-10-01T00:00:00Z', textVersion: '3' }] : [] };
  });
  isolateDataProfilePersistence('/profils/B', { profileIdentity: moteur });
  await synchroniserConsentements();
  expect(decisions).toEqual([]);
  expect(JSON.parse(localStorage.getItem(cle)!)).toEqual([retrait]);

  moteur = identiteA;
  isolateDataProfilePersistence('/profils/A', options);
  await synchroniserConsentements();

  expect(decisions).toEqual([{ ...retrait, data_profile: moteur }]);
  expect(hasCloudConsent('llm', 'openai')).toBe(false);
  await synchroniserConsentements();
  expect(decisions).toHaveLength(1);
});

it('R1-C2 : fusionne les files équivalentes dans l’ordre sans doublon ni décision de B', async () => {
  const key = (id: string) => `therese-cloud-consent-pending:${encodeURIComponent(id)}`;
  const accord = { event_id: 'accord', purpose: 'llm', provider: 'openai', granted: true,
    text_version: '3', data_categories: [], occurred_at: '2026-10-01T00:00:00Z' };
  const retrait = { ...accord, event_id: 'retrait', granted: false, occurred_at: '2026-10-02T00:00:00Z' };
  localStorage.setItem(DATA_PROFILE_STORAGE_KEY, '/profils/B');
  localStorage.setItem(key('/profils/A/'), JSON.stringify([accord, retrait]));
  localStorage.setItem(key('/profils/A'), JSON.stringify([retrait]));
  localStorage.setItem(key('/profils/B'), JSON.stringify([{ ...accord, event_id: 'autre-profil' }]));

  isolateDataProfilePersistence('/profils/A');
  await flushConsentDecisions();

  expect(request.mock.calls.map(([, options]) => JSON.parse(options.body))).toEqual([
    { ...accord, data_profile: '/profils/A' }, { ...retrait, data_profile: '/profils/A' },
  ]);
  expect(JSON.parse(localStorage.getItem(key('/profils/A/')) || '[]')).toEqual([]);
  expect(JSON.parse(localStorage.getItem(key('/profils/B'))!)).toEqual([{ ...accord, event_id: 'autre-profil' }]);
});

it('R1-C2 : une relecture en vol ne réactive pas un accord après la fusion du retrait', async () => {
  localStorage.setItem(DATA_PROFILE_STORAGE_KEY, '/profils/A/');
  request.mockRejectedValue(new Error('Hors ligne'));
  revokeCloudConsent('llm', 'openai');
  await expect(flushConsentDecisions()).rejects.toThrow('Hors ligne');
  localStorage.setItem(DATA_PROFILE_STORAGE_KEY, '/profils/A');
  let terminer!: (value: unknown) => void;
  request.mockReset();
  request.mockImplementationOnce(() => new Promise(resolve => { terminer = resolve; }))
    .mockResolvedValue({ grants: [] });
  const synchro = synchroniserConsentements();
  await vi.waitFor(() => expect(terminer).toBeDefined());

  expect(isolateDataProfilePersistence('/profils/A')).toBe('unchanged');
  await flushConsentDecisions();
  terminer({ grants: [{ purpose: 'llm', provider: 'openai', timestamp: '2026-10-01T00:00:00Z', textVersion: '3' }] });
  await synchro;

  expect(request.mock.calls.map(([, options]) => options?.method ?? 'GET')).toEqual(['GET', 'POST', 'GET']);
  expect(hasCloudConsent('llm', 'openai')).toBe(false);
});

it('R1-C2 : une écriture de destination refusée laisse le retrait et le cache intacts', async () => {
  const source = `therese-cloud-consent-pending:${encodeURIComponent('/profils/A/')}`;
  const destination = `therese-cloud-consent-pending:${encodeURIComponent('/profils/A')}`;
  localStorage.setItem(DATA_PROFILE_STORAGE_KEY, '/profils/A/');
  request.mockRejectedValue(new Error('Hors ligne'));
  revokeCloudConsent('llm', 'openai');
  await expect(flushConsentDecisions()).rejects.toThrow('Hors ligne');
  const retrait = localStorage.getItem(source);
  localStorage.setItem(DATA_PROFILE_STORAGE_KEY, '/profils/B');
  localStorage.setItem('therese-chat', 'cache B');
  const ecrire = vi.mocked(localStorage.setItem).getMockImplementation()!;
  vi.mocked(localStorage.setItem).mockImplementation((key, value) => {
    if (key === destination) throw new Error('Stockage plein');
    ecrire(key, value);
  });
  const reload = vi.fn();
  try {
    expect(() => isolateDataProfilePersistence('/profils/A', { reload })).toThrow('Stockage plein');
    expect(localStorage.getItem(source)).toBe(retrait);
    expect(localStorage.getItem(DATA_PROFILE_STORAGE_KEY)).toBe('/profils/B');
    expect(localStorage.getItem('therese-chat')).toBe('cache B');
    expect(reload).not.toHaveBeenCalled();
  } finally {
    vi.mocked(localStorage.setItem).mockImplementation(ecrire);
  }
});

it('ne remplace pas le cache du nouveau profil avec une réponse tardive de l’ancien', async () => {
  localStorage.setItem(DATA_PROFILE_STORAGE_KEY, '/profils/A');
  let terminer!: (value: unknown) => void;
  request.mockImplementation(() => new Promise(resolve => { terminer = resolve; }));
  const synchro = synchroniserConsentements();
  await vi.waitFor(() => expect(terminer).toBeDefined());
  isolateDataProfilePersistence('/profils/B');
  terminer({ grants: [{ purpose: 'llm', provider: 'openai', timestamp: '2026-10-01T00:00:00Z' }] });
  await synchro.catch(() => {});
  expect(hasCloudConsent('llm', 'openai')).toBe(false);
});

it('un retrait acquitté pendant un import gagne sur la réponse ancienne', async () => {
  localStorage.setItem(DATA_PROFILE_STORAGE_KEY, '/profils/A');
  // Un accord v2 sans version de texte : c'est lui qui déclenche l'import (correctifs 0.83).
  localStorage.setItem('therese-cloud-consent', JSON.stringify({ version: '2', grants: {
    'llm:openai': { purpose: 'llm', provider: 'openai', timestamp: '2026-01-01T00:00:00Z' } } }));
  let terminer!: (value: unknown) => void;
  request.mockImplementationOnce(() => new Promise(resolve => { terminer = resolve; }))
    .mockResolvedValue({ grants: [] });
  const synchro = synchroniserConsentements();
  await vi.waitFor(() => expect(terminer).toBeDefined());
  revokeCloudConsent('llm', 'openai');
  await flushConsentDecisions();
  terminer({ grants: [{ purpose: 'llm', provider: 'openai', timestamp: '2026-10-01T00:00:00Z' }] });
  await synchro;
  expect(request.mock.calls[0][0]).toBe('/api/consents/import');
  expect(hasCloudConsent('llm', 'openai')).toBe(false);
});

it('reprend la file historique avant de purger les caches de A', async () => {
  localStorage.setItem(DATA_PROFILE_STORAGE_KEY, '/profils/A');
  localStorage.setItem('therese-cloud-consent-pending', JSON.stringify([
    { event_id: 'ancien-retrait', purpose: 'llm', provider: 'openai', granted: false,
      text_version: '3', data_categories: [], occurred_at: '2026-10-29T00:00:00Z' },
  ]));
  isolateDataProfilePersistence('/profils/B');
  await flushConsentDecisions();
  expect(request).not.toHaveBeenCalled();
  isolateDataProfilePersistence('/profils/A');
  await flushConsentDecisions();
  expect(JSON.parse(request.mock.calls[0][1].body)).toMatchObject({
    event_id: 'ancien-retrait', data_profile: '/profils/A', granted: false,
  });
});

it('l’effacement ne laisse pas un accord en attente revenir après le retrait du moteur', async () => {
  localStorage.setItem(DATA_PROFILE_STORAGE_KEY, '/profils/A');
  request.mockRejectedValue(new Error('Hors ligne'));
  grantCloudConsent('llm', 'openai');
  await expect(flushConsentDecisions()).rejects.toThrow();
  purgeLocalPersistence();
  await Promise.resolve();
  request.mockResolvedValue({ grants: [] });
  localStorage.setItem(DATA_PROFILE_STORAGE_KEY, '/profils/A');
  await flushConsentDecisions().catch(() => {});
  await flushConsentDecisions();
  const decisions = request.mock.calls.filter(([path]) => path === '/api/consents')
    .map(([, options]) => JSON.parse(options.body));
  expect(decisions.at(-1)).toMatchObject({ granted: false });
});

it('R2-C4 : le recul de l’horloge ne renverse pas les décisions d’une ancienne file', async () => {
  const id = '/profils/A';
  const ancien = `${id}/`;
  const accord = { event_id: 'accord', purpose: 'llm', provider: 'openai', granted: true,
    text_version: '3', data_categories: [], occurred_at: '2026-10-02T00:00:00Z' };
  const retrait = { ...accord, event_id: 'retrait', granted: false, occurred_at: '2026-10-01T00:00:00Z' };
  localStorage.setItem(DATA_PROFILE_STORAGE_KEY, id);
  localStorage.setItem(`therese-cloud-consent-pending:${encodeURIComponent(ancien)}`, JSON.stringify([accord, retrait]));
  let accorde = true;
  request.mockImplementation(async (_path, options) => {
    accorde = JSON.parse(options.body).granted;
    return { grants: [] };
  });

  reconcileConsentOutboxes(id, [ancien]);
  await flushConsentDecisions();

  expect(request.mock.calls.map(([, options]) => JSON.parse(options.body).event_id)).toEqual(['accord', 'retrait']);
  expect(accorde).toBe(false);
});

it('R2-C4 : entre files sans ordre prouvé, le retrait prime sur un accord daté plus tard', async () => {
  const id = '/profils/A';
  const ancien = `${id}/`;
  const accord = { event_id: 'accord', purpose: 'llm', provider: 'openai', granted: true,
    text_version: '3', data_categories: [], occurred_at: '2026-10-02T00:00:00Z' };
  const retrait = { ...accord, event_id: 'retrait', granted: false, occurred_at: '2026-10-01T00:00:00Z' };
  localStorage.setItem(DATA_PROFILE_STORAGE_KEY, id);
  localStorage.setItem(`therese-cloud-consent-pending:${encodeURIComponent(id)}`, JSON.stringify([retrait]));
  localStorage.setItem(`therese-cloud-consent-pending:${encodeURIComponent(ancien)}`, JSON.stringify([accord]));

  reconcileConsentOutboxes(id, [ancien]);
  await flushConsentDecisions();

  expect(request.mock.calls.map(([, options]) => JSON.parse(options.body).event_id)).toEqual(['accord', 'retrait']);
});

it('R2-C4 : un nouvel accord après retrait dans la même file garde son ordre explicite', async () => {
  const id = '/profils/A';
  const ancien = `${id}/`;
  const retrait = { event_id: 'retrait', purpose: 'llm', provider: 'openai', granted: false,
    text_version: '3', data_categories: [], occurred_at: '2026-10-02T00:00:00Z' };
  const accord = { ...retrait, event_id: 'nouvel-accord', granted: true, occurred_at: '2026-10-01T00:00:00Z' };
  localStorage.setItem(DATA_PROFILE_STORAGE_KEY, id);
  localStorage.setItem(`therese-cloud-consent-pending:${encodeURIComponent(ancien)}`, JSON.stringify([retrait, accord]));

  reconcileConsentOutboxes(id, [ancien]);
  await flushConsentDecisions();

  expect(request.mock.calls.map(([, options]) => JSON.parse(options.body).event_id)).toEqual(['retrait', 'nouvel-accord']);
});

it('R2-C4 : des ordres contradictoires restent intacts sans aucune transmission', () => {
  const id = '/profils/A';
  const ancien = `${id}/`;
  const accord = { event_id: 'accord', purpose: 'llm', provider: 'openai', granted: true,
    text_version: '3', data_categories: [], occurred_at: '2026-10-02T00:00:00Z' };
  const retrait = { ...accord, event_id: 'retrait', granted: false };
  const destination = `therese-cloud-consent-pending:${encodeURIComponent(id)}`;
  const source = `therese-cloud-consent-pending:${encodeURIComponent(ancien)}`;
  localStorage.setItem(DATA_PROFILE_STORAGE_KEY, id);
  localStorage.setItem(destination, JSON.stringify([accord, retrait]));
  localStorage.setItem(source, JSON.stringify([retrait, accord]));

  expect(() => reconcileConsentOutboxes(id, [ancien])).toThrow('L’ordre des accords est ambigu');

  expect(localStorage.getItem(destination)).toBe(JSON.stringify([accord, retrait]));
  expect(localStorage.getItem(source)).toBe(JSON.stringify([retrait, accord]));
  expect(request).not.toHaveBeenCalled();
});

it.each(['/profils/A', '/profils/lien'])('R2-C2 : la file ancienne %s sans identité historique ne part pas dans le profil courant', async (ancien) => {
  localStorage.setItem(DATA_PROFILE_STORAGE_KEY, ancien);
  localStorage.setItem('therese-chat', 'cache ancien');
  const file = `therese-cloud-consent-pending:${encodeURIComponent(ancien)}`;
  const accord = { event_id: 'accord-ancien', purpose: 'llm', provider: 'openai', granted: true,
    text_version: '3', data_categories: [], occurred_at: '2026-10-02T00:00:00Z' };
  localStorage.setItem(file, JSON.stringify([accord]));

  expect(isolateDataProfilePersistence('/profils/A', {
    canonicalDataDir: '/profils/A', verifiedAliases: [ancien], profileIdentity: 'directory:1:1:0',
  })).toBe('switched');
  await expect(synchroniserConsentements()).rejects.toThrow(/non identifié/);

  expect(localStorage.getItem('therese-chat')).toBeNull();
  expect(localStorage.getItem(file)).toBe(JSON.stringify([accord]));
  expect(request).not.toHaveBeenCalled();
});

it('R3-C2 : un retrait ancien bloque la réactivation au démarrage réel puis au rechargement', async () => {
  const ancien = '/profils/A/';
  const file = `therese-cloud-consent-pending:${encodeURIComponent(ancien)}`;
  localStorage.setItem(DATA_PROFILE_STORAGE_KEY, ancien);
  request.mockRejectedValue(new Error('Hors ligne'));
  revokeCloudConsent('llm', 'openai');
  await expect(flushConsentDecisions()).rejects.toThrow('Hors ligne');
  const retrait = localStorage.getItem(file);
  request.mockClear();
  request.mockResolvedValue({ grants: [
    { purpose: 'llm', provider: 'openai', timestamp: '2026-10-01T00:00:00Z', textVersion: '3' },
  ] });
  const options = { canonicalDataDir: '/profils/A', verifiedAliases: [ancien],
    profileIdentity: 'directory:1:1:0', reload: vi.fn() };

  for (const attendu of ['switched', 'unchanged']) {
    expect(isolateDataProfilePersistence('/profils/A', options)).toBe(attendu);
    await expect(synchroniserConsentements()).rejects.toThrow(/non identifié/);
    expect(hasCloudConsent('llm', 'openai')).toBe(false);
    expect(localStorage.getItem(file)).toBe(retrait);
    expect(request).not.toHaveBeenCalled();
  }
});

it('R3-C2 : un retrait ambigu arrivé pendant un GET empêche aussi sa publication', async () => {
  localStorage.setItem(DATA_PROFILE_STORAGE_KEY, 'directory:1:1:0');
  let terminer!: (value: unknown) => void;
  request.mockImplementationOnce(() => new Promise(resolve => { terminer = resolve; }));
  const synchro = synchroniserConsentements();
  await vi.waitFor(() => expect(terminer).toBeDefined());
  localStorage.setItem(`therese-cloud-consent-pending:${encodeURIComponent('/profils/A')}`, JSON.stringify([
    { event_id: 'retrait-ancien', purpose: 'llm', provider: 'openai', granted: false,
      text_version: '3', data_categories: [], occurred_at: '2026-10-01T00:00:00Z' },
  ]));
  terminer({ grants: [{ purpose: 'llm', provider: 'openai', timestamp: '2026-10-01T00:00:00Z', textVersion: '3' }] });
  await expect(synchro).rejects.toThrow(/non identifié/);
  expect(hasCloudConsent('llm', 'openai')).toBe(false);
});

it('R3-C3 : une file globale sans marqueur reste non identifiée après plusieurs démarrages', async () => {
  const cle = 'therese-cloud-consent-pending';
  const decisions = JSON.stringify([{ event_id: 'accord-de-A', purpose: 'llm', provider: 'openai', granted: true,
    text_version: '3', data_categories: [], occurred_at: '2026-10-01T00:00:00Z' }]);
  localStorage.setItem(cle, decisions);
  const options = { canonicalDataDir: '/profils/B', verifiedAliases: [], profileIdentity: 'directory:1:2:0', reload: vi.fn() };
  for (let demarrage = 0; demarrage < 3; demarrage += 1) {
    isolateDataProfilePersistence('/profils/B', options);
    await expect(synchroniserConsentements()).rejects.toThrow(/non identifié/);
    expect(localStorage.getItem(cle)).toBe(decisions);
    expect(localStorage.getItem(`${cle}:${encodeURIComponent(options.profileIdentity)}`)).toBeNull();
    expect(request).not.toHaveBeenCalled();
  }
  purgeLocalPersistence({ profileSwitch: true });
  isolateDataProfilePersistence('/profils/C', { ...options, profileIdentity: 'directory:1:3:0' });
  await expect(synchroniserConsentements()).rejects.toThrow(/non identifié/);
  expect(localStorage.getItem(cle)).toBe(decisions);
  expect(request).not.toHaveBeenCalled();
});

it('R3-C4 : une ancienne identité sans nonce ne permet pas de réactiver un accord', async () => {
  const ancien = 'directory:7:42:0';
  localStorage.setItem(DATA_PROFILE_STORAGE_KEY, ancien);
  const cle = `therese-cloud-consent-pending:${encodeURIComponent(ancien)}`;
  const retrait = JSON.stringify([{ event_id: 'retrait', purpose: 'llm', provider: 'openai', granted: false }]);
  localStorage.setItem(cle, retrait);
  isolateDataProfilePersistence('/profils/A', {
    profileIdentity: 'directory:7:42:0123456789abcdef0123456789abcdef', canonicalDataDir: '/profils/A', verifiedAliases: [],
  });
  await expect(synchroniserConsentements()).rejects.toThrow(/non identifié/);
  expect(localStorage.getItem(cle)).toBe(retrait);
  expect(request).not.toHaveBeenCalled();
});

it('R3-C2 : une file ancienne illisible suspend les accords sans casser leur lecture', async () => {
  localStorage.setItem(DATA_PROFILE_STORAGE_KEY, 'directory:1:1:0');
  localStorage.setItem('therese-cloud-consent', JSON.stringify({ version: '2', grants: {
    'llm:openai': { purpose: 'llm', provider: 'openai', timestamp: '2026-01-01', textVersion: '3' },
  } }));
  const cle = `therese-cloud-consent-pending:${encodeURIComponent('/profils/A')}`;
  localStorage.setItem(cle, '{incomplet');
  expect(hasCloudConsent('llm', 'openai')).toBe(false);
  await expect(synchroniserConsentements()).rejects.toThrow(/non identifié/);
  expect(localStorage.getItem(cle)).toBe('{incomplet');
  expect(request).not.toHaveBeenCalled();
});
