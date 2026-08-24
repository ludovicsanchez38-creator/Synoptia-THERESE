/**
 * Le chemin Email depuis les Réglages (0.44).
 *
 * L'inventaire du 13/08 a établi que l'assistant de configuration email n'a
 * AUCUN chemin par les Réglages : la rubrique Services ne contenait que
 * Images, Transcription vocale, Recherche Web et Extraction automatique. Le
 * testeur l'a redit le 18/08 : « les paramètres de la messagerie devraient,
 * comme tout le reste, se trouver dans paramètres ».
 *
 * Cette section ne DÉPLACE pas l'assistant — il vit dans la vue Email et y
 * reste. Elle donne le chemin : voir ses comptes, et y aller en un clic.
 */
import { describe, expect, it, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';

const apiMock = vi.hoisted(() => ({
  getEmailAuthStatus: vi.fn(),
}));
vi.mock('../../services/api/email', () => apiMock);

const fermerReglages = vi.hoisted(() => vi.fn());
vi.mock('../../stores/panelStore', () => ({
  usePanelStore: Object.assign(
    (selecteur: (s: Record<string, unknown>) => unknown) =>
      selecteur({ closeSettings: fermerReglages }),
    { getState: () => ({ closeSettings: fermerReglages }) },
  ),
}));

const allerALaVue = vi.hoisted(() => vi.fn());
vi.mock('../../stores/navigationStore', () => ({
  useNavigationStore: Object.assign(
    (selecteur: (s: Record<string, unknown>) => unknown) =>
      selecteur({ setView: allerALaVue }),
    { getState: () => ({ setView: allerALaVue }) },
  ),
}));

import { EmailAccountsSection } from './EmailAccountsSection';

beforeEach(() => {
  vi.clearAllMocks();
});

describe('La section Comptes email des Réglages', () => {
  it('montre les comptes connectés', async () => {
    apiMock.getEmailAuthStatus.mockResolvedValue({
      connected: true,
      accounts: [{ id: '1', email: 'ludo@synoptia.fr', provider: 'gmail' }],
    });

    render(<EmailAccountsSection />);

    await waitFor(() => {
      expect(screen.getByText('ludo@synoptia.fr')).toBeInTheDocument();
    });
  });

  it('dit clairement quand aucun compte n’est connecté', async () => {
    apiMock.getEmailAuthStatus.mockResolvedValue({ connected: false, accounts: [] });

    render(<EmailAccountsSection />);

    await waitFor(() => {
      expect(screen.getByText(/aucun compte/i)).toBeInTheDocument();
    });
  });

  it('mène à la configuration en un clic, Réglages refermés', async () => {
    apiMock.getEmailAuthStatus.mockResolvedValue({ connected: false, accounts: [] });

    render(<EmailAccountsSection />);
    await waitFor(() => screen.getByTestId('email-accounts-open'));

    fireEvent.click(screen.getByTestId('email-accounts-open'));

    expect(fermerReglages).toHaveBeenCalledOnce();
    expect(allerALaVue).toHaveBeenCalledWith('email');
  });

  it('garde le chemin ouvert même si la liste des comptes échoue', async () => {
    // Le bouton EST la fonctionnalité : un backend grognon ne doit pas le
    // faire disparaître — ce serait recréer l'impasse qu'on corrige.
    apiMock.getEmailAuthStatus.mockRejectedValue(new Error('backend indisponible'));

    render(<EmailAccountsSection />);

    await waitFor(() => {
      expect(screen.getByTestId('email-accounts-open')).toBeInTheDocument();
    });
  });
});
