import { expect, it, vi } from 'vitest';

const banc = vi.hoisted(() => ({ demarrer: undefined as undefined | ((fixtures: unknown) => Promise<void>) }));
vi.mock('@playwright/test', () => {
  const scenario = Object.assign(vi.fn(), {
    describe: (_nom: string, suite: () => void) => suite(),
    beforeEach: (demarrer: typeof banc.demarrer) => { banc.demarrer = demarrer; },
  });
  return { test: scenario, expect: () => ({ toBeVisible: async () => {} }) };
});
vi.mock('../../../../tests/e2e/stories/helpers/backend', () => ({
  BACKEND_URL: 'http://127.0.0.1:31999', authentifierAmorcageNavigateur: async () => {},
}));
vi.mock('../../../../tests/e2e/stories/helpers/surfaces', () => ({ passerLaMiseEnRoute: async () => {} }));

await import('../../../../tests/e2e/stories/parcours-08-capacites-prototype.spec');

async function installerGarde() {
  let garde!: (route: unknown) => Promise<unknown>;
  const page = {
    route: async (_motif: string, gestionnaire: typeof garde) => { garde = gestionnaire; },
    goto: async () => {}, getByTestId: () => ({}),
  };
  expect(banc.demarrer).toBeDefined();
  await banc.demarrer!({ page, request: {} });

  return async function simuler(methode: string, chemin: string) {
    let resultat: unknown;
    await garde({
      request: () => ({ url: () => `http://127.0.0.1:31999${chemin}`, method: () => methode }),
      continue: () => { resultat = 'moteur'; },
      fulfill: (reponse: unknown) => { resultat = reponse; },
    });
    return resultat;
  };
}

it('refuse les mutations sur les routes bouchonnées', async () => {
  const simuler = await installerGarde();
  for (const chemin of ['/api/images/generate', '/api/tasks', '/api/config/profile']) {
    expect(await simuler('POST', chemin)).toMatchObject({ status: 405 });
  }
  expect(await simuler('GET', '/api/tasks')).toMatchObject({ status: 200 });
});

it('laisse le calcul pur rejoindre le moteur', async () => {
  const simuler = await installerGarde();
  expect(await simuler('POST', '/api/calc/roi')).toBe('moteur');
});
