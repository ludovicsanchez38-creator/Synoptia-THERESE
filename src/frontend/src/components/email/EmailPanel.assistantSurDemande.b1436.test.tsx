/**
 * B-1436 (recette P-146, lot 1, KO-3 ; décision du 25/09) : sans boîte
 * branchée, ouvrir l'écran Email lançait l'assistant de connexion par-dessus ;
 * son voile cachait « Retour » et il fallait deux Échap pour revenir.
 * Dans l'écran intégré, l'assistant ne s'ouvre plus que sur demande
 * (« Brancher mes mails ») ; sinon l'écran propose « Configurer un compte ».
 */
import { render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { demanderLaConnexionEmail } from '../../lib/demandeDeConnexionEmail';

vi.mock('../../services/api', () => ({
  getEmailAuthStatus: vi.fn().mockResolvedValue({ accounts: [] }),
  listEmailLabels: vi.fn(),
}));
vi.mock('../../stores/emailStore', () => ({
  useEmailStore: () => ({
    isEmailPanelOpen: true, toggleEmailPanel: vi.fn(), accounts: [], currentAccountId: null,
    setAccounts: vi.fn(), setCurrentAccount: vi.fn(), isComposing: false, setIsComposing: vi.fn(),
    currentMessageId: null, labels: [], setLabels: vi.fn(), currentLabelId: 'INBOX', setCurrentLabel: vi.fn(),
    needsReauth: false, setNeedsReauth: vi.fn(), triggerRefresh: vi.fn(),
  }),
}));
vi.mock('./wizard', () => ({ EmailSetupWizard: () => <div data-testid="email-setup-wizard" /> }));
vi.mock('@tauri-apps/plugin-shell', () => ({ open: vi.fn() }));
vi.mock('./EmailList', () => ({ EmailList: () => <div>EmailList</div> }));
vi.mock('./EmailDetail', () => ({ EmailDetail: () => <div>EmailDetail</div> }));
vi.mock('./EmailCompose', () => ({ EmailCompose: () => <div>EmailCompose</div> }));

import { EmailPanel } from './EmailPanel';

describe('B-1436 : l’assistant e-mail ne s’ouvre que sur demande', () => {
  beforeEach(() => vi.clearAllMocks());

  it('ouvrir l’écran Email sans boîte propose « Configurer un compte », sans assistant par-dessus', async () => {
    render(<EmailPanel standalone />);
    expect(await screen.findByText('Configurer un compte')).toBeInTheDocument();
    expect(screen.queryByTestId('email-setup-wizard')).toBeNull();
  });

  it('« Brancher mes mails » ouvre l’assistant, une seule fois', async () => {
    demanderLaConnexionEmail();
    const { unmount } = render(<EmailPanel standalone />);
    await waitFor(() => expect(screen.getByTestId('email-setup-wizard')).toBeInTheDocument());
    unmount();
    render(<EmailPanel standalone />);
    expect(await screen.findByText('Configurer un compte')).toBeInTheDocument();
  });
});
