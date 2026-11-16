/**
 * B-1936 : dès qu’Ollama répond, le fournisseur porte « Tes données restent
 * sur ta machine », y compris quand le modèle choisi est un Ollama Cloud.
 */
import { act, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { LLMStep } from './LLMStep';

const apiMocks = vi.hoisted(() => ({
  getApiKeysWithCorrupted: vi.fn(),
  getOllamaStatus: vi.fn(),
  getSystemResources: vi.fn(),
  setApiKey: vi.fn(),
  setLLMConfig: vi.fn(),
}));

vi.mock('../../services/api', () => apiMocks);

const catalogueMocks = vi.hoisted(() => ({ chargerCatalogue: vi.fn() }));
vi.mock('../../lib/catalogueModeles', async (importOriginal) => {
  const reel = await importOriginal<typeof import('../../lib/catalogueModeles')>();
  return {
    ...reel,
    chargerCatalogue: (...args: Parameters<typeof reel.chargerCatalogue>) =>
      catalogueMocks.chargerCatalogue(...args) ?? Promise.resolve(null),
  };
});

const gib = 1024 ** 3;

describe('promesse locale et modèle Ollama Cloud (B-1936)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.spyOn(console, 'error').mockImplementation(() => undefined);
    apiMocks.getApiKeysWithCorrupted.mockResolvedValue({ keys: {}, corrupted: [], sources: {} });
    apiMocks.getOllamaStatus.mockResolvedValue({
      available: true,
      base_url: 'http://ollama.test',
      error: null,
      models: [
        { name: 'qwen3:8b', size: 4.9 * gib, modified_at: null, digest: null, gere_les_outils: true },
        { name: 'kimi-k2.6:cloud', size: 1000, modified_at: null, digest: null, gere_les_outils: true },
      ],
    });
    apiMocks.getSystemResources.mockResolvedValue({
      total_ram_bytes: 16 * gib,
      safe_local_model_ram_bytes: 8 * gib,
      ollama_context_margin_bytes: 2 * gib,
      detection_method: 'test',
    });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('retire la promesse locale quand le modèle choisi part en ligne', async () => {
    render(<LLMStep onNext={vi.fn()} onBack={vi.fn()} />);
    await act(async () => Promise.resolve());
    await act(async () => Promise.resolve());

    const ollama = screen.getByRole('radio', { name: /Ollama \(Local\)/ });
    const select = screen.getByLabelText('Modèle') as HTMLSelectElement;
    expect(select.value).toBe('qwen3:8b');
    expect(ollama).toHaveTextContent('Tes données restent sur ta machine');

    fireEvent.change(select, { target: { value: 'kimi-k2.6:cloud' } });

    const optionCloud = Array.from(select.options).find((o) => o.value === 'kimi-k2.6:cloud');
    expect(optionCloud?.textContent).toMatch(/Ollama Cloud, en ligne/);
    expect(ollama).not.toHaveTextContent('Tes données restent sur ta machine');

    fireEvent.change(select, { target: { value: 'qwen3:8b' } });
    expect(ollama).toHaveTextContent('Tes données restent sur ta machine');
  });
});
