/**
 * Audit bêta du 27/10/2026 (A2-22) : Gérard colle sa clé, l'écran affiche bien
 * « sk-ant-… » et répond « La clé API doit commencer par "sk-ant-" ». La copie
 * avait pris une espace devant. Le contrôle de préfixe portait sur la saisie
 * brute ; le moteur, lui, nettoie déjà (B-510).
 */
import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

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

import { LLMStep } from './LLMStep';

const CLE = 'sk-ant-api03-AbCdEf0123456789';

describe('Une clé collée avec des blancs autour est acceptée telle qu’elle se lit', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.spyOn(console, 'error').mockImplementation(() => undefined);
    apiMocks.getApiKeysWithCorrupted.mockResolvedValue({ keys: {}, corrupted: [], sources: {} });
    apiMocks.getOllamaStatus.mockResolvedValue({ available: false, base_url: '', models: [], error: null });
    apiMocks.getSystemResources.mockResolvedValue(null);
    apiMocks.setApiKey.mockResolvedValue(undefined);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  async function coller(valeur: string) {
    const { container } = render(<LLMStep onNext={vi.fn()} onBack={vi.fn()} />);
    await act(async () => { await Promise.resolve(); });
    const champ = container.querySelector<HTMLInputElement>('input#llm-api-key');
    if (!champ) throw new Error('champ de clé API introuvable');
    fireEvent.change(champ, { target: { value: valeur } });
    fireEvent.click(screen.getByRole('button', { name: 'Sauver' }));
  }

  it.each([
    [' ' + CLE], [CLE + ' '], [CLE + '\n'], [CLE + '\r\n'], ['\t' + CLE], ['  ' + CLE + '  '],
    [' ' + CLE], ['\n' + CLE + '\n'],
  ])('« %j » part nettoyée, sans message d’erreur', async (saisie) => {
    await coller(saisie);

    await waitFor(() => expect(apiMocks.setApiKey).toHaveBeenCalledWith('anthropic', CLE));
    expect(screen.queryByText(/doit commencer par/)).toBeNull();
  });

  it('une vraie clé d’un autre fournisseur reste refusée, même nettoyée', async () => {
    await coller('  sk-proj-0000  ');

    expect(await screen.findByRole('alert')).toHaveTextContent('sk-ant-');
    expect(apiMocks.setApiKey).not.toHaveBeenCalled();
  });
});
