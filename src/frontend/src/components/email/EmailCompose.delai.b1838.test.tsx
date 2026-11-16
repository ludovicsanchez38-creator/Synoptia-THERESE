/**
 * B-1838 : le délai de 35 s courait à côté de sendEmail. S'il gagnait,
 * l'envoi continuait et un second clic partait encore. S'il perdait,
 * son rejet n'avait plus personne pour l'attraper.
 */
import { act, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { useEmailStore } from '../../stores/emailStore';
import { EmailCompose } from './EmailCompose';

const { sendEmailMock } = vi.hoisted(() => ({ sendEmailMock: vi.fn() }));

vi.mock('../../services/api', async () => {
  const actual = await vi.importActual<typeof import('../../services/api')>('../../services/api');
  return { ...actual, sendEmail: sendEmailMock, createDraft: vi.fn() };
});

function seedDraft() {
  useEmailStore.setState({
    accounts: [
      { id: 'account-1', email: 'moi@cabinet.fr', provider: 'gmail', scopes: [], created_at: '', last_sync: null },
    ],
    currentAccountId: 'account-1',
    isComposing: true,
    draftRecipients: ['client@example.fr'],
    draftCc: [],
    draftBcc: [],
    draftSubject: 'Point de suivi',
    draftBody: 'Bonjour, voici le point demandé.',
    draftIsHtml: false,
  });
}

describe('B-1838 : le délai coupe vraiment l’envoi', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.clearAllMocks();
    seedDraft();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('abandonne l’appel encore en cours au bout de 35 s et garde le brouillon', async () => {
    let signal: AbortSignal | undefined;
    sendEmailMock.mockImplementation((_compte: string, _email: unknown, recu?: AbortSignal) => {
      signal = recu;
      return new Promise((_resolve, reject) => {
        recu?.addEventListener('abort', () => reject(new DOMException('TIMEOUT', 'AbortError')), { once: true });
      });
    });

    render(<EmailCompose />);
    fireEvent.click(screen.getByRole('button', { name: 'Envoyer' }));
    expect(sendEmailMock).toHaveBeenCalledTimes(1);

    await act(async () => { await vi.advanceTimersByTimeAsync(35_000); });

    expect(signal?.aborted).toBe(true);
    expect(screen.getByRole('alert')).toHaveTextContent("L'envoi a expiré");
    expect(useEmailStore.getState().isComposing).toBe(true);
    expect(useEmailStore.getState().draftSubject).toBe('Point de suivi');
  });

  it('désarme le délai quand l’envoi finit avant lui', async () => {
    sendEmailMock.mockResolvedValue({ success: true });

    render(<EmailCompose />);
    fireEvent.click(screen.getByRole('button', { name: 'Envoyer' }));
    await act(async () => {
      await Promise.resolve();
      await Promise.resolve();
      await Promise.resolve();
    });

    expect(useEmailStore.getState().isComposing).toBe(false);
    expect(vi.getTimerCount()).toBe(0);
  });
});
