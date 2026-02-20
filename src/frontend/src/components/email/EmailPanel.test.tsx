/**
 * THÉRÈSE v2 - EmailPanel Tests
 *
 * Régression BUG-037 : Croix de fermeture du wizard email inopérante.
 * La croix doit fermer le wizard même quand aucun compte n'est configuré.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';

// --- Mocks -----------------------------------------------------------------

const mockGetEmailAuthStatus = vi.fn();
const mockListEmailLabels = vi.fn();

vi.mock('../../services/api', () => ({
  getEmailAuthStatus: (...args: unknown[]) => mockGetEmailAuthStatus(...args),
  listEmailLabels: (...args: unknown[]) => mockListEmailLabels(...args),
}));

// Variables partagées pour l'email store
let mockToggleEmailPanel = vi.fn();

vi.mock('../../stores/emailStore', () => ({
  useEmailStore: () => ({
    isEmailPanelOpen: true,
    toggleEmailPanel: mockToggleEmailPanel,
    accounts: [],
    currentAccountId: null,
    setAccounts: vi.fn(),
    setCurrentAccount: vi.fn(),
    isComposing: false,
    setIsComposing: vi.fn(),
    currentMessageId: null,
    labels: [],
    setLabels: vi.fn(),
    currentLabelId: 'INBOX',
    setCurrentLabel: vi.fn(),
    needsReauth: false,
    setNeedsReauth: vi.fn(),
  }),
}));

// Mock EmailSetupWizard : expose un bouton pour simuler onCancel
vi.mock('./wizard', () => ({
  EmailSetupWizard: ({
    onCancel,
    onComplete,
  }: {
    onCancel: () => void;
    onComplete: () => void;
  }) => (
    <div data-testid="email-setup-wizard">
      <button data-testid="wizard-cancel-btn" onClick={onCancel}>
        X
      </button>
      <button data-testid="wizard-complete-btn" onClick={onComplete}>
        Terminer
      </button>
    </div>
  ),
}));

// Mock dépendances Tauri non disponibles en test
vi.mock('@tauri-apps/plugin-shell', () => ({
  open: vi.fn(),
}));

// Mock sous-composants email et dépendances tierces absentes en test
vi.mock('./EmailList', () => ({ EmailList: () => <div>EmailList</div> }));
vi.mock('./EmailDetail', () => ({ EmailDetail: () => <div>EmailDetail</div> }));
vi.mock('./EmailCompose', () => ({ EmailCompose: () => <div>EmailCompose</div> }));
vi.mock('dompurify', () => ({ default: { sanitize: (s: string) => s } }));

// ---------------------------------------------------------------------------

describe('BUG-037 - Croix de fermeture du wizard email', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockGetEmailAuthStatus.mockResolvedValue({ accounts: [] });
    mockToggleEmailPanel = vi.fn();
  });

  it('affiche le wizard quand aucun compte n\'est configuré', async () => {
    const { EmailPanel } = await import('./EmailPanel');
    render(<EmailPanel standalone />);

    await waitFor(() => {
      expect(screen.getByTestId('email-setup-wizard')).toBeTruthy();
    });
  });

  it('BUG-037 : la croix du wizard ferme le wizard (mode standalone, sans compte)', async () => {
    const { EmailPanel } = await import('./EmailPanel');
    render(<EmailPanel standalone />);

    // Attendre que le wizard s'affiche
    await waitFor(() => {
      expect(screen.getByTestId('email-setup-wizard')).toBeTruthy();
    });

    // Cliquer sur la croix du wizard
    fireEvent.click(screen.getByTestId('wizard-cancel-btn'));

    // Le wizard doit disparaître
    await waitFor(() => {
      expect(screen.queryByTestId('email-setup-wizard')).toBeNull();
    });
  });

  it('BUG-037 : après fermeture du wizard, un écran de repli s\'affiche avec "Configurer un compte"', async () => {
    const { EmailPanel } = await import('./EmailPanel');
    render(<EmailPanel standalone />);

    await waitFor(() => {
      expect(screen.getByTestId('email-setup-wizard')).toBeTruthy();
    });

    fireEvent.click(screen.getByTestId('wizard-cancel-btn'));

    // L'écran de repli doit proposer de relancer la configuration
    await waitFor(() => {
      expect(screen.getByText('Configurer un compte')).toBeTruthy();
    });
  });

  it('BUG-037 : clic sur "Configurer un compte" relance le wizard', async () => {
    const { EmailPanel } = await import('./EmailPanel');
    render(<EmailPanel standalone />);

    await waitFor(() => {
      expect(screen.getByTestId('email-setup-wizard')).toBeTruthy();
    });

    // Fermer le wizard
    fireEvent.click(screen.getByTestId('wizard-cancel-btn'));

    await waitFor(() => {
      expect(screen.getByText('Configurer un compte')).toBeTruthy();
    });

    // Relancer le wizard
    fireEvent.click(screen.getByText('Configurer un compte'));

    await waitFor(() => {
      expect(screen.getByTestId('email-setup-wizard')).toBeTruthy();
    });
  });

  it('BUG-037 : en mode modal sans compte, la croix ferme le panel entier', async () => {
    const { EmailPanel } = await import('./EmailPanel');
    render(<EmailPanel standalone={false} />);

    await waitFor(() => {
      expect(screen.getByTestId('email-setup-wizard')).toBeTruthy();
    });

    fireEvent.click(screen.getByTestId('wizard-cancel-btn'));

    // toggleEmailPanel doit avoir été appelé pour fermer le panel
    await waitFor(() => {
      expect(mockToggleEmailPanel).toHaveBeenCalled();
    });
  });
});
