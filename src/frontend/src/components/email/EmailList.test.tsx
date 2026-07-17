import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { PrototypeExternalActionConfirmationProvider } from '../app/ExternalActionConfirmation';
import { useEmailStore } from '../../stores/emailStore';
import { EmailList } from './EmailList';

const { deleteEmailMessageMock, listEmailMessagesMock } = vi.hoisted(() => ({
  deleteEmailMessageMock: vi.fn(),
  listEmailMessagesMock: vi.fn(),
}));

vi.mock('../../services/api', async () => {
  const actual = await vi.importActual<typeof import('../../services/api')>('../../services/api');
  return {
    ...actual,
    deleteEmailMessage: deleteEmailMessageMock,
    listEmailMessages: listEmailMessagesMock,
    classifyEmail: vi.fn(),
  };
});

const listMessage = {
  id: 'message-1',
  threadId: 'thread-1',
  subject: 'Contrat à valider',
  from: 'Camille Martin <camille@example.fr>',
  date: '2026-07-15T08:00:00Z',
  labelIds: ['INBOX'],
  snippet: 'Peux-tu valider le contrat ?',
  is_read: true,
  is_starred: false,
};

function seedStore() {
  useEmailStore.setState({
    messages: [{
      id: 'message-1',
      thread_id: 'thread-1',
      subject: 'Contrat à valider',
      from_email: 'camille@example.fr',
      from_name: 'Camille Martin',
      to_emails: ['ludo@synoptia.fr'],
      date: '2026-07-15T08:00:00Z',
      labels: ['INBOX'],
      is_read: true,
      is_starred: false,
      is_draft: false,
      has_attachments: false,
      snippet: 'Peux-tu valider le contrat ?',
      body_plain: null,
      body_html: null,
      priority: 'medium',
    }],
    currentMessageId: null,
    currentLabelId: 'INBOX',
    searchQuery: '',
    refreshCounter: 0,
    needsReauth: false,
  });
}

describe('EmailList - confirmation de suppression 0.40', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    seedStore();
    listEmailMessagesMock.mockResolvedValue({ messages: [listMessage] });
    deleteEmailMessageMock.mockResolvedValue({});
  });

  it('affiche expéditeur et objet puis attend la confirmation dans la coque', async () => {
    render(
      <PrototypeExternalActionConfirmationProvider>
        <EmailList accountId="account-1" />
      </PrototypeExternalActionConfirmationProvider>,
    );

    await screen.findByText('Contrat à valider');
    fireEvent.click(screen.getByTitle('Supprimer'));

    const preview = screen.getByTestId('external-action-confirmation');
    expect(preview).toHaveTextContent('Camille Martin');
    expect(preview).toHaveTextContent('Contrat à valider');
    expect(deleteEmailMessageMock).not.toHaveBeenCalled();

    fireEvent.click(screen.getByRole('button', { name: 'Mettre à la corbeille' }));

    await waitFor(() => {
      expect(deleteEmailMessageMock).toHaveBeenCalledWith('account-1', 'message-1', false);
    });
  });

  it('conserve la suppression directe en mode classique', async () => {
    render(<EmailList accountId="account-1" />);

    await screen.findByText('Contrat à valider');
    fireEvent.click(screen.getByTitle('Supprimer'));

    await waitFor(() => {
      expect(deleteEmailMessageMock).toHaveBeenCalledWith('account-1', 'message-1', false);
    });
    expect(screen.queryByTestId('external-action-confirmation')).not.toBeInTheDocument();
  });
});

describe('BUG-122 - dossier IMAP introuvable', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    seedStore();
  });

  it('affiche l’avertissement du backend et vide la liste périmée', async () => {
    listEmailMessagesMock.mockResolvedValue({
      messages: [],
      nextPageToken: null,
      resultSizeEstimate: 0,
      warning: 'Dossier « Envoyés » introuvable sur ce serveur IMAP. Rien n’est affiché plutôt que de montrer la boîte de réception à sa place.',
    });

    render(
      <PrototypeExternalActionConfirmationProvider>
        <EmailList accountId="acc-1" />
      </PrototypeExternalActionConfirmationProvider>,
    );

    await waitFor(() =>
      expect(screen.getByText(/Dossier « Envoyés » introuvable/)).toBeInTheDocument(),
    );
    // L'ancienne liste (INBOX en cache) ne doit plus être affichée.
    expect(screen.queryByText('Contrat à valider')).not.toBeInTheDocument();
  });
});
