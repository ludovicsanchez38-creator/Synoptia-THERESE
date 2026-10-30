/**
 * Démarrage et accords (correctifs 0.83, parcours e2e 07).
 *
 * `App.tsx` appelle `synchroniserConsentements()` à chaque démarrage. La
 * version du lot confidentialité postait `/api/consents/import` même sans
 * accord ancien à reprendre : onze écritures dans un parcours qui n'en tolère
 * aucune. L'import ne part que s'il reste des accords v2 sans version de
 * texte, une seule fois ; sinon le démarrage relit le moteur.
 */
import { beforeEach, expect, it, vi } from 'vitest';
import { installLocalStorageStub } from '../test/localStorage-stub';
const request = vi.hoisted(() => vi.fn());
vi.mock('../services/api/core', () => ({ request }));
import { flushConsentDecisions, synchroniserConsentements } from './consentSync';
import {
  CLOUD_CONSENT_KEY, grantCloudConsent, hasCloudConsent, listCloudConsents, revokeCloudConsent,
} from './consent';

const ANCIEN = { purpose: 'llm', provider: 'openai', timestamp: '2026-01-01T12:00:00Z' };
const REPRIS = { ...ANCIEN, dataCategories: [], textVersion: '2' };

function appels(): string[] {
  return request.mock.calls.map(([chemin, options]) => `${options?.method ?? 'GET'} ${chemin}`);
}

function poserLeCache(grants: Record<string, unknown>): void {
  localStorage.setItem(CLOUD_CONSENT_KEY, JSON.stringify({ version: '2', grants }));
}

beforeEach(async () => {
  request.mockResolvedValue({ grants: [] });
  await flushConsentDecisions().catch(() => {});
  installLocalStorageStub();
  localStorage.setItem('therese:data-profile', '/profils/test');
  request.mockReset();
});

it('sans accord ancien à reprendre, relit le moteur sans aucune écriture', async () => {
  request.mockResolvedValue({ grants: [{ ...REPRIS, textVersion: '3' }], history: [] });

  await synchroniserConsentements();

  expect(appels()).toEqual(['GET /api/consents']);
  expect(hasCloudConsent('llm', 'openai')).toBe(true);
});

it('un cache déjà repris (accords versionnés) ne repart pas à l’import', async () => {
  poserLeCache({ 'llm:openai': REPRIS, 'images:gpt-image-2': {
    purpose: 'images', provider: 'gpt-image-2', timestamp: '2026-10-01T00:00:00Z', textVersion: '3' } });
  request.mockResolvedValue({ grants: [REPRIS], history: [] });

  await synchroniserConsentements();

  expect(appels()).toEqual(['GET /api/consents']);
  // Le moteur fait foi : l'accord images qu'il ne connaît pas ne reste pas affiché.
  expect(hasCloudConsent('llm', 'openai')).toBe(true);
  expect(hasCloudConsent('images', 'gpt-image-2')).toBe(false);
});

it('importe les accords anciens une seule fois, même si une décision arrive pendant l’import', async () => {
  poserLeCache({ 'llm:openai': ANCIEN });
  let terminer!: () => void;
  const moteur: Record<string, unknown>[] = [REPRIS];
  request.mockImplementation((chemin: string, options?: { method?: string; body?: string }) => {
    if (chemin === '/api/consents/import') {
      return new Promise(resolve => { terminer = () => resolve({ grants: moteur }); });
    }
    if (options?.method === 'POST') {
      const decision = JSON.parse(options.body!);
      moteur.push({ purpose: decision.purpose, provider: decision.provider,
        timestamp: decision.occurred_at, textVersion: decision.text_version });
    }
    return Promise.resolve({ grants: moteur, history: [] });
  });

  const synchro = synchroniserConsentements();
  await vi.waitFor(() => expect(terminer).toBeDefined());
  grantCloudConsent('images', 'gpt-image-2');
  await flushConsentDecisions();
  terminer();
  await synchro;

  expect(appels().filter(a => a === 'POST /api/consents/import')).toHaveLength(1);
  expect(appels().at(-1)).toBe('GET /api/consents');
  expect(hasCloudConsent('llm', 'openai')).toBe(true);
  expect(hasCloudConsent('images', 'gpt-image-2')).toBe(true);

  // Démarrage suivant : plus rien d'ancien à reprendre, donc plus d'import.
  request.mockClear();
  await synchroniserConsentements();
  expect(appels()).toEqual(['GET /api/consents']);
});

it('un import refusé garde les accords anciens et sera retenté au démarrage suivant', async () => {
  poserLeCache({ 'llm:openai': ANCIEN });
  request.mockRejectedValueOnce(new Error('Écriture refusée'));

  await expect(synchroniserConsentements()).rejects.toThrow('Écriture refusée');
  // Rien de perdu : le cache local n'a pas été remplacé.
  expect(listCloudConsents()).toEqual([ANCIEN]);

  request.mockResolvedValue({ grants: [REPRIS], history: [] });
  await synchroniserConsentements();

  const imports = request.mock.calls.filter(([chemin]) => chemin === '/api/consents/import')
    .map(([, options]) => JSON.parse(options.body).grants);
  expect(imports).toEqual([[ANCIEN], [ANCIEN]]);
  expect(listCloudConsents()).toEqual([REPRIS]);
});

it('une relecture refusée ne touche pas au cache local', async () => {
  poserLeCache({ 'llm:openai': REPRIS });
  request.mockRejectedValue(new Error('Moteur indisponible'));

  await expect(synchroniserConsentements()).rejects.toThrow('Moteur indisponible');

  expect(appels()).toEqual(['GET /api/consents']);
  expect(listCloudConsents()).toEqual([REPRIS]);
});

it('un retrait arrivé pendant la relecture n’est pas réactivé par sa réponse périmée', async () => {
  poserLeCache({ 'llm:openai': REPRIS });
  let accordMoteur = true;
  let terminer!: () => void;
  let premiere = true;
  request.mockImplementation((_chemin: string, options?: { method?: string; body?: string }) => {
    if (options?.method === 'POST') {
      accordMoteur = JSON.parse(options.body!).granted;
      return Promise.resolve({ grants: [] });
    }
    const reponse = { grants: accordMoteur ? [REPRIS] : [], history: [] };
    if (!premiere) return Promise.resolve(reponse);
    premiere = false;
    return new Promise(resolve => { terminer = () => resolve(reponse); });
  });

  const synchro = synchroniserConsentements();
  await vi.waitFor(() => expect(terminer).toBeDefined());
  revokeCloudConsent('llm', 'openai');
  await flushConsentDecisions();
  terminer();
  await synchro;

  expect(hasCloudConsent('llm', 'openai')).toBe(false);
  expect(appels().filter(a => a.endsWith('/import'))).toEqual([]);
});

it('un retrait resté hors ligne arrête la synchro sans réactiver l’accord', async () => {
  poserLeCache({ 'llm:openai': REPRIS });
  request.mockRejectedValue(new Error('Hors ligne'));
  revokeCloudConsent('llm', 'openai');
  await expect(flushConsentDecisions()).rejects.toThrow('Hors ligne');
  request.mockClear();

  await expect(synchroniserConsentements()).rejects.toThrow('Hors ligne');

  expect(appels()).toEqual(['POST /api/consents']);
  expect(hasCloudConsent('llm', 'openai')).toBe(false);
});
