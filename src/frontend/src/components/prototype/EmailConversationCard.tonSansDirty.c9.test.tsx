/**
 * B-861 (cycle 9) : changer le ton ou la longueur souhaités éteignait le
 * bandeau « Brouillon enregistré » alors que le texte enregistré n'avait pas
 * bougé : l'utilisateur croyait devoir ré-enregistrer et déclenchait un
 * remplacement inutile chez le fournisseur.
 */
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import type { EmailMessage } from '../../services/api/email';
import { EmailMessageCanvas } from './EmailConversationCard';

function message(): EmailMessage {
  return {
    id: 'message-1', thread_id: 'thread-1', subject: 'Préparation du rendez-vous',
    from_email: 'camille@example.test', from_name: 'Camille Martin', to_emails: ['ludo@example.test'],
    cc_emails: [], bcc_emails: [], date: '2026-07-13T08:30:00+02:00', labels: ['INBOX'],
    is_read: false, is_starred: false, is_draft: false, has_attachments: false,
    snippet: 'Peux-tu confirmer ?', body_plain: 'Bonjour Ludo, peux-tu confirmer ?', body_html: null, priority: 'high',
  };
}

describe('EmailMessageCanvas - B-861, le ton et la longueur ne périment pas un brouillon enregistré', () => {
  it('le bandeau reste tant que le texte ne change pas', async () => {
    const onSaveDraft = vi.fn().mockResolvedValue({ id: 'draft-1' });
    render(
      <EmailMessageCanvas
        resource={{ status: 'ready', data: message(), error: null }}
        onRetry={vi.fn()}
        onGenerateDraft={vi.fn().mockResolvedValue('Proposition')}
        onSaveDraft={onSaveDraft}
        onOpenClassic={vi.fn()}
      />,
    );
    await waitFor(() => expect(screen.getByLabelText('Destinataire du brouillon')).toHaveValue('camille@example.test'));
    fireEvent.change(screen.getByLabelText('Corps du brouillon'), { target: { value: 'Réponse relue par Ludo' } });
    fireEvent.click(screen.getByRole('button', { name: 'Enregistrer comme brouillon' }));
    fireEvent.click(screen.getByRole('button', { name: 'Confirmer le brouillon' }));
    await screen.findByTestId('email-draft-saved');

    fireEvent.change(screen.getByLabelText('Ton du brouillon'), { target: { value: 'formal' } });
    expect(screen.getByTestId('email-draft-saved')).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText('Longueur du brouillon'), { target: { value: 'short' } });
    expect(screen.getByTestId('email-draft-saved')).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText('Corps du brouillon'), { target: { value: 'Réponse modifiée' } });
    expect(screen.queryByTestId('email-draft-saved')).toBeNull();
  });
});
