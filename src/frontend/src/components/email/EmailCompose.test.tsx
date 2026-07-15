import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { PrototypeExternalActionConfirmationProvider } from '../app/ExternalActionConfirmation';
import { useEmailStore } from '../../stores/emailStore';
import { EmailCompose } from './EmailCompose';

const { sendEmailMock } = vi.hoisted(() => ({ sendEmailMock: vi.fn() }));

vi.mock('../../services/api', async () => {
  const actual = await vi.importActual<typeof import('../../services/api')>('../../services/api');
  return {
    ...actual,
    sendEmail: sendEmailMock,
    createDraft: vi.fn(),
  };
});

function seedDraft() {
  useEmailStore.setState({
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

describe('EmailCompose - confirmation 0.40', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    sendEmailMock.mockResolvedValue({ success: true });
    seedDraft();
  });

  it('affiche l’aperçu et attend la confirmation dans la coque prototype', async () => {
    render(
      <PrototypeExternalActionConfirmationProvider>
        <EmailCompose />
      </PrototypeExternalActionConfirmationProvider>,
    );

    fireEvent.click(screen.getByRole('button', { name: 'Envoyer' }));

    const preview = screen.getByTestId('external-action-confirmation');
    expect(preview).toHaveTextContent('client@example.fr');
    expect(preview).toHaveTextContent('Point de suivi');
    expect(preview).toHaveTextContent('Bonjour, voici le point demandé.');
    expect(sendEmailMock).not.toHaveBeenCalled();

    fireEvent.click(screen.getByRole('button', { name: 'Confirmer et envoyer' }));

    await waitFor(() => {
      expect(sendEmailMock).toHaveBeenCalledWith('account-1', {
        to: ['client@example.fr'],
        cc: undefined,
        bcc: undefined,
        subject: 'Point de suivi',
        body: 'Bonjour, voici le point demandé.',
        html: false,
      });
    });
  });

  it('conserve l’envoi direct en mode classique', async () => {
    render(<EmailCompose />);

    fireEvent.click(screen.getByRole('button', { name: 'Envoyer' }));

    await waitFor(() => expect(sendEmailMock).toHaveBeenCalledTimes(1));
    expect(screen.queryByTestId('external-action-confirmation')).not.toBeInTheDocument();
  });
});
