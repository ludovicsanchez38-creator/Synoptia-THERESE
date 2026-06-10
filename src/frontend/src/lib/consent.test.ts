import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { recordCloudConsent, getCloudConsent } from './consent';

// Le setup global mocke localStorage avec des vi.fn() non persistants ; on
// installe ici un localStorage à mémoire réelle pour tester record + relecture.
describe('consentement transfert cloud (US-003 RGPD-4)', () => {
  beforeEach(() => {
    const store: Record<string, string> = {};
    vi.stubGlobal('localStorage', {
      getItem: (k: string) => store[k] ?? null,
      setItem: (k: string, v: string) => {
        store[k] = v;
      },
      removeItem: (k: string) => {
        delete store[k];
      },
      clear: () => {
        for (const k of Object.keys(store)) delete store[k];
      },
    });
  });

  afterEach(() => vi.unstubAllGlobals());

  it('persiste le consentement horodaté et versionné', () => {
    recordCloudConsent('2026-06-10T10:00:00.000Z');
    const c = getCloudConsent();
    expect(c?.accepted).toBe(true);
    expect(c?.timestamp).toBe('2026-06-10T10:00:00.000Z');
    expect(c?.version).toBeTruthy();
  });

  it('retourne null tant qu’aucun consentement n’est donné', () => {
    expect(getCloudConsent()).toBeNull();
  });
});
