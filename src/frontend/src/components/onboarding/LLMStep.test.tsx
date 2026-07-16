import { act, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { LLMStep } from './LLMStep';

const apiMocks = vi.hoisted(() => ({
  getApiKeys: vi.fn(),
  getOllamaStatus: vi.fn(),
  getSystemResources: vi.fn(),
  setApiKey: vi.fn(),
  setLLMConfig: vi.fn(),
}));

vi.mock('../../services/api', () => apiMocks);

describe('LLMStep', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.clearAllMocks();
    vi.spyOn(console, 'error').mockImplementation(() => undefined);
    apiMocks.getApiKeys.mockReturnValue(new Promise(() => {}));
    apiMocks.getOllamaStatus.mockReturnValue(new Promise(() => {}));
    apiMocks.getSystemResources.mockReturnValue(new Promise(() => {}));
  });

  afterEach(() => {
    vi.restoreAllMocks();
    vi.useRealTimers();
  });

  it('sort du chargement après timeout et laisse configurer le modèle plus tard', async () => {
    const onNext = vi.fn();
    render(<LLMStep onNext={onNext} onBack={vi.fn()} />);

    expect(screen.getByText('Vérification des modèles disponibles…')).toBeInTheDocument();
    await act(async () => vi.advanceTimersByTimeAsync(10_000));

    expect(screen.getByRole('alert')).toHaveTextContent('prend trop de temps');
    fireEvent.click(screen.getByRole('button', { name: 'Configurer plus tard' }));
    expect(onNext).toHaveBeenCalledTimes(1);
  });

  it('affiche la faisabilité RAM du modèle Ollama sélectionné sans bloquer la suite', async () => {
    const gib = 1024 ** 3;
    apiMocks.getApiKeys.mockResolvedValue({});
    apiMocks.getOllamaStatus.mockResolvedValue({
      available: true,
      base_url: 'http://ollama.test',
      models: [{ name: 'qwen:14b', size: 7 * gib, modified_at: null, digest: null }],
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
    fireEvent.click(screen.getByRole('radio', { name: /Ollama \(Local\)/ }));

    expect(screen.getByTestId('local-model-feasibility')).toHaveAttribute('data-status', 'too-large');
    expect(screen.getByRole('button', { name: 'Continuer' })).toBeEnabled();
  });
});
