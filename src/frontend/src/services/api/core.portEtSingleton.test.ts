/**
 * B-039 : remplace les gardes textuelles de tests/test_regression.py (BUG-002,
 * BUG-011, BUG-015, port fixe) qui lisaient le source de core.ts. Ici on
 * exerce initApiBase : le paramètre ?port= de l'URL l'emporte, le port par
 * défaut vaut 17293 hors surcharge, et l'initialisation est un singleton.
 */
import { afterEach, describe, expect, it, vi } from 'vitest';

async function chargerCore() {
  vi.resetModules();
  return import('./core');
}

describe('initApiBase : port et singleton', () => {
  afterEach(() => {
    window.history.replaceState({}, '', '/');
    vi.unstubAllEnvs();
  });

  it('lit le port dans ?port= avant toute autre source', async () => {
    window.history.replaceState({}, '', '/?port=17555');
    const core = await chargerCore();
    await core.initApiBase();
    expect(core.getApiBase()).toContain(':17555');
  });

  it('sans surcharge, retombe sur le port fixe 17293', async () => {
    vi.stubEnv('VITE_THERESE_BACKEND_PORT', '');
    const core = await chargerCore();
    await core.initApiBase();
    expect(core.getApiBase()).toMatch(/:17293$/);
  });

  it('deux appels partagent la même promesse d’initialisation', async () => {
    const core = await chargerCore();
    const premiere = core.initApiBase();
    const seconde = core.initApiBase();
    expect(seconde).toBe(premiere);
    await premiere;
  });
});
