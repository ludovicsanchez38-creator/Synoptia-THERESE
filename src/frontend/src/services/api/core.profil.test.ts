import { expect, it, vi } from 'vitest';
import { getStats } from './core';

it('R1-C1 : transmet les chemins à vérifier sans les normaliser dans une URL', async () => {
  const chemins = ['/profils/intermediaire/../A', '/profils/Équipe & clients/A/'];
  vi.mocked(globalThis.fetch).mockResolvedValueOnce(new Response(JSON.stringify({
    data_dir: '/profils/A', data_profile_aliases: [chemins[0]],
  })));

  const stats = await getStats(chemins);

  const url = new URL(String(vi.mocked(globalThis.fetch).mock.calls.at(-1)![0]));
  expect(url.pathname).toBe('/api/config/stats');
  expect(url.searchParams.getAll('data_profiles')).toEqual(chemins);
  expect(stats.data_dir).toBe('/profils/A');
});
