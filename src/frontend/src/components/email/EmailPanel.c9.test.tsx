/**
 * B-784 (cycle 9) : la sonde de réautorisation testait le compte capturé au
 * démarrage. Si l'utilisateur change de compte pendant l'attente, la sonde
 * doit suivre le compte courant.
 */
import { act, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

const api = vi.hoisted(() => ({
  getEmailAuthStatus: vi.fn(), listEmailLabels: vi.fn(), reauthorizeEmail: vi.fn(),
}));
vi.mock('../../services/api', () => api);
const etat = vi.hoisted(() => ({ currentAccountId: 'compte-a' as string | null }));
vi.mock('../../stores/emailStore', () => ({
  useEmailStore: () => ({
    isEmailPanelOpen: true, toggleEmailPanel: vi.fn(),
    accounts: [{ id: 'compte-a', email: 'a@example.fr', provider: 'gmail' }, { id: 'compte-b', email: 'b@example.fr', provider: 'gmail' }],
    currentAccountId: etat.currentAccountId,
    setAccounts: vi.fn(), setCurrentAccount: vi.fn(), isComposing: false, setIsComposing: vi.fn(),
    currentMessageId: null, labels: [], setLabels: vi.fn(), currentLabelId: 'INBOX', setCurrentLabel: vi.fn(),
    needsReauth: true, setNeedsReauth: vi.fn(), triggerRefresh: vi.fn(),
  }),
}));
vi.mock('./wizard', () => ({ EmailSetupWizard: () => <div /> }));
vi.mock('@tauri-apps/plugin-shell', () => ({ open: vi.fn().mockResolvedValue(undefined) }));
vi.mock('./EmailList', () => ({ EmailList: () => <div>EmailList</div> }));
vi.mock('./EmailDetail', () => ({ EmailDetail: () => <div>EmailDetail</div> }));
vi.mock('./EmailCompose', () => ({ EmailCompose: () => <div>EmailCompose</div> }));
vi.mock('dompurify', () => ({ default: { sanitize: (s: string) => s } }));

import { EmailPanel } from './EmailPanel';

describe('EmailPanel - B-784, la sonde de réautorisation suit le compte courant', () => {
  beforeEach(() => {
    vi.clearAllMocks(); vi.useFakeTimers({ shouldAdvanceTime: true });
    etat.currentAccountId = 'compte-a';
    api.getEmailAuthStatus.mockResolvedValue({ connected: true, accounts: [{ id: 'compte-a' }, { id: 'compte-b' }] });
    api.listEmailLabels.mockRejectedValue(new Error('401'));
    api.reauthorizeEmail.mockResolvedValue({ auth_url: 'https://accounts.google.test/o/oauth2' });
  });
  afterEach(() => vi.useRealTimers());

  it('interroge le compte sélectionné entre-temps, pas celui du démarrage', async () => {
    const { rerender } = render(<EmailPanel />);
    const bouton = await screen.findAllByRole('button', { name: /Reconnecter/ });
    fireEvent.click(bouton[0]);
    await act(async () => { await Promise.resolve(); await Promise.resolve(); });
    api.listEmailLabels.mockClear();

    etat.currentAccountId = 'compte-b';
    rerender(<EmailPanel />);
    await act(async () => { await vi.advanceTimersByTimeAsync(3100); });

    expect(api.listEmailLabels).toHaveBeenCalledWith('compte-b');
    expect(api.listEmailLabels).not.toHaveBeenCalledWith('compte-a');
  });
});
