import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { SettingsModal } from './SettingsModal';
import { usePersonalisationStore } from '../../stores/personalisationStore';

// Mock PARTIEL (leçon 22/07) : seuls les appels réseau sont neutralisés.
vi.mock('../../services/api', async (importOriginal) => ({
  ...(await importOriginal<typeof import('../../services/api')>()),
  getApiKeysWithCorrupted: vi
    .fn()
    .mockResolvedValue({ keys: { mistral: true, openai: true }, corrupted: [] }),
  getLLMConfig: vi.fn().mockResolvedValue({
    provider: 'mistral',
    model: 'mistral-medium-latest',
    available_models: [],
    available: true,
  }),
  setLLMConfig: vi.fn().mockResolvedValue({}),
  getPreferences: vi.fn().mockResolvedValue({}),
  getStats: vi.fn().mockResolvedValue(null),
  getProfile: vi.fn().mockResolvedValue(null),
  getWorkingDirectory: vi.fn().mockResolvedValue({ path: null, exists: false }),
  getOllamaStatus: vi.fn().mockResolvedValue(null),
  getSystemResources: vi.fn().mockResolvedValue(null),
  hasGroqKey: vi.fn().mockResolvedValue(false),
  getWebSearchStatus: vi.fn().mockResolvedValue({
    enabled: true,
    providers: { gemini: 'indisponible', others: 'indisponible' },
    description: '',
  }),
}));

async function ouvrirOngletIA() {
  render(<SettingsModal isOpen onClose={vi.fn()} />);
  fireEvent.click(screen.getByTestId('settings-tab-ai'));
  // Lot 9 : la grille renonce au motif radio (`setLLMConfig` est un POST, la
  // flèche ne doit pas l'appeler). Les cartes sont des boutons à état.
  await waitFor(() =>
    expect(screen.getByRole('button', { name: /Mistral AI/, pressed: true })).toBeInTheDocument(),
  );
}

describe('B-1805 : dernier choix de modèle', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    usePersonalisationStore.setState({ uxMode: 'contributeur' });
  });

  it('B-1805 : une ancienne lecture lente ne remplace pas le dernier modèle choisi', async () => {
    const api = await import('../../services/api');
    await ouvrirOngletIA();
    const config = await api.getLLMConfig();
    let terminerPremiere!: (value: typeof config) => void;
    let terminerSeconde!: (value: typeof config) => void;
    vi.mocked(api.getLLMConfig)
      .mockImplementationOnce(() => new Promise(resolve => { terminerPremiere = resolve; }))
      .mockImplementationOnce(() => new Promise(resolve => { terminerSeconde = resolve; }));

    fireEvent.change(screen.getByLabelText('Modèle'), { target: { value: 'mistral-small-2603' } });
    fireEvent.change(screen.getByLabelText('Modèle'), { target: { value: 'mistral-large-latest' } });
    await act(async () => { terminerSeconde(config); });
    await act(async () => { terminerPremiere(config); });

    expect(vi.mocked(api.setLLMConfig)).toHaveBeenLastCalledWith('mistral', 'mistral-large-latest', 'auto');
    expect(screen.getByLabelText('Modèle')).toHaveValue('mistral-large-latest');
  });

  it('B-1805 : une sauvegarde lente ne réécrit pas le dernier choix', async () => {
    const api = await import('../../services/api');
    await ouvrirOngletIA();
    let terminerPremiere!: () => void;
    let modeleEnregistre = 'mistral-medium-latest';
    let actifs = 0;
    let maximumActifs = 0;
    vi.mocked(api.setLLMConfig)
      .mockImplementationOnce(async (_provider, model) => {
        maximumActifs = Math.max(maximumActifs, ++actifs);
        await new Promise<void>(resolve => { terminerPremiere = resolve; });
        modeleEnregistre = model;
        actifs--;
        return {} as Awaited<ReturnType<typeof api.setLLMConfig>>;
      })
      .mockImplementationOnce(async (_provider, model) => {
        maximumActifs = Math.max(maximumActifs, ++actifs);
        modeleEnregistre = model;
        actifs--;
        return {} as Awaited<ReturnType<typeof api.setLLMConfig>>;
      });

    fireEvent.change(screen.getByLabelText('Modèle'), { target: { value: 'mistral-small-2603' } });
    await waitFor(() => expect(terminerPremiere).toBeTypeOf('function'));
    fireEvent.change(screen.getByLabelText('Modèle'), { target: { value: 'mistral-large-latest' } });
    await act(async () => {});
    await act(async () => { terminerPremiere(); });

    await waitFor(() => expect(modeleEnregistre).toBe('mistral-large-latest'));
    expect(maximumActifs).toBe(1);
    expect(screen.getByLabelText('Modèle')).toHaveValue('mistral-large-latest');
  });

  it('B-1805 : changer de fournisseur rend inopérant un ancien choix de modèle', async () => {
    const api = await import('../../services/api');
    await ouvrirOngletIA();
    const config = await api.getLLMConfig();
    let terminerLecture!: (value: typeof config) => void;
    vi.mocked(api.getLLMConfig).mockImplementationOnce(
      () => new Promise(resolve => { terminerLecture = resolve; }),
    );

    fireEvent.change(screen.getByLabelText('Modèle'), { target: { value: 'mistral-small-2603' } });
    fireEvent.click(screen.getByRole('button', { name: /GPT \(OpenAI\)/ }));
    await waitFor(() => expect(api.setLLMConfig).toHaveBeenCalled());
    await act(async () => { terminerLecture(config); });

    const appels = vi.mocked(api.setLLMConfig).mock.calls;
    expect(appels[appels.length - 1][0]).toBe('openai');
    expect(screen.getByRole('button', { name: /GPT \(OpenAI\)/, pressed: true })).toBeInTheDocument();
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
  });

  it.each(['lecture', 'sauvegarde'])('B-1805 : après une %s refusée, affiche le dernier modèle réellement enregistré', async (etape) => {
    const api = await import('../../services/api');
    await ouvrirOngletIA();
    let terminerPremiere!: () => void;
    vi.mocked(api.setLLMConfig).mockImplementationOnce(async () => {
      await new Promise<void>(resolve => { terminerPremiere = resolve; });
      return {} as Awaited<ReturnType<typeof api.setLLMConfig>>;
    });
    fireEvent.change(screen.getByLabelText('Modèle'), { target: { value: 'mistral-small-2603' } });
    await waitFor(() => expect(terminerPremiere).toBeTypeOf('function'));
    if (etape === 'lecture') vi.mocked(api.getLLMConfig).mockRejectedValueOnce(new Error('Choix refusé'));
    else vi.mocked(api.setLLMConfig).mockRejectedValueOnce(new Error('Choix refusé'));
    fireEvent.change(screen.getByLabelText('Modèle'), { target: { value: 'mistral-large-latest' } });
    await act(async () => {});
    await act(async () => { terminerPremiere(); });

    await waitFor(() => expect(screen.getByRole('alert')).toHaveTextContent('Choix refusé'));
    expect(screen.getByLabelText('Modèle')).toHaveValue('mistral-small-2603');
    // Le refus ne doit pas bloquer les sauvegardes suivantes.
    fireEvent.change(screen.getByLabelText('Modèle'), { target: { value: 'mistral-large-latest' } });
    await waitFor(() => expect(screen.getByLabelText('Modèle')).toHaveValue('mistral-large-latest'));
  });

  it('B-1805 : un fournisseur refusé ne restaure pas un choix intermédiaire jamais enregistré', async () => {
    const api = await import('../../services/api');
    await ouvrirOngletIA();
    let terminerPremiere!: () => void;
    vi.mocked(api.setLLMConfig)
      .mockImplementationOnce(async () => {
        await new Promise<void>(resolve => { terminerPremiere = resolve; });
        return {} as Awaited<ReturnType<typeof api.setLLMConfig>>;
      })
      .mockRejectedValueOnce(new Error('Fournisseur refusé'));
    fireEvent.change(screen.getByLabelText('Modèle'), { target: { value: 'mistral-small-2603' } });
    await waitFor(() => expect(terminerPremiere).toBeTypeOf('function'));
    fireEvent.click(screen.getByRole('button', { name: /GPT \(OpenAI\)/ }));
    fireEvent.click(screen.getByRole('button', { name: /Claude \(Anthropic\)/ }));
    await act(async () => { terminerPremiere(); });

    await waitFor(() => expect(screen.getByRole('alert')).toHaveTextContent('Fournisseur refusé'));
    expect(screen.getByRole('button', { name: /Mistral AI/, pressed: true })).toBeInTheDocument();
    expect(screen.getByLabelText('Modèle')).toHaveValue('mistral-small-2603');
  });
});
