/**
 * B-1473 (recette P-146, lot 5) : installer un connecteur annonçait un délai
 * dépassé à 30 s alors que le moteur attend jusqu'à 150 s un premier
 * démarrage (téléchargement par npx ou uvx : initialize 90 s, liste des
 * outils 60 s). Le client n'abandonne plus avant le moteur.
 */
import { beforeEach, describe, expect, it, vi } from 'vitest';

const { request } = vi.hoisted(() => ({ request: vi.fn() }));
vi.mock('./core', async (importOriginal) => ({
  ...(await importOriginal<typeof import('./core')>()),
  request,
}));

import { installMCPPreset, restartMCPServer, startMCPServer } from './mcp';

describe('B-1473 : démarrer un connecteur laisse au moteur le temps de répondre', () => {
  beforeEach(() => request.mockResolvedValue({}));

  it.each([
    ['installer', () => installMCPPreset('fetch')],
    ['démarrer', () => startMCPServer('s-1')],
    ['redémarrer', () => restartMCPServer('s-1')],
  ])('%s attend au moins 150 s', async (_nom, appel) => {
    await appel();
    const options = request.mock.calls.at(-1)?.[1] as { timeoutMs?: number | null };
    expect(options.timeoutMs).toBeGreaterThanOrEqual(150_000);
  });
});
