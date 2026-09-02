/**
 * B-246 : le refus de format de clé API n'était pas signalé sur le champ.
 *
 * Le fond du refus était juste (« La clé API doit commencer par "sk-ant-" »,
 * validation locale, aucune requête émise), mais le message atterrissait dans
 * un bandeau rendu APRÈS le sélecteur de modèle, sans `id`, tandis que
 * `#llm-api-key` ne portait ni `aria-invalid` ni `aria-describedby` : le
 * fichier entier n'en contenait aucune occurrence. Une personne au lecteur
 * d'écran revenait sur le champ sans savoir qu'il était en faute, ni pourquoi.
 *
 * L'échec de configuration (bouton « Continuer ») garde son bandeau général :
 * il ne parle pas du champ, et le champ n'est même plus affiché quand une clé
 * est déjà enregistrée.
 */
import { act, fireEvent, render, screen } from '@testing-library/react';
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

describe('B-246 : une clé au mauvais préfixe est signalée sur le champ', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.spyOn(console, 'error').mockImplementation(() => undefined);
    apiMocks.getApiKeysWithCorrupted.mockResolvedValue({ keys: {}, corrupted: [], sources: {} });
    apiMocks.getOllamaStatus.mockResolvedValue({
      available: false,
      base_url: '',
      models: [],
      error: null,
    });
    apiMocks.getSystemResources.mockResolvedValue(null);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  async function afficherLEtape() {
    const { container } = render(<LLMStep onNext={vi.fn()} onBack={vi.fn()} />);
    await act(async () => { await Promise.resolve(); });
    // Par l'identifiant : le bouton oeil porte lui aussi « clé API » dans son
    // nom accessible, un getByLabelText serait ambigu.
    const champ = container.querySelector<HTMLInputElement>('input#llm-api-key');
    if (!champ) throw new Error('champ de clé API introuvable');
    return champ;
  }

  it('marque le champ en faute et l’associe au message', async () => {
    const champ = await afficherLEtape();
    fireEvent.change(champ, { target: { value: 'sk-test-0000' } });
    fireEvent.click(screen.getByRole('button', { name: 'Sauver' }));

    const message = await screen.findByRole('alert');
    expect(message).toHaveTextContent('sk-ant-');

    expect(champ).toHaveAttribute('aria-invalid', 'true');
    const decritPar = champ.getAttribute('aria-describedby');
    expect(decritPar).toBeTruthy();
    expect(message.id).toBe(decritPar);

    // Validation locale : rien ne part au serveur.
    expect(apiMocks.setApiKey).not.toHaveBeenCalled();
  });

  it('le message est rendu avec le champ, avant le sélecteur de modèle', async () => {
    const champ = await afficherLEtape();
    fireEvent.change(champ, { target: { value: 'sk-test-0000' } });
    fireEvent.click(screen.getByRole('button', { name: 'Sauver' }));

    const message = await screen.findByRole('alert');
    const selecteurModele = screen.getByLabelText('Modèle');
    // Node.DOCUMENT_POSITION_FOLLOWING : le sélecteur vient APRÈS le message.
    expect(message.compareDocumentPosition(selecteurModele) & 4).toBeTruthy();
  });

  it('la marque tombe dès que la saisie reprend', async () => {
    const champ = await afficherLEtape();
    fireEvent.change(champ, { target: { value: 'sk-test-0000' } });
    fireEvent.click(screen.getByRole('button', { name: 'Sauver' }));
    await screen.findByRole('alert');

    fireEvent.change(champ, { target: { value: 'sk-ant-0000' } });

    expect(champ).not.toHaveAttribute('aria-invalid');
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
  });
});
