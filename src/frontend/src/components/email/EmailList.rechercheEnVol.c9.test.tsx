/**
 * B-897 (cycle 9, relecteur V1) : Entrée dans le champ de recherche appelait
 * loadMessages, dont la garde « chargement déjà en cours » renvoyait en
 * silence tant qu'une page suivante était en vol : la recherche était perdue,
 * sans autre déclencheur que de retaper Entrée plus tard.
 */
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { useEmailStore } from '../../stores/emailStore';
import { EmailList } from './EmailList';

const { listEmailMessagesMock } = vi.hoisted(() => ({ listEmailMessagesMock: vi.fn() }));
vi.mock('../../services/api', async () => {
  const actual = await vi.importActual<typeof import('../../services/api')>('../../services/api');
  return { ...actual, listEmailMessages: listEmailMessagesMock, deleteEmailMessage: vi.fn(), classifyEmail: vi.fn() };
});

function message(id: string, subject: string) {
  return {
    id, threadId: `thread-${id}`, subject, from: 'Camille Martin <camille@example.fr>',
    date: '2026-07-15T08:00:00Z', labelIds: ['INBOX'], snippet: 'Extrait', is_read: true, is_starred: false,
  };
}

describe('EmailList - B-897, une recherche lancée pendant une page suivante en vol part quand même', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useEmailStore.setState({
      messages: [], currentMessageId: null, currentLabelId: 'INBOX', searchQuery: '', refreshCounter: 0,
      needsReauth: false, hasMore: false, pageToken: null,
    } as never);
  });

  it('Entrée pendant « Charger la suite » déclenche la recherche', async () => {
    const suiteEnAttente = new Promise(() => {});
    listEmailMessagesMock.mockImplementation(async (_compte: string, options: { pageToken?: string; query?: string }) => {
      if (options.pageToken === 'page-2') return suiteEnAttente;
      if (options.query === 'contrat') return { messages: [message('c1', 'Contrat trouvé')] };
      return { messages: [message('m1', 'Premier message')], nextPageToken: 'page-2' };
    });

    render(<EmailList accountId="account-1" />);
    await screen.findByText('Premier message');
    fireEvent.click(screen.getByRole('button', { name: 'Charger la suite' }));
    await waitFor(() => expect(listEmailMessagesMock).toHaveBeenCalledWith('account-1', expect.objectContaining({ pageToken: 'page-2' })));

    const champ = screen.getByPlaceholderText(/Rechercher/);
    fireEvent.change(champ, { target: { value: 'contrat' } });
    fireEvent.keyDown(champ, { key: 'Enter' });

    await waitFor(() => expect(listEmailMessagesMock).toHaveBeenCalledWith('account-1', expect.objectContaining({ query: 'contrat' })));
    expect(await screen.findByText('Contrat trouvé')).toBeInTheDocument();
  });
});
