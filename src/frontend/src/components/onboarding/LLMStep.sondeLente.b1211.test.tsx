/**
 * B-1211 (garde, constat non reproduit) : suite supposée de B-1173. Quand la première vérification d'Ollama échoue
 * (sonde lente), qu'on choisit Ollama puis qu'on relance la vérification, le
 * modèle retenu restait celui du fournisseur précédent : le menu montrait un
 * modèle Ollama mais « Continuer » restait grisé.
 */
import { act, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { LLMStep } from './LLMStep';

const apiMocks = vi.hoisted(() => ({
  getApiKeysWithCorrupted: vi.fn(),
  getOllamaStatus: vi.fn(),
  getSystemResources: vi.fn(),
  setApiKey: vi.fn(),
  setLLMConfig: vi.fn(),
}));

vi.mock('../../services/api', () => apiMocks);

const catalogueMocks = vi.hoisted(() => ({ chargerCatalogue: vi.fn() }));
vi.mock('../../lib/catalogueModeles', async (importOriginal) => {
  const reel = await importOriginal<typeof import('../../lib/catalogueModeles')>();
  return {
    ...reel,
    chargerCatalogue: (...args: Parameters<typeof reel.chargerCatalogue>) =>
      catalogueMocks.chargerCatalogue(...args) ?? Promise.resolve(null),
  };
});

const gib = 1024 ** 3;

function statut(models: Array<Record<string, unknown>>) {
  return { available: true, base_url: 'http://ollama.test', models, error: null };
}

describe('B-1211 : vérification d’Ollama relancée après un échec', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.spyOn(console, 'error').mockImplementation(() => undefined);
  });
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('après « Réessayer la vérification », le modèle local capable est retenu et « Continuer » s’active', async () => {
    apiMocks.getApiKeysWithCorrupted.mockResolvedValue({ keys: {}, corrupted: [], sources: {} });
    apiMocks.getSystemResources.mockResolvedValue(null);
    apiMocks.setLLMConfig.mockResolvedValue({});
    apiMocks.getOllamaStatus
      .mockRejectedValueOnce(new Error('La vérification a pris trop de temps.'))
      .mockResolvedValue(statut([{ name: 'qwen3:8b', size: 5 * gib, modified_at: null, digest: null, gere_les_outils: true }]));
    render(<LLMStep onNext={vi.fn()} onBack={vi.fn()} />);
    await act(async () => Promise.resolve());
    await act(async () => Promise.resolve());
    const ollama = screen.queryByRole('radio', { name: /Ollama \(Local\)/ });
    if (ollama) fireEvent.click(ollama);
    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: 'Réessayer la vérification' }));
    });
    await act(async () => Promise.resolve());
    const radio = screen.getByRole('radio', { name: /Ollama \(Local\)/ });
    if (!(radio as HTMLInputElement).checked) fireEvent.click(radio);
    const select = screen.getByLabelText('Modèle') as HTMLSelectElement;
    const continuer = screen.getByTestId('onboarding-next-btn') as HTMLButtonElement;
    expect({ modele: select.value, continuerActif: !continuer.disabled })
      .toEqual({ modele: 'qwen3:8b', continuerActif: true });
  });
});
