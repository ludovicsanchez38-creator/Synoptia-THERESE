/**
 * B-1348 (boucle DQ), audit bêta du 27/10/2026 (A2-23) : une clé fausse au bon
 * format s'affichait « Clé API enregistrée » ; l'échec n'arrivait qu'au premier
 * message. Après l'enregistrement, l'écran dit ce que le fournisseur répond.
 */
import { act, cleanup, fireEvent, render, screen } from '@testing-library/react';
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

async function saisir(cle = 'sk-ant-api03-fausse-cle') {
  await act(async () => { render(<LLMStep onNext={vi.fn()} onBack={vi.fn()} />); });
  const champ = document.querySelector<HTMLInputElement>('input#llm-api-key');
  if (!champ) throw new Error('champ de clé introuvable');
  fireEvent.change(champ, { target: { value: cle } });
}

async function enregistrer() {
  await saisir();
  await act(async () => {
    fireEvent.click(screen.getByRole('button', { name: 'Sauver' }));
    // Le clic lance une sauvegarde asynchrone. Son absence de verdict n'est
    // pas un signal de fin : attendre la réponse puis laisser React la rendre.
    await apiMocks.setApiKey.mock.results.at(-1)!.value;
  });
}

describe('La clé enregistrée est vérifiée auprès du fournisseur', () => {
  beforeEach(() => {
    // Comme LLMStep.test.tsx : le message « enregistré » expire après 3 s.
    // Ni la charge de la machine ni les frames d'entrée ne pilotent ce délai.
    vi.useFakeTimers();
    vi.clearAllMocks();
    vi.spyOn(console, 'error').mockImplementation(() => undefined);
    apiMocks.getApiKeysWithCorrupted.mockResolvedValue({ keys: {}, corrupted: [], sources: {} });
    apiMocks.getOllamaStatus.mockResolvedValue({ available: false, base_url: '', models: [], error: null });
    apiMocks.getSystemResources.mockResolvedValue(null);
    apiMocks.setApiKey.mockResolvedValue(undefined);
  });

  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
    vi.useRealTimers();
  });

  it('une clé refusée le dit tout de suite, en alerte, avec le geste', async () => {
    apiMocks.verifierCle.mockResolvedValue({ provider: 'anthropic', etat: 'refusee', message: 'Anthropic refuse cette clé. Vérifie que tu as copié toute la clé.' });
    await enregistrer();

    const verdict = screen.getByTestId('verification-cle');
    expect(verdict).toHaveAttribute('data-etat', 'refusee');
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
    const verdict = screen.getByTestId('verification-cle');
    expect(verdict).toHaveAttribute('data-etat', etat);
    expect(verdict).toHaveAttribute('role', role);
  });

  it('une vérification indisponible n’affirme rien et garde « Clé API enregistrée »', async () => {
    apiMocks.verifierCle.mockRejectedValue(new Error('moteur indisponible'));
    await enregistrer();
    expect(screen.getByText('Clé API enregistrée')).toBeInTheDocument();
    expect(screen.queryByTestId('verification-cle')).toBeNull();
    expect(apiMocks.verifierCle).toHaveBeenCalledWith('anthropic');
  });

  it('attend une sauvegarde lente puis un rejet différé, même à la limite des 3 s', async () => {
    let terminerSauvegarde!: () => void;
    let refuserVerification!: (erreur: Error) => void;
    apiMocks.setApiKey.mockReturnValue(new Promise<void>((resolve) => { terminerSauvegarde = resolve; }));
    apiMocks.verifierCle.mockReturnValue(new Promise<never>((_resolve, reject) => { refuserVerification = reject; }));
    await saisir();
    const sauver = screen.getByRole('button', { name: 'Sauver' });
    fireEvent.click(sauver);

    await act(async () => { await vi.advanceTimersByTimeAsync(30_000); });
    expect(sauver).toBeDisabled();
    expect(apiMocks.verifierCle).not.toHaveBeenCalled();
    expect(screen.queryByText('Clé API enregistrée')).toBeNull();
    expect(screen.queryByTestId('verification-cle')).toBeNull();

    await act(async () => { terminerSauvegarde(); });
    expect(screen.getByTestId('verification-cle')).toHaveAttribute('data-etat', 'en_cours');
    expect(screen.queryByText('Clé API enregistrée')).toBeNull();
    await act(async () => { await vi.advanceTimersByTimeAsync(2999); });
    expect(screen.getByTestId('verification-cle')).toHaveAttribute('data-etat', 'en_cours');

    await act(async () => { refuserVerification(new Error('moteur indisponible')); });
    expect(screen.getByText('Clé API enregistrée')).toBeInTheDocument();
    expect(screen.queryByTestId('verification-cle')).toBeNull();
    expect(apiMocks.verifierCle).toHaveBeenCalledWith('anthropic');

    await act(async () => { await vi.advanceTimersByTimeAsync(1); });
    expect(screen.queryByText('Clé API enregistrée')).toBeNull();
    expect(screen.getByTestId('llm-origine-cle')).toHaveTextContent('Clé API configurée (chiffrée localement)');
  });
});
