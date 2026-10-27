/**
 * B-1348 (boucle DQ), audit bêta du 27/10/2026 (A2-23) : une clé fausse au bon
 * format s'affichait « Clé API enregistrée » ; l'échec n'arrivait qu'au premier
 * message. Après l'enregistrement, l'écran dit ce que le fournisseur répond.
 */
import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

const apiMocks = vi.hoisted(() => ({
  getApiKeysWithCorrupted: vi.fn(),
  getOllamaStatus: vi.fn(),
  getSystemResources: vi.fn(),
  setApiKey: vi.fn(),
  setLLMConfig: vi.fn(),
  verifierCle: vi.fn(),
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

async function enregistrer(cle = 'sk-ant-api03-fausse-cle') {
  const { container } = render(<LLMStep onNext={vi.fn()} onBack={vi.fn()} />);
  await act(async () => { await Promise.resolve(); });
  const champ = container.querySelector<HTMLInputElement>('input#llm-api-key');
  if (!champ) throw new Error('champ de clé introuvable');
  fireEvent.change(champ, { target: { value: cle } });
  fireEvent.click(screen.getByRole('button', { name: 'Sauver' }));
  return champ;
}

describe('La clé enregistrée est vérifiée auprès du fournisseur', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.spyOn(console, 'error').mockImplementation(() => undefined);
    apiMocks.getApiKeysWithCorrupted.mockResolvedValue({ keys: {}, corrupted: [], sources: {} });
    apiMocks.getOllamaStatus.mockResolvedValue({ available: false, base_url: '', models: [], error: null });
    apiMocks.getSystemResources.mockResolvedValue(null);
    apiMocks.setApiKey.mockResolvedValue(undefined);
  });

  afterEach(() => vi.restoreAllMocks());

  it('une clé refusée le dit tout de suite, en alerte, avec le geste', async () => {
    apiMocks.verifierCle.mockResolvedValue({ provider: 'anthropic', etat: 'refusee', message: 'Anthropic refuse cette clé. Vérifie que tu as copié toute la clé.' });
    await enregistrer();

    const verdict = await screen.findByTestId('verification-cle');
    await waitFor(() => expect(verdict).toHaveAttribute('data-etat', 'refusee'));
    expect(verdict).toHaveAttribute('role', 'alert');
    expect(verdict).toHaveTextContent('copié toute la clé');
    expect(apiMocks.verifierCle).toHaveBeenCalledWith('anthropic');
    expect(screen.queryByText('Clé API enregistrée')).toBeNull();
  });

  it.each([
    ['acceptee', 'status'], ['limite', 'status'], ['non_rattachee', 'alert'], ['paiement', 'alert'],
    ['injoignable', 'status'], ['non_verifiable', 'status'], ['incertaine', 'status'],
  ])('état %s : rôle %s', async (etat, role) => {
    apiMocks.verifierCle.mockResolvedValue({ provider: 'anthropic', etat, message: `message ${etat}` });
    await enregistrer();
    const verdict = await screen.findByTestId('verification-cle');
    await waitFor(() => expect(verdict).toHaveAttribute('data-etat', etat));
    expect(verdict).toHaveAttribute('role', role);
  });

  it('une vérification indisponible n’affirme rien et garde « Clé API enregistrée »', async () => {
    apiMocks.verifierCle.mockRejectedValue(new Error('moteur indisponible'));
    await enregistrer();
    await waitFor(() => expect(screen.queryByTestId('verification-cle')).toBeNull());
    expect(screen.getByText('Clé API enregistrée')).toBeInTheDocument();
  });
});
