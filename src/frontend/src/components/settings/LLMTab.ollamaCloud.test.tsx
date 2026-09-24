/**
 * B-1146 (audit de release 0.75, agent sécurité) : un modèle Ollama Cloud
 * (« gpt-oss:120b-cloud », « kimi-k2.6:cloud ») apparaît dans la liste des
 * modèles installés, mais Ollama transmet ses requêtes à ollama.com. Sous la
 * promesse « En local, rien ne quitte ton ordinateur », il doit se dire en ligne.
 */
import { render, screen, within } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import type { OllamaStatus } from '../../services/api';
import { LLMTab } from './LLMTab';

const GIB = 1024 ** 3;
const noms = ['qwen:8b', 'gpt-oss:120b-cloud', 'kimi-k2.6:cloud'];
const ollamaStatus: OllamaStatus = {
  available: true,
  base_url: 'http://ollama.test',
  models: noms.map((name) => ({ name, size: 5 * GIB, modified_at: null, digest: null })),
  error: null,
};

describe('B-1146 : les modèles Ollama Cloud se disent en ligne', () => {
  it('seuls les modèles :cloud et -cloud portent la mention en ligne', () => {
    render(
      <LLMTab
        selectedProvider="ollama"
        selectedModel="qwen:8b"
        apiKeys={{}}
        apiKeyInput=""
        setApiKeyInput={vi.fn()}
        showApiKey={false}
        setShowApiKey={vi.fn()}
        ollamaStatus={ollamaStatus}
        ollamaModels={noms}
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
    const liste = screen.getByLabelText('Modèle');
    const libelle = (valeur: string) =>
      within(liste).getAllByRole('option').find((o) => (o as HTMLOptionElement).value === valeur)?.textContent ?? '';
    expect(libelle('qwen:8b')).not.toMatch(/en ligne/);
    expect(libelle('gpt-oss:120b-cloud')).toMatch(/en ligne/);
    expect(libelle('kimi-k2.6:cloud')).toMatch(/en ligne/);
  });
});
