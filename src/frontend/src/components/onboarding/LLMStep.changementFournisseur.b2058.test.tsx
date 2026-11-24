import { act, cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

const apiMocks = vi.hoisted(() => ({
  getApiKeysWithCorrupted: vi.fn(),
  getOllamaStatus: vi.fn(),
  getSystemResources: vi.fn(),
  setApiKey: vi.fn(),
  verifierCle: vi.fn(),
  setLLMConfig: vi.fn(),
}));
vi.mock('../../services/api', () => apiMocks);
vi.mock('../../lib/catalogueModeles', async (original) => ({
  ...await original<typeof import('../../lib/catalogueModeles')>(),
  chargerCatalogue: vi.fn().mockResolvedValue(null),
}));

import { LLMStep } from './LLMStep';

function differee<T>() {
  let resolve!: (value: T) => void;
  let reject!: (reason: Error) => void;
  const promise = new Promise<T>((ok, ko) => { resolve = ok; reject = ko; });
  return { promise, resolve, reject };
}

async function afficher(onNext = vi.fn()) {
  await act(async () => { render(<LLMStep onNext={onNext} onBack={vi.fn()} />); });
}

async function choisir(nom: RegExp) {
  await act(async () => { fireEvent.click(screen.getByRole('radio', { name: nom })); });
}

function saisir(cle = 'sk-ant-cle-a') {
  fireEvent.change(screen.getByLabelText(/^Clé API /), { target: { value: cle } });
}

async function sauver() {
  await act(async () => { fireEvent.click(screen.getByRole('button', { name: 'Sauver' })); });
}

function sansResultatDeA() {
  expect(screen.queryByText('Clé API enregistrée')).toBeNull();
  expect(screen.queryByTestId('verification-cle')).toBeNull();
  expect(screen.queryByTestId('llm-origine-cle')).toBeNull();
  expect(screen.getByTestId('onboarding-next-btn')).toBeDisabled();
}

describe('B-2058 : chaque réponse reste liée à son fournisseur et à sa demande', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.clearAllMocks();
    Object.values(apiMocks).forEach((mock) => mock.mockReset());
    apiMocks.getApiKeysWithCorrupted.mockResolvedValue({ keys: {}, corrupted: [], sources: {} });
    apiMocks.getOllamaStatus.mockResolvedValue({ available: false, models: [] });
    apiMocks.getSystemResources.mockResolvedValue(null);
    apiMocks.setApiKey.mockResolvedValue(undefined);
    apiMocks.verifierCle.mockResolvedValue({ etat: 'acceptee', message: 'Clé A acceptée' });
  });

  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
    vi.useRealTimers();
  });

  it('une sauvegarde de A terminée sous B ne valide pas B et conserve sa saisie', async () => {
    const sauvegarde = differee<void>();
    apiMocks.setApiKey.mockReturnValue(sauvegarde.promise);
    apiMocks.verifierCle.mockRejectedValue(new Error('vérification indisponible'));
    await afficher();
    saisir();
    await sauver();
    await choisir(/GPT \(OpenAI\)/);
    saisir('sk-proj-cle-b');
    await act(async () => { await vi.advanceTimersByTimeAsync(30_000); });
    sansResultatDeA();

    await act(async () => { sauvegarde.resolve(); });
    sansResultatDeA();
    expect(screen.getByLabelText(/^Clé API /)).toHaveValue('sk-proj-cle-b');
    expect(apiMocks.setApiKey).toHaveBeenCalledWith('anthropic', 'sk-ant-cle-a');
    await choisir(/Claude \(Anthropic\)/);
    expect(screen.getByTestId('llm-origine-cle')).toHaveTextContent('chiffrée localement');
    expect(screen.getByText('Clé API enregistrée')).toBeInTheDocument();
    expect(screen.getByTestId('onboarding-next-btn')).toBeEnabled();
    await act(async () => { await vi.advanceTimersByTimeAsync(3000); });
    expect(screen.queryByText('Clé API enregistrée')).toBeNull();
    expect(screen.getByTestId('onboarding-next-btn')).toBeEnabled();
  });

  it.each(['acceptee', 'refusee', 'rejet'])('une vérification tardive de A (%s) reste sous A au retour', async (etat) => {
    const verification = differee<{ etat: string; message: string }>();
    apiMocks.verifierCle.mockReturnValue(verification.promise);
    await afficher();
    saisir();
    await sauver();
    expect(screen.getByTestId('verification-cle')).toHaveAttribute('data-etat', 'en_cours');
    await choisir(/GPT \(OpenAI\)/);
    await act(async () => {
      if (etat === 'rejet') verification.reject(new Error('service indisponible'));
      else verification.resolve({ etat, message: `Verdict A : ${etat}` });
    });
    sansResultatDeA();

    await choisir(/Claude \(Anthropic\)/);
    expect(screen.getByTestId('llm-origine-cle')).toHaveTextContent('chiffrée localement');
    expect(screen.getByTestId('onboarding-next-btn')).toBeEnabled();
    if (etat === 'rejet') {
      expect(screen.queryByTestId('verification-cle')).toBeNull();
      expect(screen.getByText('Clé API enregistrée')).toBeInTheDocument();
    } else {
      expect(screen.getByTestId('verification-cle')).toHaveAttribute('data-etat', etat);
      expect(screen.getByTestId('verification-cle')).toHaveTextContent(`Verdict A : ${etat}`);
    }
  });

  it('un échec de sauvegarde de A reste sous A et ne bloque pas la saisie de B', async () => {
    const sauvegarde = differee<void>();
    apiMocks.setApiKey.mockReturnValue(sauvegarde.promise);
    await afficher();
    saisir();
    await sauver();
    await choisir(/GPT \(OpenAI\)/);
    saisir('sk-proj-cle-b');
    expect(screen.getByRole('button', { name: 'Sauver' })).toBeEnabled();
    await act(async () => { sauvegarde.reject(new Error('Échec coffre A')); });
    expect(screen.queryByText('Échec coffre A')).toBeNull();
    sansResultatDeA();
    await choisir(/Claude \(Anthropic\)/);
    expect(screen.getByRole('alert')).toHaveTextContent('Échec coffre A');
    expect(screen.getByTestId('onboarding-next-btn')).toBeDisabled();
  });

  it('la fin de A ne retire pas l’attente de la sauvegarde de B', async () => {
    const a = differee<void>();
    const b = differee<void>();
    apiMocks.setApiKey.mockReturnValueOnce(a.promise).mockReturnValueOnce(b.promise);
    await afficher();
    saisir();
    await sauver();
    await choisir(/GPT \(OpenAI\)/);
    saisir('sk-proj-cle-b');
    const sauverB = screen.getByRole('button', { name: 'Sauver' });
    await sauver();
    expect(apiMocks.setApiKey).toHaveBeenCalledTimes(2);
    await act(async () => { a.resolve(); });
    expect(screen.getByLabelText(/^Clé API /)).toHaveValue('sk-proj-cle-b');
    expect(sauverB).toBeDisabled();
    sansResultatDeA();
    await act(async () => { b.resolve(); });
    expect(screen.getByTestId('llm-origine-cle')).toHaveTextContent('chiffrée localement');
    expect(screen.getByTestId('onboarding-next-btn')).toBeEnabled();
  });

  it('Entrée pendant une sauvegarde ne lance pas une deuxième écriture de la clé', async () => {
    const sauvegarde = differee<void>();
    apiMocks.setApiKey.mockReturnValue(sauvegarde.promise);
    await afficher();
    saisir();
    await sauver();
    fireEvent.keyDown(screen.getByLabelText(/^Clé API /), { key: 'Enter' });
    expect(apiMocks.setApiKey).toHaveBeenCalledTimes(1);
    await act(async () => { sauvegarde.resolve(); });
  });

  it('la revérification attend l’écriture pour garder la clé enregistrée', async () => {
    const sauvegarde = differee<void>();
    const lectureAvantEcriture = differee<{ keys: Record<string, boolean>; corrupted: string[]; sources: Record<string, string> }>();
    apiMocks.setApiKey.mockReturnValue(sauvegarde.promise);
    await afficher();
    saisir();
    await sauver();
    apiMocks.getApiKeysWithCorrupted.mockReturnValueOnce(lectureAvantEcriture.promise);

    const reverifier = screen.getByRole('button', { name: 'Revérifier la disponibilité' });
    await act(async () => { fireEvent.click(reverifier); });
    await act(async () => { sauvegarde.resolve(); });
    await act(async () => { lectureAvantEcriture.resolve({ keys: {}, corrupted: [], sources: {} }); });

    expect(screen.getByTestId('llm-origine-cle')).toHaveTextContent('chiffrée localement');
    expect(apiMocks.getApiKeysWithCorrupted).toHaveBeenCalledTimes(1);
    expect(screen.getByTestId('onboarding-next-btn')).toBeEnabled();
    expect(screen.getByRole('button', { name: 'Revérifier la disponibilité' })).toBeEnabled();
  });

  it.each([
    ['anthropic', /Claude \(Anthropic\)/, 'sk-ant-test', true],
    ['anthropic', /Claude \(Anthropic\)/, 'sk-ant-test', false],
    ['openai', /GPT \(OpenAI\)/, 'sk-proj-test', true],
    ['openai', /GPT \(OpenAI\)/, 'sk-proj-test', false],
    ['gemini', /Gemini \(Google\)/, 'gemini-factice', true],
    ['gemini', /Gemini \(Google\)/, 'gemini-factice', false],
    ['mistral', /Mistral AI/, 'mistral-factice', true],
    ['mistral', /Mistral AI/, 'mistral-factice', false],
    ['synthetic', /^Synthetic/, 'synthetic-factice', true],
    ['synthetic', /^Synthetic/, 'synthetic-factice', false],
  ] as const)('rejoue la lecture du coffre pour %s avec %s et %s (écriture=%s)', async (fournisseur, nom, cle, succes) => {
    const sauvegarde = differee<void>();
    apiMocks.setApiKey.mockReturnValue(sauvegarde.promise);
    await afficher();
    if (fournisseur !== 'anthropic') await choisir(nom);
    saisir(cle);
    await sauver();

    const reverifier = screen.getByRole('button', { name: 'Revérifier la disponibilité' });
    expect(reverifier).toBeDisabled();
    await act(async () => { fireEvent.click(reverifier); });
    expect(apiMocks.getApiKeysWithCorrupted).toHaveBeenCalledTimes(1);

    await act(async () => {
      if (succes) sauvegarde.resolve();
      else sauvegarde.reject(new Error('Écriture du coffre refusée'));
    });
    expect(reverifier).toBeEnabled();
    if (!succes) expect(screen.getByRole('alert')).toHaveTextContent('Écriture du coffre refusée');
    apiMocks.getApiKeysWithCorrupted.mockResolvedValueOnce({
      keys: { [fournisseur]: succes }, corrupted: [], sources: succes ? { [fournisseur]: 'coffre' } : {},
    });
    await act(async () => { fireEvent.click(reverifier); });
    expect(apiMocks.getApiKeysWithCorrupted).toHaveBeenCalledTimes(2);
    if (succes) expect(screen.getByTestId('llm-origine-cle')).toHaveTextContent('chiffrée localement');
    else expect(screen.queryByTestId('llm-origine-cle')).toBeNull();
  });

  it.each(['acceptee', 'rejet'])('une ancienne vérification (%s) ne remplace pas la nouvelle demande de A', async (etat) => {
    const ancienne = differee<{ etat: string; message: string }>();
    apiMocks.verifierCle.mockReturnValueOnce(ancienne.promise)
      .mockResolvedValueOnce({ etat: 'refusee', message: 'Nouvelle clé A refusée' });
    await afficher();
    saisir();
    await sauver();
    // Le rechargement constate une clé retirée du coffre entre-temps.
    await act(async () => { fireEvent.click(screen.getByRole('button', { name: 'Revérifier la disponibilité' })); });
    saisir('sk-ant-nouvelle-cle-a');
    await sauver();
    expect(screen.getByTestId('verification-cle')).toHaveTextContent('Nouvelle clé A refusée');
    await act(async () => {
      if (etat === 'rejet') ancienne.reject(new Error('ancienne vérification indisponible'));
      else ancienne.resolve({ etat, message: 'Ancienne clé A acceptée' });
    });
    expect(screen.getByTestId('verification-cle')).toHaveAttribute('data-etat', 'refusee');
    expect(screen.getByTestId('verification-cle')).toHaveTextContent('Nouvelle clé A refusée');
  });

  it.each(['succes', 'echec'])('la configuration finale (%s) verrouille le fournisseur jusqu’à sa réponse', async (issue) => {
    const configuration = differee<void>();
    const onNext = vi.fn();
    apiMocks.setLLMConfig.mockReturnValue(configuration.promise);
    await afficher(onNext);
    saisir();
    await sauver();
    await act(async () => { fireEvent.click(screen.getByTestId('onboarding-next-btn')); });
    const b = screen.getByRole('radio', { name: /GPT \(OpenAI\)/ });
    expect(b).toBeDisabled();
    await choisir(/GPT \(OpenAI\)/);
    expect(screen.getByRole('radio', { name: /Claude \(Anthropic\)/ })).toHaveAttribute('aria-checked', 'true');
    await act(async () => {
      if (issue === 'echec') configuration.reject(new Error('Configuration A impossible'));
      else configuration.resolve();
    });
    if (issue === 'echec') {
      expect(screen.getByRole('alert')).toHaveTextContent('Configuration A impossible');
      expect(b).toBeEnabled();
      expect(onNext).not.toHaveBeenCalled();
    } else {
      expect(onNext).toHaveBeenCalledExactlyOnceWith('anthropic');
    }
  });

  it('une sonde Ollama ne change pas automatiquement le fournisseur pendant sa configuration', async () => {
    const configuration = differee<void>();
    const onNext = vi.fn();
    apiMocks.getApiKeysWithCorrupted.mockResolvedValue({ keys: { anthropic: true }, sources: {} });
    apiMocks.setLLMConfig.mockReturnValue(configuration.promise);
    await afficher(onNext);
    await act(async () => { fireEvent.click(screen.getByTestId('onboarding-next-btn')); });
    apiMocks.getOllamaStatus.mockResolvedValue({ available: true, models: [{ name: 'qwen3.5:4b' }] });
    await act(async () => { fireEvent.click(screen.getByText('Vérifier Ollama après l’installation')); });
    expect(screen.getByRole('radio', { name: /Claude \(Anthropic\)/ })).toHaveAttribute('aria-checked', 'true');
    expect(apiMocks.getOllamaStatus).toHaveBeenCalledTimes(1);
    await act(async () => { configuration.resolve(); });
    expect(onNext).toHaveBeenCalledExactlyOnceWith('anthropic');
  });
});
