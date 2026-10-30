import { beforeEach, expect, it, vi } from 'vitest';
import { installLocalStorageStub } from '../test/localStorage-stub';
const request = vi.hoisted(() => vi.fn());
vi.mock('../services/api/core', () => ({ request }));
import { flushConsentDecisions, synchroniserConsentements } from './consentSync';
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
