/**
 * B-239 (volet écran) : l'onboarding annonçait « chiffrée localement » pour une
 * clé qui n'a jamais été saisie, jamais stockée et jamais chiffrée — elle vient
 * d'une variable d'environnement.
 *
 * Le contrat d'API a été corrigé côté serveur : `GET /api/config/` transporte
 * désormais `api_keys_source` (« coffre », « environnement », « corrompue »,
 * « absente ») à côté du booléen historique. L'écran doit lire cette origine au
 * lieu de déduire le chiffrement d'un simple « il y a une clé ».
 *
 * Le test rend le pas et lit la phrase affichée : une assertion sur la fonction
 * d'API laisserait passer un écran qui reçoit l'origine et continue d'écrire la
 * mauvaise phrase.
 */
import { render, screen, waitForElementToBeRemoved } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { LLMStep } from './LLMStep';

const apiMocks = vi.hoisted(() => ({
  // Le booléen historique reste servi : sans lui, un écran non corrigé
  // planterait au lieu d'afficher sa phrase fautive, et le rouge ne prouverait
  // plus rien.
  getApiKeys: vi.fn(),
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

function poserOrigine(origine: string) {
  apiMocks.getApiKeys.mockResolvedValue({ anthropic: true });
  apiMocks.getApiKeysWithCorrupted.mockResolvedValue({
    keys: { anthropic: true },
    corrupted: [],
    sources: { anthropic: origine },
  });
}

/** Le pas affiche d'abord « Vérification des modèles disponibles… » : sans
 *  cette attente, une assertion d'absence passerait sur un écran encore vide. */
async function ecranCharge() {
  await waitForElementToBeRemoved(
    () => screen.queryByText('Vérification des modèles disponibles…'),
  );
}

describe("B-239 : l'écran dit d'où vient la clé", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.spyOn(console, 'error').mockImplementation(() => undefined);
    apiMocks.getOllamaStatus.mockResolvedValue({
      available: false, base_url: '', models: [], error: null,
    });
    apiMocks.getSystemResources.mockResolvedValue(null);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('ne promet pas le chiffrement local pour une clé lue dans l’environnement', async () => {
    poserOrigine('environnement');
    render(<LLMStep onNext={vi.fn()} onBack={vi.fn()} />);

    // Le défaut d'abord : l'écran ne doit plus affirmer un chiffrement qui
    // n'a pas eu lieu. L'assertion suivante vérifie qu'il dit la vérité.
    await ecranCharge();
    expect(screen.queryByText(/chiffrée localement/i)).not.toBeInTheDocument();

    const mention = await screen.findByTestId('llm-origine-cle');
    expect(mention).toHaveTextContent(/environnement/i);
  });

  it('garde la mention du chiffrement pour une clé confiée au coffre', async () => {
    poserOrigine('coffre');
    render(<LLMStep onNext={vi.fn()} onBack={vi.fn()} />);

    const mention = await screen.findByTestId('llm-origine-cle');
    expect(mention).toHaveTextContent(/chiffrée localement/i);
  });

  it('n’affirme rien quand le serveur ne dit pas l’origine', async () => {
    apiMocks.getApiKeys.mockResolvedValue({ anthropic: true });
    apiMocks.getApiKeysWithCorrupted.mockResolvedValue({
      keys: { anthropic: true },
      corrupted: [],
      sources: {},
    });
    render(<LLMStep onNext={vi.fn()} onBack={vi.fn()} />);

    const mention = await screen.findByTestId('llm-origine-cle');
    expect(mention).not.toHaveTextContent(/chiffrée localement/i);
    expect(mention).not.toHaveTextContent(/environnement/i);
  });
});
