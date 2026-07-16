import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import type { EmailMessage } from '../../services/api/email';
import { EmailInboxCard, EmailMessageCanvas } from './EmailConversationCard';

function message(overrides: Partial<EmailMessage> = {}): EmailMessage {
  return {
    id: 'message-1',
    thread_id: 'thread-1',
    subject: 'Préparation du rendez-vous',
    from_email: 'camille@example.test',
    from_name: 'Camille Martin',
    to_emails: ['ludo@example.test'],
    cc_emails: [],
    bcc_emails: [],
    date: '2026-07-13T08:30:00+02:00',
    labels: ['INBOX', 'UNREAD'],
    is_read: false,
    is_starred: false,
    is_draft: false,
    has_attachments: false,
    snippet: 'Peux-tu confirmer les éléments à préparer ?',
    body_plain: 'Bonjour Ludo, peux-tu confirmer les éléments à préparer ?',
    body_html: null,
    priority: 'high',
    ...overrides,
  };
}

describe('EmailInboxCard', () => {
  it('affiche les messages réels et ouvre le message sélectionné', () => {
    const onOpenMessage = vi.fn();
    render(
      <EmailInboxCard
        resource={{
          status: 'ready',
          error: null,
          data: {
            accounts: [],
            currentAccount: {
              id: 'account-1', email: 'ludo@example.test', provider: 'imap', scopes: [],
              created_at: '2026-07-13', last_sync: null,
            },
            messages: [message()],
            failedMessages: 0,
          },
        }}
        onRetry={vi.fn()}
        onOpenMessage={onOpenMessage}
        onOpenClassic={vi.fn()}
      />,
    );

    expect(screen.getByText('Camille Martin')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Non lu\. Camille Martin/ })).toBeInTheDocument();
    expect(screen.getByText('Prioritaire')).toBeInTheDocument();
    fireEvent.click(screen.getByText('Préparation du rendez-vous'));
    expect(onOpenMessage).toHaveBeenCalledWith('message-1');
  });

  it('distingue clairement l’absence de compte connecté', () => {
    render(
      <EmailInboxCard
        resource={{
          status: 'ready', error: null,
          data: { accounts: [], currentAccount: null, messages: [], failedMessages: 0 },
        }}
        onRetry={vi.fn()}
        onOpenMessage={vi.fn()}
        onOpenClassic={vi.fn()}
      />,
    );

    expect(screen.getByTestId('email-no-account')).toHaveTextContent('Aucun compte email connecté');
  });
});

describe('EmailMessageCanvas', () => {
  it('génère un texte modifiable et exige une confirmation avant de créer le brouillon', async () => {
    const onGenerateDraft = vi.fn().mockResolvedValue('Proposition générée');
    const onSaveDraft = vi.fn().mockResolvedValue({ id: 'draft-1' });
    render(
      <EmailMessageCanvas
        resource={{ status: 'ready', data: message(), error: null }}
        onRetry={vi.fn()}
        onGenerateDraft={onGenerateDraft}
        onSaveDraft={onSaveDraft}
        onOpenClassic={vi.fn()}
      />,
    );

    await waitFor(() => expect(screen.getByLabelText('Destinataire du brouillon')).toHaveValue('camille@example.test'));
    fireEvent.click(screen.getByRole('button', { name: 'Générer une proposition' }));
    await waitFor(() => expect(screen.getByLabelText('Corps du brouillon')).toHaveValue('Proposition générée'));

    fireEvent.change(screen.getByLabelText('Corps du brouillon'), { target: { value: 'Réponse relue par Ludo' } });
    fireEvent.click(screen.getByRole('button', { name: 'Enregistrer comme brouillon' }));

    expect(screen.getByTestId('email-draft-confirmation')).toBeInTheDocument();
    expect(onSaveDraft).not.toHaveBeenCalled();

    fireEvent.click(screen.getByRole('button', { name: 'Confirmer le brouillon' }));
    await waitFor(() => expect(onSaveDraft).toHaveBeenCalledWith({
      to: ['camille@example.test'],
      subject: 'Re: Préparation du rendez-vous',
      body: 'Réponse relue par Ludo',
      html: false,
    }));
    expect(await screen.findByTestId('email-draft-saved')).toHaveTextContent('Aucun message n’a été envoyé');
  });

  it('confirme le remplacement IA, permet de l’annuler et invalide tout faux statut enregistré', async () => {
    const onGenerateDraft = vi.fn().mockResolvedValue('Proposition IA');
    const onSaveDraft = vi.fn().mockResolvedValue({ id: 'draft-2' });
    render(
      <EmailMessageCanvas
        resource={{ status: 'ready', data: message(), error: null }}
        onRetry={vi.fn()}
        onGenerateDraft={onGenerateDraft}
        onSaveDraft={onSaveDraft}
        onOpenClassic={vi.fn()}
      />,
    );

    const body = await screen.findByLabelText('Corps du brouillon');
    fireEvent.change(body, { target: { value: 'Mon texte manuel' } });
    fireEvent.click(screen.getByRole('button', { name: 'Générer une proposition' }));
    expect(onGenerateDraft).not.toHaveBeenCalled();
    expect(screen.getByText(/Remplacer le brouillon actuel/)).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Remplacer' }));
    await waitFor(() => expect(body).toHaveValue('Proposition IA'));
    fireEvent.click(screen.getByRole('button', { name: 'Annuler le remplacement IA' }));
    expect(body).toHaveValue('Mon texte manuel');

    fireEvent.click(screen.getByRole('button', { name: 'Enregistrer comme brouillon' }));
    fireEvent.click(screen.getByRole('button', { name: 'Confirmer le brouillon' }));
    expect(await screen.findByTestId('email-draft-saved')).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText('Objet du brouillon'), { target: { value: 'Objet modifié' } });
    expect(screen.queryByTestId('email-draft-saved')).not.toBeInTheDocument();
  });

  it('lie l’erreur au premier champ fautif et le focalise', async () => {
    render(
      <EmailMessageCanvas
        resource={{ status: 'ready', data: message(), error: null }}
        onRetry={vi.fn()}
        onGenerateDraft={vi.fn()}
        onSaveDraft={vi.fn()}
        onOpenClassic={vi.fn()}
      />,
    );
    const recipient = await screen.findByLabelText('Destinataire du brouillon');
    fireEvent.change(recipient, { target: { value: 'invalide' } });
    fireEvent.click(screen.getByRole('button', { name: 'Enregistrer comme brouillon' }));
    await waitFor(() => expect(recipient).toHaveFocus());
    expect(recipient).toHaveAttribute('aria-invalid', 'true');
    expect(recipient).toHaveAttribute('aria-describedby', 'email-draft-error');
  });
});
