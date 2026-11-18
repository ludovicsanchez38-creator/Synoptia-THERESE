import { act, fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { LLMTab } from './LLMTab';
import type { OllamaStatus } from '../../services/api';

vi.mock('../../services/api', async (importOriginal) => ({
  ...(await importOriginal<typeof import('../../services/api')>()),
  getLLMConfig: vi.fn().mockResolvedValue({ provider: 'openai', model: 'gpt-5.6-luna', effort: 'auto' }),
  setLLMConfig: vi.fn().mockResolvedValue(undefined),
}));

function statutOllama(partiel: Partial<OllamaStatus> = {}): OllamaStatus {
  return {
    available: true,
    base_url: 'http://127.0.0.1:11434',
    models: [],
    error: null,
    ...partiel,
  } as OllamaStatus;
}

type Props = Partial<React.ComponentProps<typeof LLMTab>>;

function rendre(props: Props = {}) {
  return render(
    <LLMTab
      selectedProvider="anthropic"
      selectedModel="claude-sonnet-4-6"
      apiKeys={{}}
      corruptedKeys={[]}
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
      {...props}
    />,
  );
}

describe('Textes des réglages IA, cycle 20', () => {
  it('B-1960 : le bouton français ouvre la saisie du modèle personnalisé', async () => {
    const choisir = vi.fn();
    rendre({ onSelectModel: choisir });
    await act(async () => {});
    fireEvent.click(screen.getByRole('button', { name: 'Modèle personnalisé' }));
    const champ = screen.getByRole('textbox', { name: 'Identifiant du modèle personnalisé' });
    fireEvent.change(champ, { target: { value: 'modele-hors-catalogue' } });
    fireEvent.keyDown(champ, { key: 'Enter' });
    expect(choisir).toHaveBeenCalledWith('modele-hors-catalogue');
  });
  it('B-1959 : le statut indisponible tutoie et garde le motif', async () => {
    rendre({ selectedProvider: 'ollama', selectedModel: '', ollamaStatus: statutOllama({ available: false, error: 'Connexion refusée' }) });
    await act(async () => {});
    expect(screen.getByRole('status')).toHaveTextContent('Connexion refusée. Démarre Ollama pour utiliser des modèles locaux.');
  });
});
