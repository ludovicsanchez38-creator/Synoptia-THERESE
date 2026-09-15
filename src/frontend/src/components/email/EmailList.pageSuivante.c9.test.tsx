/**
 * B-855 (cycle 9) : « Charger la suite » concaténait la page suivante à l'état
 * du store au moment de la réponse. Changer de rubrique pendant le chargement
 * collait donc la suite de la boîte de réception sous les messages envoyés.
 */
import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { useEmailStore } from '../../stores/emailStore';
import { EmailList } from './EmailList';

const { listEmailMessagesMock } = vi.hoisted(() => ({ listEmailMessagesMock: vi.fn() }));
vi.mock('../../services/api', async () => {
  const actual = await vi.importActual<typeof import('../../services/api')>('../../services/api');
  return { ...actual, listEmailMessages: listEmailMessagesMock, deleteEmailMessage: vi.fn(), classifyEmail: vi.fn() };
});

function message(id: string, subject: string, label: string) {
  return {
    id, threadId: `thread-${id}`, subject, from: 'Camille Martin <camille@example.fr>',
    date: '2026-07-15T08:00:00Z', labelIds: [label], snippet: 'Extrait du message', is_read: true, is_starred: false,
  };
}

describe('EmailList - B-855, une page suivante arrivée après un changement de rubrique est ignorée', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useEmailStore.setState({
      messages: [], currentMessageId: null, currentLabelId: 'INBOX', searchQuery: '', refreshCounter: 0,
      needsReauth: false, hasMore: false, pageToken: null,
    } as never);
  });

  it('ne colle pas la suite de la boîte de réception sous les messages envoyés', async () => {
    let livrerLaSuite: (valeur: unknown) => void = () => {};
    const suiteEnAttente = new Promise((resolve) => { livrerLaSuite = resolve; });
    listEmailMessagesMock.mockImplementation(async (_compte: string, options: { pageToken?: string; labelIds?: string[] }) => {
      if (options.pageToken === 'page-2') return suiteEnAttente;
      if (options.labelIds?.[0] === 'SENT') return { messages: [message('s1', 'Devis envoyé', 'SENT')] };
      return { messages: [message('m1', 'Premier message', 'INBOX')], nextPageToken: 'page-2' };
    });

    render(<EmailList accountId="account-1" />);
    await screen.findByText('Premier message');

    fireEvent.click(screen.getByRole('button', { name: 'Charger la suite' }));
    await waitFor(() => expect(listEmailMessagesMock).toHaveBeenCalledWith('account-1', expect.objectContaining({ pageToken: 'page-2' })));

    act(() => { useEmailStore.setState({ currentLabelId: 'SENT', messages: [] } as never); });
    await screen.findByText('Devis envoyé');

    await act(async () => {
      livrerLaSuite({ messages: [message('m2', 'Deuxième message', 'INBOX')] });
      await Promise.resolve();
    });

    expect(screen.queryByText('Deuxième message')).toBeNull();
    expect(useEmailStore.getState().messages.map((m) => m.id)).toEqual(['s1']);
  });
});
