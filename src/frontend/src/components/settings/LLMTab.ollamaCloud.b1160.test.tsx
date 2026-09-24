/**
 * B-1160 (cycle 13, lecteur B) : Paramètres > IA et les modèles Ollama Cloud.
 * Un modèle Cloud recevait une carte « RAM compatible », était compté parmi
 * les « modèles installés », et changer l'effort sans modèle Ollama envoyait
 * setLLMConfig('ollama', '', effort).
 */
import { act, fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import type { OllamaStatus } from '../../services/api';

const apiMocks = vi.hoisted(() => ({
  getLLMConfig: vi.fn(),
  setLLMConfig: vi.fn(),
}));
vi.mock('../../services/api', async () => {
  const actual = await vi.importActual<typeof import('../../services/api')>('../../services/api');
  return { ...actual, ...apiMocks };
});

import { LLMTab } from './LLMTab';

const GIB = 1024 ** 3;

function rendre(selectedModel: string, noms: string[], ollamaStatus: OllamaStatus) {
  return render(
    <LLMTab
      selectedProvider="ollama"
      selectedModel={selectedModel}
      apiKeys={{}}
      apiKeyInput=""
      setApiKeyInput={vi.fn()}
      showApiKey={false}
      setShowApiKey={vi.fn()}
      ollamaStatus={ollamaStatus}
      ollamaModels={noms}
      systemResources={{
        total_ram_bytes: 16 * GIB,
        safe_local_model_ram_bytes: 8 * GIB,
        ollama_context_margin_bytes: 2 * GIB,
        detection_method: 'test',
      }}
      saving={false}
      saved={false}
      error={null}
      setError={vi.fn()}
      onSelectProvider={vi.fn()}
      onSelectModel={vi.fn()}
      onSaveApiKey={vi.fn()}
    />,
  );
}

describe('B-1160 Paramètres > IA', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    apiMocks.getLLMConfig.mockResolvedValue({ provider: 'ollama', model: '', effort: 'auto' });
    apiMocks.setLLMConfig.mockResolvedValue({});
  });

  const noms = ['qwen:8b', 'gpt-oss:120b-cloud', 'kimi-k2.6:cloud'];
  const statut: OllamaStatus = {
    available: true,
    base_url: 'http://ollama.test',
    models: noms.map((name) => ({ name, size: 2 * GIB, modified_at: null, digest: null })),
    error: null,
  };

  it('pas de carte de faisabilité RAM pour un modèle cloud sélectionné', async () => {
    rendre('gpt-oss:120b-cloud', noms, statut);
    await act(async () => Promise.resolve());
    const carte = screen.queryByTestId('local-model-feasibility');
    expect(carte ? `${carte.getAttribute('data-status')} : ${carte.textContent}` : null).toBeNull();
  });

  it('la carte Ollama ne compte pas un modèle cloud parmi les « installés » sans le dire', async () => {
    rendre('gpt-oss:120b-cloud', noms, statut);
    await act(async () => Promise.resolve());
    const ligne = screen.getByText(/modèles? installés?/);
    expect(ligne.textContent).toMatch(/en ligne|(^|\D)1 modèle installé/);
  });

  it('changer l’effort sans modèle Ollama n’envoie pas un modèle vide', async () => {
    rendre('', [], { available: true, base_url: 'http://ollama.test', models: [], error: null });
    await act(async () => Promise.resolve());
    const effort = screen.getByLabelText('Effort de raisonnement') as HTMLSelectElement;
    await act(async () => { fireEvent.change(effort, { target: { value: 'high' } }); });
    const appelsModeleVide = apiMocks.setLLMConfig.mock.calls.filter((c) => c[1] === '');
    expect(appelsModeleVide).toEqual([]);
  });
});
