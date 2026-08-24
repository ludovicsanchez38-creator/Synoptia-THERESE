/**
 * Dette 0.43.4 - l'adresse d'espace de travail Qwen depuis les Réglages.
 *
 * Le parcours, pas la classe : l'utilisateur voit le champ, colle l'adresse,
 * enregistre - et setLLMConfig part avec base_url. Sans ce chemin, le
 * fournisseur restait configurable uniquement en théorie.
 */
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { describe, expect, it, vi, beforeEach } from 'vitest';

const apiMocks = vi.hoisted(() => ({
  getLLMConfig: vi.fn(),
  setLLMConfig: vi.fn(),
}));

vi.mock('../../services/api', () => apiMocks);

import { LLMTab } from './LLMTab';

function rendreOngletQwen() {
  return render(
    <LLMTab
      selectedProvider="qwen"
      selectedModel="qwen3.8-max"
      apiKeys={{ qwen: true }}
      apiKeyInput=""
      setApiKeyInput={vi.fn()}
      showApiKey={false}
      setShowApiKey={vi.fn()}
      ollamaStatus={null}
      ollamaModels={[]}
      systemResources={null}
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

describe('LLMTab - adresse d’espace de travail Qwen', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    apiMocks.getLLMConfig.mockResolvedValue({
      provider: 'qwen', model: 'qwen3.8-max', available_models: [],
      base_url: 'https://deja-la.aliyuncs.com/compatible-mode/v1',
    });
    apiMocks.setLLMConfig.mockResolvedValue({});
  });

  it('préremplit l’adresse déjà enregistrée', async () => {
    rendreOngletQwen();

    await waitFor(() => {
      expect(screen.getByLabelText('Adresse de ton espace de travail'))
        .toHaveValue('https://deja-la.aliyuncs.com/compatible-mode/v1');
    });
  });

  it('enregistre l’adresse saisie via setLLMConfig', async () => {
    rendreOngletQwen();
    const champ = await screen.findByLabelText('Adresse de ton espace de travail');

    fireEvent.change(champ, {
      target: { value: 'https://ws-9.ap-southeast-1.maas.aliyuncs.com/compatible-mode/v1' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Enregistrer' }));

    await waitFor(() => {
      expect(apiMocks.setLLMConfig).toHaveBeenCalledWith(
        'qwen', 'qwen3.8-max', undefined,
        'https://ws-9.ap-southeast-1.maas.aliyuncs.com/compatible-mode/v1',
      );
    });
  });
});
