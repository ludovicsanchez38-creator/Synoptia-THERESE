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

describe('LLMStep - dette 0.43.4, le parcours des nouveaux fournisseurs', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.clearAllMocks();
    vi.spyOn(console, 'error').mockImplementation(() => undefined);
    apiMocks.getApiKeys.mockResolvedValue({ qwen: true });
    apiMocks.getOllamaStatus.mockResolvedValue({
      available: false, base_url: '', models: [], error: null,
    });
    apiMocks.getSystemResources.mockResolvedValue(null);
    apiMocks.setLLMConfig.mockResolvedValue({});
  });

  afterEach(() => {
    vi.restoreAllMocks();
    vi.useRealTimers();
  });

  it('propose GLM, Kimi, Qwen et MiniMax - et plus jamais gpt-5.3-codex', async () => {
    render(<LLMStep onNext={vi.fn()} onBack={vi.fn()} />);
    await act(async () => { await vi.advanceTimersByTimeAsync(0); });

    for (const nom of ['GLM (Z.ai)', 'Kimi (Moonshot AI)', 'Qwen (Alibaba)', 'MiniMax']) {
      expect(screen.getByText(nom)).toBeInTheDocument();
    }

    // La copie locale du catalogue proposait encore gpt-5.3-codex, dont l'API
    // ne supporte pas chat/completions - retiré partout ailleurs le 24/08.
    fireEvent.click(screen.getByText('GPT (OpenAI)'));
    const options = Array.from(document.querySelectorAll('#llm-model option'));
    expect(options.length).toBeGreaterThan(0);
    expect(options.map((o) => o.getAttribute('value'))).not.toContain('gpt-5.3-codex');
  });

  it('exige l’adresse d’espace de travail Qwen puis la transmet', async () => {
    render(<LLMStep onNext={vi.fn()} onBack={vi.fn()} />);
    await act(async () => { await vi.advanceTimersByTimeAsync(0); });

    fireEvent.click(screen.getByText('Qwen (Alibaba)'));
    await act(async () => { await vi.advanceTimersByTimeAsync(0); });

    const champ = screen.getByLabelText('Adresse de ton espace de travail');
    const continuer = screen.getByRole('button', { name: 'Continuer' });

    // Sans adresse, continuer livrerait un fournisseur incapable de répondre.
    expect(continuer).toBeDisabled();

    fireEvent.change(champ, {
      target: { value: 'https://ws-42.ap-southeast-1.maas.aliyuncs.com/compatible-mode/v1' },
    });
    expect(continuer).toBeEnabled();

    fireEvent.click(continuer);
    await act(async () => { await vi.advanceTimersByTimeAsync(0); });

    expect(apiMocks.setLLMConfig).toHaveBeenCalledWith(
      'qwen',
      expect.any(String),
      undefined,
      'https://ws-42.ap-southeast-1.maas.aliyuncs.com/compatible-mode/v1',
    );
  });
});
