/**
 * Démarrage et accords (correctifs 0.83, parcours e2e 07).
 *
 * Le lot confidentialité a inséré `synchroniserConsentements()` dans la
 * boucle de démarrage. Un import refusé y faisait échouer toute la tentative,
 * relancée cinq fois, puis la vérification de mise en route était sautée.
 * Une synchronisation des accords en échec ne bloque plus le démarrage : elle
 * est journalisée et retentée au démarrage suivant, le cache local intact.
 *
 * Les autres chemins de la séquence (cloisonnement, profil changé, moteur
 * injoignable, fin de l'assistant) sont rejoués ici pour vérifier qu'ils
 * n'ont pas bougé.
 */
import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('./components/onboarding', () => ({
  OnboardingWizard: ({ isOpen, onComplete }: { isOpen: boolean; onComplete: () => void }) =>
    isOpen ? <button type="button" onClick={onComplete}>Terminer la configuration</button> : null,
}));
vi.mock('./components/prototype/ConversationCanvasPrototype', () => ({
  ConversationCanvasPrototype: () => <main data-testid="canevas-double" id="main-content" />,
}));
vi.mock('./components/actions', () => ({ ActionPanel: () => null }));
vi.mock('./components/app/CommonToolConfirmationLayer', () => ({ CommonToolConfirmationLayer: () => null }));
vi.mock('./components/app/ExternalActionConfirmation', () => ({
  PrototypeExternalActionConfirmationProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));
vi.mock('./components/ui/Notifications', () => ({ Notifications: () => null }));
vi.mock('./components/ui/UpdateBanner', () => ({ UpdateBanner: () => null }));
vi.mock('./components/ui/SidecarStatusBanner', () => ({ SidecarStatusBanner: () => null }));
vi.mock('./hooks/useHealthCheck', () => ({ useHealthCheck: vi.fn() }));
vi.mock('./lib/capacites/generation', () => ({
  controlerGenerationAuDemarrage: vi.fn().mockResolvedValue(undefined),
}));
vi.mock('./lib/profileStorageIsolation', () => ({
  isolateDataProfilePersistence: vi.fn(),
}));
vi.mock('./lib/consentSync', async (importOriginal) => ({
  ...(await importOriginal<typeof import('./lib/consentSync')>()),
  synchroniserConsentements: vi.fn(),
}));
vi.mock('./services/api', async (importOriginal) => ({
  ...(await importOriginal<typeof import('./services/api')>()),
  initializeAuth: vi.fn(),
  getStats: vi.fn(),
  getOnboardingStatus: vi.fn(),
}));

import App from './App';
import * as api from './services/api';
import { synchroniserConsentements } from './lib/consentSync';
import { isolateDataProfilePersistence } from './lib/profileStorageIsolation';

const synchro = vi.mocked(synchroniserConsentements);
const statut = vi.mocked(api.getOnboardingStatus);
const isolation = vi.mocked(isolateDataProfilePersistence);

describe('Démarrage : la synchronisation des accords ne bloque jamais la mise en route', () => {
  let avertissements: ReturnType<typeof vi.spyOn>;

  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(api.initializeAuth).mockResolvedValue(undefined);
    vi.mocked(api.getStats).mockResolvedValue({ data_dir: '/profils/test' } as Awaited<ReturnType<typeof api.getStats>>);
    isolation.mockReturnValue('unchanged');
    synchro.mockResolvedValue(undefined);
    statut.mockResolvedValue({ completed: true } as Awaited<ReturnType<typeof api.getOnboardingStatus>>);
    avertissements = vi.spyOn(console, 'warn').mockImplementation(() => {});
  });

  afterEach(() => {
    avertissements.mockRestore();
  });

  it('accords synchronisés : la mise en route est vérifiée une fois et l’assistant s’ouvre si elle manque', async () => {
    statut.mockResolvedValue({ completed: false } as Awaited<ReturnType<typeof api.getOnboardingStatus>>);
    render(<App />);

    expect(await screen.findByRole('button', { name: 'Terminer la configuration' })).toBeInTheDocument();
    expect(synchro).toHaveBeenCalledTimes(1);
    expect(statut).toHaveBeenCalledTimes(1);
  });

  it('import refusé : le démarrage continue, une seule tentative, et l’assistant s’ouvre quand même', async () => {
    synchro.mockRejectedValue(new Error('Écriture non autorisée par ce scénario de contrôle.'));
    statut.mockResolvedValue({ completed: false } as Awaited<ReturnType<typeof api.getOnboardingStatus>>);
    render(<App />);

    expect(await screen.findByRole('button', { name: 'Terminer la configuration' }, { timeout: 3000 })).toBeInTheDocument();
    expect(synchro).toHaveBeenCalledTimes(1);
    expect(api.initializeAuth).toHaveBeenCalledTimes(1);
    expect(statut).toHaveBeenCalledTimes(1);
    expect(avertissements).toHaveBeenCalledWith(
      expect.stringContaining('accords'), expect.objectContaining({ message: expect.stringContaining('Écriture non autorisée') }));
  });

  it('import refusé, mise en route faite : l’application s’ouvre sans assistant', async () => {
    synchro.mockRejectedValue(new Error('Moteur indisponible'));
    render(<App />);

    expect(await screen.findByTestId('canevas-double', {}, { timeout: 3000 })).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Terminer la configuration' })).not.toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Aller au contenu principal' })).toHaveAttribute('href', '#main-content');
    expect(synchro).toHaveBeenCalledTimes(1);
    expect(statut).toHaveBeenCalledTimes(1);
  });

  it('fin de l’assistant : il se ferme et la mise en route est mémorisée', async () => {
    statut.mockResolvedValue({ completed: false } as Awaited<ReturnType<typeof api.getOnboardingStatus>>);
    render(<App />);
    const terminer = await screen.findByRole('button', { name: 'Terminer la configuration' });

    await act(async () => { fireEvent.click(terminer); });

    expect(screen.queryByRole('button', { name: 'Terminer la configuration' })).not.toBeInTheDocument();
    expect(localStorage.setItem).toHaveBeenCalledWith('therese-onboarding-done', 'true');
  });

  it('profil changé : la page se recharge sans synchroniser ni vérifier la mise en route', async () => {
    isolation.mockReturnValue('switched');
    render(<App />);

    await waitFor(() => expect(isolation).toHaveBeenCalledTimes(1));
    await act(async () => { await Promise.resolve(); });
    expect(synchro).not.toHaveBeenCalled();
    expect(statut).not.toHaveBeenCalled();
    expect(screen.queryByTestId('canevas-double')).not.toBeInTheDocument();
  });

  it('cloisonnement impossible : écran d’arrêt, aucune synchronisation, bouton « Relancer »', async () => {
    isolation.mockImplementation(() => { throw new Error('Dossier illisible'); });
    const erreurs = vi.spyOn(console, 'error').mockImplementation(() => {});
    const reload = vi.fn();
    vi.stubGlobal('location', { ...window.location, reload });
    try {
      render(<App />);

      expect(await screen.findByRole('heading', { name: 'Cloisonnement du profil impossible' })).toBeInTheDocument();
      expect(synchro).not.toHaveBeenCalled();
      expect(statut).not.toHaveBeenCalled();
      fireEvent.click(screen.getByRole('button', { name: 'Relancer' }));
      expect(reload).toHaveBeenCalledTimes(1);
    } finally {
      vi.unstubAllGlobals();
      erreurs.mockRestore();
    }
  });

  it('moteur injoignable cinq fois : ni assistant ni synchronisation, l’application s’ouvre', async () => {
    vi.mocked(api.getStats).mockRejectedValue(new Error('Moteur injoignable'));
    const erreurs = vi.spyOn(console, 'error').mockImplementation(() => {});
    render(<App />);

    expect(await screen.findByTestId('canevas-double', {}, { timeout: 9000 })).toBeInTheDocument();
    expect(api.initializeAuth).toHaveBeenCalledTimes(5);
    expect(synchro).not.toHaveBeenCalled();
    expect(statut).not.toHaveBeenCalled();
    expect(screen.queryByRole('button', { name: 'Terminer la configuration' })).not.toBeInTheDocument();
    erreurs.mockRestore();
  }, 15_000);
});
