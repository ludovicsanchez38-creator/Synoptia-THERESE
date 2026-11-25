import { beforeEach, expect, it, vi } from 'vitest';
import { setLLMConfig, type LLMProvider } from './config';
import { request } from './core';

vi.mock('./core', async (importOriginal) => ({
  ...(await importOriginal<typeof import('./core')>()),
  request: vi.fn(),
}));

beforeEach(() => vi.clearAllMocks());

it('l’API de configuration accepte le fournisseur Synthetic et son alias', async () => {
  const fournisseur: LLMProvider = 'synthetic';
  await setLLMConfig(fournisseur, 'syn:large:text');

  expect(request).toHaveBeenCalledWith('/api/config/llm', {
    method: 'POST',
    body: JSON.stringify({ provider: 'synthetic', model: 'syn:large:text' }),
  });
});

it('l’absence d’effort omet la propriété, un effort explicite est transmis', async () => {
  await setLLMConfig('openai', 'gpt-6-sol', 'high');
  await setLLMConfig('openai', 'gpt-6.2-sol');

  const appels = vi.mocked(request).mock.calls;
  expect(appels[0][1]?.body).toBe(JSON.stringify({ provider: 'openai', model: 'gpt-6-sol', effort: 'high' }));
  expect(appels[1][1]?.body).toBe(JSON.stringify({ provider: 'openai', model: 'gpt-6.2-sol' }));
});
