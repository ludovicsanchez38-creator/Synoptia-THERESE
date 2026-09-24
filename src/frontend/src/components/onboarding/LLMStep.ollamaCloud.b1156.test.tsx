/**
 * B-1156 (cycle 13, lecteur D) : l’onboarding listait un modèle Ollama
 * Cloud sous « Ollama (Local) - 100% local » et le présélectionnait.
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

describe('B-1156 onboarding Ollama Cloud', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.spyOn(console, 'error').mockImplementation(() => undefined);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('ne présélectionne pas un modèle Ollama Cloud sous « 100% local » et le signale', async () => {
    const gib = 1024 ** 3;
    apiMocks.getApiKeysWithCorrupted.mockResolvedValue({ keys: {}, corrupted: [], sources: {} });
    apiMocks.getOllamaStatus.mockResolvedValue({
      available: true,
      base_url: 'http://ollama.test',
      models: [
        { name: 'kimi-k2.6:cloud', size: 1000, modified_at: null, digest: null },
        { name: 'qwen3:8b', size: 5 * gib, modified_at: null, digest: null },
      ],
      error: null,
    });
    apiMocks.getSystemResources.mockResolvedValue({
      total_ram_bytes: 16 * gib,
      safe_local_model_ram_bytes: 8 * gib,
      ollama_context_margin_bytes: 2 * gib,
      detection_method: 'test',
    });
    apiMocks.setLLMConfig.mockResolvedValue({});

    render(<LLMStep onNext={vi.fn()} onBack={vi.fn()} />);
    await act(async () => Promise.resolve());
    await act(async () => Promise.resolve());
    const radio = screen.getByRole('radio', { name: /Ollama \(Local\)/ });
    expect(radio).toHaveTextContent('100% local');
    fireEvent.click(radio);

    const select = screen.getByLabelText('Modèle') as HTMLSelectElement;
    const optionCloud = Array.from(select.options).find((o) => o.value === 'kimi-k2.6:cloud');
    const etat = {
      preselection: select.value,
      libelleOptionCloud: optionCloud?.textContent?.trim(),
    };
    expect(etat).toEqual({
      preselection: 'qwen3:8b',
      libelleOptionCloud: expect.stringMatching(/cloud.*(en ligne|Ollama Cloud)|Ollama Cloud/i),
    });
  });
});
