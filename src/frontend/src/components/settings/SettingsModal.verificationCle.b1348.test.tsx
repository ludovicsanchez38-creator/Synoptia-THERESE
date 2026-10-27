/**
 * B-1348 (boucle DQ) dans les Paramètres : une clé refusée par le fournisseur
 * se dit tout de suite sous le champ, au lieu d'attendre le premier message.
 */
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { SettingsModal } from './SettingsModal';
import { usePersonalisationStore } from '../../stores/personalisationStore';

vi.mock('../../services/api', async (importOriginal) => ({
  ...(await importOriginal<typeof import('../../services/api')>()),
  getApiKeysWithCorrupted: vi.fn().mockResolvedValue({ keys: {}, corrupted: [] }),
  getLLMConfig: vi.fn().mockResolvedValue({ provider: 'mistral', model: 'mistral-medium-latest', available_models: [], available: false }),
  setLLMConfig: vi.fn().mockResolvedValue({}),
  setApiKey: vi.fn().mockResolvedValue(undefined),
  verifierCle: vi.fn(),
  getPreferences: vi.fn().mockResolvedValue({}),
  getStats: vi.fn().mockResolvedValue(null),
  getProfile: vi.fn().mockResolvedValue(null),
  getWorkingDirectory: vi.fn().mockResolvedValue({ path: null, exists: false }),
  getOllamaStatus: vi.fn().mockResolvedValue(null),
  getSystemResources: vi.fn().mockResolvedValue(null),
  hasGroqKey: vi.fn().mockResolvedValue(false),
  getWebSearchStatus: vi.fn().mockResolvedValue({ enabled: true, providers: { gemini: 'indisponible', others: 'indisponible' }, description: '' }),
}));

async function enregistrerUneCle() {
  render(<SettingsModal isOpen onClose={vi.fn()} />);
  fireEvent.click(screen.getByTestId('settings-tab-ai'));
  const champ = await waitFor(() => {
    const el = document.getElementById('settings-api-key') as HTMLInputElement | null;
    if (!el) throw new Error('champ de clé absent');
    return el;
  });
  fireEvent.change(champ, { target: { value: 'cle-mistral-fausse' } });
  fireEvent.keyDown(champ, { key: 'Enter' });
}

describe('Paramètres : la clé enregistrée est vérifiée (B-1348)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    usePersonalisationStore.setState({ uxMode: 'contributeur' });
  });

  it('un refus du fournisseur s’affiche en erreur', async () => {
    const api = await import('../../services/api');
    vi.mocked(api.verifierCle).mockResolvedValue({ provider: 'mistral', etat: 'refusee', message: 'Mistral refuse cette clé. Vérifie que tu as copié toute la clé.' });
    await enregistrerUneCle();

    await waitFor(() => expect(vi.mocked(api.setApiKey)).toHaveBeenCalledWith('mistral', 'cle-mistral-fausse'));
    expect(await screen.findByText(/Mistral refuse cette clé/)).toBeInTheDocument();
  });

  it('une clé acceptée n’affiche aucune erreur', async () => {
    const api = await import('../../services/api');
    vi.mocked(api.verifierCle).mockResolvedValue({ provider: 'mistral', etat: 'acceptee', message: 'Clé acceptée par Mistral.' });
    await enregistrerUneCle();

    await waitFor(() => expect(vi.mocked(api.verifierCle)).toHaveBeenCalledWith('mistral'));
    expect(screen.queryByText(/refuse cette clé/)).toBeNull();
  });
});
