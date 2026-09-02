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

  it('quand la page est saturée, ne présente pas le compteur comme celui de toute la boîte', () => {
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
            listeIncomplete: true,
          },
        }}
        onRetry={vi.fn()}
        onOpenMessage={vi.fn()}
        onOpenClassic={vi.fn()}
      />,
    );
    expect(screen.getByText(/parmi les 30 plus récents/)).toBeInTheDocument();
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

  /**
   * B-060 (reliquat frontend). L'ecran garde depuis toujours l'identifiant
   * rendu par le premier enregistrement, et ne s'en sert que pour peindre un
   * bandeau vert. Chaque correction re-enregistree creait donc un brouillon
   * de PLUS chez le fournisseur, sans que rien ne le dise.
   *
   * Deux exigences, car la premiere seule ne suffit pas : l'identifiant doit
   * etre transmis au deuxieme enregistrement, et celui rendu par ce
   * deuxieme doit prendre la place du premier (chez IMAP, remplacer un
   * brouillon le re-APPEND sous un UID neuf : reutiliser l'ancien
   * ressusciterait le doublon des le troisieme enregistrement).
   */
  it('re-enregistrer transmet l’identifiant du brouillon deja pose, puis le suivant', async () => {
    const onSaveDraft = vi
      .fn()
      .mockResolvedValueOnce({ id: 'draft-1' })
      .mockResolvedValueOnce({ id: 'draft-9' })
      .mockResolvedValue({ id: 'draft-9' });
    render(
      <EmailMessageCanvas
        resource={{ status: 'ready', data: message(), error: null }}
        onRetry={vi.fn()}
        onGenerateDraft={vi.fn()}
        onSaveDraft={onSaveDraft}
        onOpenClassic={vi.fn()}
      />,
    );

    const body = await screen.findByLabelText('Corps du brouillon');
    const enregistrer = async () => {
      fireEvent.click(screen.getByRole('button', { name: 'Enregistrer comme brouillon' }));
      fireEvent.click(screen.getByRole('button', { name: 'Confirmer le brouillon' }));
    };

    fireEvent.change(body, { target: { value: 'Premiere version' } });
    await enregistrer();
    await waitFor(() => expect(onSaveDraft).toHaveBeenCalledTimes(1));
    // Rien a remplacer encore : c'est bien une creation.
    expect(onSaveDraft.mock.calls[0][1]).toBeUndefined();

    fireEvent.change(body, { target: { value: 'Version corrigee' } });
    await enregistrer();
    await waitFor(() => expect(onSaveDraft).toHaveBeenCalledTimes(2));
    expect(onSaveDraft.mock.calls[1][1]).toBe('draft-1');

    fireEvent.change(body, { target: { value: 'Troisieme jet' } });
    await enregistrer();
    await waitFor(() => expect(onSaveDraft).toHaveBeenCalledTimes(3));
    expect(onSaveDraft.mock.calls[2][1]).toBe('draft-9');
  });

  /**
   * La frontiere du correctif B-060, epinglee pour qu'elle reste une decision.
   *
   * Re-ouvrir le meme message (« Reessayer ») rend un nouvel objet `resource` :
   * l'effet de reinitialisation VIDE le composeur. L'identifiant du brouillon
   * part avec lui, a dessein - garder le lien ferait ecraser le brouillon
   * enregistre par un texte qui n'a plus rien a voir. Le prochain
   * enregistrement est donc bien une creation.
   */
  it('re-ouvrir le message vide le composeur, donc repart sur une création', async () => {
    const onSaveDraft = vi.fn().mockResolvedValue({ id: 'draft-1' });
    const props = {
      onRetry: vi.fn(),
      onGenerateDraft: vi.fn(),
      onSaveDraft,
      onOpenClassic: vi.fn(),
    };
    const { rerender } = render(
      <EmailMessageCanvas resource={{ status: 'ready', data: message(), error: null }} {...props} />,
    );

    const body = await screen.findByLabelText('Corps du brouillon');
    fireEvent.change(body, { target: { value: 'Premiere version' } });
    fireEvent.click(screen.getByRole('button', { name: 'Enregistrer comme brouillon' }));
    fireEvent.click(screen.getByRole('button', { name: 'Confirmer le brouillon' }));
    await waitFor(() => expect(onSaveDraft).toHaveBeenCalledTimes(1));

    // Nouvel objet `resource`, meme message : ce que produit openMessage.
    rerender(
      <EmailMessageCanvas resource={{ status: 'ready', data: message(), error: null }} {...props} />,
    );

    const rouvert = screen.getByLabelText('Corps du brouillon');
    expect(rouvert).toHaveValue('');

    fireEvent.change(rouvert, { target: { value: 'Tout autre reponse' } });
    fireEvent.click(screen.getByRole('button', { name: 'Enregistrer comme brouillon' }));
    fireEvent.click(screen.getByRole('button', { name: 'Confirmer le brouillon' }));
    await waitFor(() => expect(onSaveDraft).toHaveBeenCalledTimes(2));
    expect(onSaveDraft.mock.calls[1][1]).toBeUndefined();
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
