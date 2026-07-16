import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import type { OllamaStatus, SystemResources } from '../../services/api';
import { LLMTab } from './LLMTab';

const GIB = 1024 ** 3;
const ollamaStatus: OllamaStatus = {
  available: true,
  base_url: 'http://ollama.test',
  models: [
    { name: 'qwen:8b', size: 5 * GIB, modified_at: null, digest: null },
    { name: 'qwen:14b', size: 7 * GIB, modified_at: null, digest: null },
  ],
  error: null,
};
const systemResources: SystemResources = {
  total_ram_bytes: 16 * GIB,
  safe_local_model_ram_bytes: 8 * GIB,
  ollama_context_margin_bytes: 2 * GIB,
  detection_method: 'test',
};

describe('LLMTab - garde-fou RAM Ollama', () => {
  it('actualise la pastille lors du choix tout en laissant sélectionner le modèle rouge', () => {
    const onSelectModel = vi.fn();
    const { rerender } = render(
      <LLMTab
        selectedProvider="ollama"
        selectedModel="qwen:8b"
        apiKeys={{}}
        apiKeyInput=""
        setApiKeyInput={vi.fn()}
        showApiKey={false}
        setShowApiKey={vi.fn()}
        ollamaStatus={ollamaStatus}
        ollamaModels={ollamaStatus.models.map((model) => model.name)}
        systemResources={systemResources}
        saving={false}
        saved={false}
        error={null}
        setError={vi.fn()}
        onSelectProvider={vi.fn()}
        onSelectModel={onSelectModel}
        onSaveApiKey={vi.fn()}
      />,
    );
    expect(screen.getByTestId('local-model-feasibility')).toHaveAttribute('data-status', 'feasible');

    fireEvent.change(screen.getByLabelText('Modèle'), { target: { value: 'qwen:14b' } });
    expect(onSelectModel).toHaveBeenCalledWith('qwen:14b');

    rerender(
      <LLMTab
        selectedProvider="ollama"
        selectedModel="qwen:14b"
        apiKeys={{}}
        apiKeyInput=""
        setApiKeyInput={vi.fn()}
        showApiKey={false}
        setShowApiKey={vi.fn()}
        ollamaStatus={ollamaStatus}
        ollamaModels={ollamaStatus.models.map((model) => model.name)}
        systemResources={systemResources}
        saving={false}
        saved={false}
        error={null}
        setError={vi.fn()}
        onSelectProvider={vi.fn()}
        onSelectModel={onSelectModel}
        onSaveApiKey={vi.fn()}
      />,
    );
    expect(screen.getByTestId('local-model-feasibility')).toHaveAttribute('data-status', 'too-large');
  });
});
