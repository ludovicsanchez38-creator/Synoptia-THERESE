/**
 * Revue Grok du diff 0.70.0 (P1) : « Configurer plus tard » restait cliquable
 * pendant que le wizard attendait l'effacement au serveur (#162 a rendu
 * completeLlmStep asynchrone) ; deux clics = deux goNext, l'étape Sécurité
 * (consentement cloud) n'était jamais montée.
 */
import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const apiMocks = vi.hoisted(() => ({
  getApiKeysWithCorrupted: vi.fn(), getOllamaStatus: vi.fn(), getSystemResources: vi.fn(),
  setApiKey: vi.fn(), setLLMConfig: vi.fn(), clearLLMConfig: vi.fn(),
}));
vi.mock('../../services/api', () => apiMocks);

import { LLMStep } from './LLMStep';

describe('Grok 0.70.0 P1 : un seul « plus tard » pendant l’attente du wizard', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    const gib = 1024 ** 3;
    apiMocks.getApiKeysWithCorrupted.mockResolvedValue({ keys: {}, corrupted: [], sources: {} });
    apiMocks.getOllamaStatus.mockResolvedValue({ available: false, base_url: '', models: [], error: null });
    apiMocks.getSystemResources.mockResolvedValue({ total_ram_bytes: 16 * gib, safe_local_model_ram_bytes: 8 * gib, ollama_context_margin_bytes: 2 * gib, detection_method: 'test' });
  });

  it('deux clics rapides pendant que onNext attend : un seul onNext, bouton désactivé', async () => {
    let liberer: (() => void) | undefined;
    const onNext = vi.fn(() => new Promise<void>((resolve) => { liberer = resolve; }));
    render(<LLMStep onNext={onNext} onBack={vi.fn()} />);
    const bouton = await screen.findByTestId('onboarding-skip-btn');
    await act(async () => { fireEvent.click(bouton); });
    expect(bouton).toBeDisabled();
    fireEvent.click(bouton);
    fireEvent.click(bouton);
    expect(onNext).toHaveBeenCalledTimes(1);
    await act(async () => { liberer?.(); });
    await waitFor(() => expect(onNext).toHaveBeenCalledTimes(1));
  });
});
