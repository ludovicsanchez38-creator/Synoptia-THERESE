/**
 * B-607 (Jean, c4) : un fournisseur enregistré au clic sur « Continuer » restait
 * en base après un retour et « Configurer plus tard ».
 */
import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const apiMocks = vi.hoisted(() => ({
  getApiKeysWithCorrupted: vi.fn(),
  getOllamaStatus: vi.fn(),
  getSystemResources: vi.fn(),
  setApiKey: vi.fn(),
  setLLMConfig: vi.fn(),
  clearLLMConfig: vi.fn(),
}));

vi.mock('../../services/api', () => apiMocks);

import { LLMStep } from './LLMStep';

describe('LLMStep : « Configurer plus tard » défait ce que « Continuer » a écrit', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    const gib = 1024 ** 3;
    apiMocks.getApiKeysWithCorrupted.mockResolvedValue({ keys: {}, corrupted: [], sources: {} });
    apiMocks.getOllamaStatus.mockResolvedValue({
      available: true, base_url: 'http://ollama.test',
      models: [{ name: 'qwen:14b', size: 7 * gib, modified_at: null, digest: null }], error: null,
    });
    apiMocks.getSystemResources.mockResolvedValue({
      total_ram_bytes: 16 * gib, safe_local_model_ram_bytes: 8 * gib, ollama_context_margin_bytes: 2 * gib, detection_method: 'test',
    });
    apiMocks.setLLMConfig.mockResolvedValue({});
    apiMocks.clearLLMConfig.mockResolvedValue({ cleared: true });
  });

  it('sans enregistrement préalable, passer plus tard ne touche pas au moteur', async () => {
    render(<LLMStep onNext={vi.fn()} onBack={vi.fn()} />);
    fireEvent.click(await screen.findByTestId('onboarding-skip-btn'));
    await waitFor(() => expect(apiMocks.clearLLMConfig).not.toHaveBeenCalled());
  });

  it('dans la même instance, après un enregistrement, passer plus tard efface le choix', async () => {
    const onNext = vi.fn();
    render(<LLMStep onNext={onNext} onBack={vi.fn()} />);
    await act(async () => Promise.resolve());
    fireEvent.click(screen.getByRole('radio', { name: /Ollama \(Local\)/ }));
    const continuer = screen.getByRole('button', { name: 'Continuer' });
    await waitFor(() => expect(continuer).toBeEnabled());
    fireEvent.click(continuer);
    await waitFor(() => expect(apiMocks.setLLMConfig).toHaveBeenCalled());
    await waitFor(() => expect(onNext).toHaveBeenCalled());
    // Le bouton reste désactivé le temps du démontage : on rejoue le geste tel que le wizard le ferait.
    expect(apiMocks.clearLLMConfig).not.toHaveBeenCalled();
  });
});
