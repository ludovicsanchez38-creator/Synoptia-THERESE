import { fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { beforeEach, expect, it, vi } from 'vitest';
import { useEmailStore } from '../../stores/emailStore';
import { EmailDetail } from './EmailDetail';
import { EmailCompose } from './EmailCompose';
import { PrototypeExternalActionConfirmationProvider } from '../app/ExternalActionConfirmation';

const { send, getMessage } = vi.hoisted(() => ({ send: vi.fn(), getMessage: vi.fn() }));
vi.mock('../../services/api', () => ({ sendEmail: send, getEmailMessage: getMessage }));
vi.mock('./ResponseGeneratorModal', () => ({ ResponseGeneratorModal: () => null }));
vi.mock('./EmailPriorityBadge', () => ({ EmailPriorityBadge: () => null }));

function Parcours() {
  const compose = useEmailStore((s) => s.isComposing);
  return <PrototypeExternalActionConfirmationProvider>{compose ? <EmailCompose /> : <EmailDetail accountId="compte" messageId="message" />}</PrototypeExternalActionConfirmationProvider>;
}

beforeEach(() => {
  vi.clearAllMocks();
  send.mockResolvedValue({ success: true });
  useEmailStore.getState().clearDraft();
  useEmailStore.setState({
    currentAccountId: 'compte', accounts: [{ id: 'compte', email: 'moi@example.fr', provider: 'imap', scopes: [], created_at: '', last_sync: null }],
    messages: [{ id: 'message', thread_id: 'fil', from_email: 'robot@example.fr', from_name: null, reply_to_emails: ['prospect@example.fr'],
      to_emails: ['moi@example.fr'], cc_emails: ['copie@example.fr'], subject: 'Formulaire', body_plain: 'Ma demande',
      date: '2026-10-28T10:00:00Z', is_read: true, is_starred: false, is_draft: false, has_attachments: false,
      snippet: null, body_html: null, labels: [] }],
  });
});

it('répond au Reply-To et affiche cette adresse avant confirmation, sans envoi anticipé', async () => {
  render(<Parcours />);
  fireEvent.click(screen.getByRole('button', { name: /^Répondre$/ }));
  expect(screen.getByLabelText('À')).toHaveValue('prospect@example.fr');
  fireEvent.click(screen.getByRole('button', { name: /^Envoyer$/ }));
  const carte = screen.getByTestId('external-action-confirmation');
  expect(carte).toHaveTextContent('Reply-To');
  expect(carte).toHaveTextContent('prospect@example.fr');
  expect(within(carte).getByText('À').nextElementSibling).toHaveTextContent('prospect@example.fr');
  expect(send).not.toHaveBeenCalled();
  fireEvent.click(within(carte).getByRole('button', { name: 'Confirmer et envoyer' }));
  await waitFor(() => expect(send).toHaveBeenCalledWith('compte', expect.objectContaining({ to: ['prospect@example.fr'] })));
});

it('répond à tous avec Reply-To, les copies et sans son propre compte', () => {
  render(<Parcours />);
  fireEvent.click(screen.getByRole('button', { name: 'Répondre à tous' }));
  expect(screen.getByLabelText('À')).toHaveValue('prospect@example.fr, copie@example.fr');
});

it('relit les en-têtes des anciens caches avant de permettre la réponse', async () => {
  useEmailStore.getState().updateMessage('message', { reply_to_emails: null });
  getMessage.mockResolvedValue({ reply_to_emails: ['prospect@example.fr'], body_plain: 'Ma demande' });
  render(<Parcours />);
  expect(screen.getByRole('button', { name: /^Répondre$/ })).toBeDisabled();
  await waitFor(() => expect(screen.getByRole('button', { name: /^Répondre$/ })).toBeEnabled());
  fireEvent.click(screen.getByRole('button', { name: /^Répondre$/ }));
  expect(screen.getByLabelText('À')).toHaveValue('prospect@example.fr');
});

it('sans Reply-To utilise l’expéditeur', () => {
  useEmailStore.getState().updateMessage('message', { reply_to_emails: [] });
  render(<Parcours />);
  fireEvent.click(screen.getByRole('button', { name: /^Répondre$/ }));
  expect(screen.getByLabelText('À')).toHaveValue('robot@example.fr');
});
