/**
 * B-826 (cycle 9) : quand le premier chargement échouait et qu'une reprise
 * automatique était programmée, le `finally` coupait l'état de chargement :
 * « Aucun message » s'affichait entre deux tentatives.
 */
import { render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { useEmailStore } from '../../stores/emailStore';
import { EmailList } from './EmailList';

const { listEmailMessagesMock } = vi.hoisted(() => ({ listEmailMessagesMock: vi.fn() }));
vi.mock('../../services/api', async () => {
  const actual = await vi.importActual<typeof import('../../services/api')>('../../services/api');
  return { ...actual, listEmailMessages: listEmailMessagesMock, deleteEmailMessage: vi.fn(), classifyEmail: vi.fn() };
});

describe('EmailList - B-826, une reprise en cours ne dit pas « Aucun message »', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useEmailStore.setState({ messages: [], currentMessageId: null, currentLabelId: 'INBOX', searchQuery: '', refreshCounter: 0, needsReauth: false, hasMore: false, pageToken: null } as never);
    listEmailMessagesMock.mockRejectedValueOnce(new Error('Failed to fetch')).mockResolvedValue({ messages: [] });
  });

  it('garde l’indicateur de chargement tant qu’une tentative est programmée', async () => {
    render(<EmailList accountId="account-1" />);
    await waitFor(() => expect(listEmailMessagesMock).toHaveBeenCalledTimes(1));
    await new Promise((r) => setTimeout(r, 200));
    expect(screen.queryByText('Aucun message')).toBeNull();
  });
});
