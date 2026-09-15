/**
 * B-774 (cycle 9) : à la suppression, la liste ne reconnaissait pas un 401
 * comme une session expirée (le détail, lui, le faisait) : l'utilisateur voyait
 * un échec générique au lieu de l'invitation à se reconnecter.
 */
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { useEmailStore } from '../../stores/emailStore';
import { EmailList } from './EmailList';

const { deleteEmailMessageMock, listEmailMessagesMock } = vi.hoisted(() => ({
  deleteEmailMessageMock: vi.fn(), listEmailMessagesMock: vi.fn(),
}));
vi.mock('../../services/api', async () => {
  const actual = await vi.importActual<typeof import('../../services/api')>('../../services/api');
  return { ...actual, deleteEmailMessage: deleteEmailMessageMock, listEmailMessages: listEmailMessagesMock, classifyEmail: vi.fn() };
});

describe('EmailList - B-774, un 401 à la suppression demande la reconnexion', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useEmailStore.setState({
      messages: [{
        id: 'message-1', thread_id: 'thread-1', subject: 'Contrat à valider', from_email: 'camille@example.fr',
        from_name: 'Camille Martin', to_emails: ['ludo@synoptia.fr'], date: '2026-07-15T08:00:00Z', labels: ['INBOX'],
        is_read: true, is_starred: false, is_draft: false, has_attachments: false, snippet: 'Peux-tu valider ?',
        body_plain: null, body_html: null, priority: 'medium',
      }],
      currentMessageId: null, currentLabelId: 'INBOX', searchQuery: '', refreshCounter: 0, needsReauth: false, hasMore: false, pageToken: null,
    } as never);
    listEmailMessagesMock.mockResolvedValue({ messages: [{ id: 'message-1', threadId: 'thread-1', subject: 'Contrat à valider', from: 'Camille Martin <camille@example.fr>', date: '2026-07-15T08:00:00Z', labelIds: ['INBOX'], snippet: 'Peux-tu valider ?', is_read: true, is_starred: false }] });
    deleteEmailMessageMock.mockRejectedValue(new Error('HTTP 401: Unauthorized'));
  });

  it('affiche « Connexion Gmail expirée » et arme la reconnexion', async () => {
    render(<EmailList accountId="account-1" />);
    await screen.findByText('Contrat à valider');
    fireEvent.click(screen.getByTitle('Supprimer'));

    await waitFor(() => expect(deleteEmailMessageMock).toHaveBeenCalled());
    expect(await screen.findByText(/Connexion Gmail expirée/)).toBeInTheDocument();
    expect(useEmailStore.getState().needsReauth).toBe(true);
  });
});
