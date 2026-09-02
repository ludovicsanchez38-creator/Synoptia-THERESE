/**
 * B-225 - inspecter un fournisseur ne doit pas perdre le modèle choisi.
 *
 * Constat du 02/09/2026 (persona A3 Léa, reproduction RP15c) : chaque clic sur
 * un radio de fournisseur enregistrait immédiatement la configuration avec le
 * PREMIER modèle du catalogue. Partie de mistral/mistral-medium-latest, Léa
 * clique « GPT (OpenAI) » pour voir si la clé est là, revient sur « Mistral
 * AI », et se retrouve sur mistral-large-latest : son choix a disparu sans
 * qu'elle ait touché au sélecteur de modèle.
 *
 * L'aller-retour est le cœur du test : un clic isolé ne prouve rien, c'est le
 * RETOUR qui doit rendre le modèle enregistré.
 */
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
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
  await waitFor(() =>
    expect(screen.getByRole('radio', { name: /Mistral AI/ })).toHaveAttribute(
      'aria-checked',
      'true',
    ),
  );
}

describe('B-225 - inspecter un fournisseur ne perd pas le modèle choisi', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    usePersonalisationStore.setState({ uxMode: 'contributeur' });
  });

  it('un aller-retour openai puis mistral rend mistral-medium-latest', async () => {
    const api = await import('../../services/api');
    await ouvrirOngletIA();

    fireEvent.click(screen.getByRole('radio', { name: /GPT \(OpenAI\)/ }));
    await waitFor(() => expect(vi.mocked(api.setLLMConfig)).toHaveBeenCalled());

    fireEvent.click(screen.getByRole('radio', { name: /Mistral AI/ }));
    await waitFor(() =>
      expect(vi.mocked(api.setLLMConfig).mock.calls.length).toBeGreaterThanOrEqual(2),
    );

    const envois = vi.mocked(api.setLLMConfig).mock.calls.map((appel) => [appel[0], appel[1]]);
    const retour = envois[envois.length - 1];
    expect(
      retour,
      `configuration enregistrée au retour : ${JSON.stringify(envois)}`,
    ).toEqual(['mistral', 'mistral-medium-latest']);
  });

  it('le sélecteur de modèle affiche à nouveau le modèle enregistré', async () => {
    await ouvrirOngletIA();
    const api = await import('../../services/api');

    fireEvent.click(screen.getByRole('radio', { name: /GPT \(OpenAI\)/ }));
    await waitFor(() => expect(vi.mocked(api.setLLMConfig)).toHaveBeenCalled());
    fireEvent.click(screen.getByRole('radio', { name: /Mistral AI/ }));

    await waitFor(() =>
      expect(screen.getByLabelText('Modèle')).toHaveValue('mistral-medium-latest'),
    );
  });

  it('un modèle explicitement choisi devient celui qu’on retrouve', async () => {
    const api = await import('../../services/api');
    await ouvrirOngletIA();

    fireEvent.change(screen.getByLabelText('Modèle'), {
      target: { value: 'mistral-small-latest' },
    });
    await waitFor(() =>
      expect(vi.mocked(api.setLLMConfig)).toHaveBeenCalledWith('mistral', 'mistral-small-latest'),
    );

    fireEvent.click(screen.getByRole('radio', { name: /GPT \(OpenAI\)/ }));
    await waitFor(() =>
      expect(vi.mocked(api.setLLMConfig).mock.calls.length).toBeGreaterThanOrEqual(2),
    );
    fireEvent.click(screen.getByRole('radio', { name: /Mistral AI/ }));

    await waitFor(() =>
      expect(vi.mocked(api.setLLMConfig).mock.calls.length).toBeGreaterThanOrEqual(3),
    );
    const envois = vi.mocked(api.setLLMConfig).mock.calls.map((appel) => [appel[0], appel[1]]);
    expect(envois[envois.length - 1]).toEqual(['mistral', 'mistral-small-latest']);
  });
});
