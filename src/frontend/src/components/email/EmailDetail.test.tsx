/**
 * THÉRÈSE v2 - EmailDetail Tests
 *
 * Régression BUG-102 (capov, 0.20) : le mail s'affichait vide et la réponse ne
 * citait rien, car la liste ne charge que les métadonnées (snippet) et le détail
 * n'allait jamais chercher le corps complet via getEmailMessage.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { PrototypeExternalActionConfirmationProvider } from '../app/ExternalActionConfirmation';

const mockGetEmailMessage = vi.fn();
const mockUpdateMessage = vi.fn();
const mockCreateFollowUp = vi.fn();
const mockDeleteEmailMessage = vi.fn();
const mockRemoveMessage = vi.fn();

let storeMessages: Array<Record<string, unknown>> = [];

vi.mock('../../services/api', () => ({
  getEmailMessage: (...a: unknown[]) => mockGetEmailMessage(...a),
  modifyEmailMessage: vi.fn().mockResolvedValue({}),
  deleteEmailMessage: (...a: unknown[]) => mockDeleteEmailMessage(...a),
  createFollowUp: (...a: unknown[]) => mockCreateFollowUp(...a),
}));

vi.mock('../../stores/emailStore', () => ({
  useEmailStore: () => ({
    messages: storeMessages,
    setCurrentMessage: vi.fn(),
    updateMessage: mockUpdateMessage,
    removeMessage: mockRemoveMessage,
    startComposing: vi.fn(),
    setNeedsReauth: vi.fn(),
  }),
}));

vi.mock('./ResponseGeneratorModal', () => ({ ResponseGeneratorModal: () => null }));
vi.mock('./EmailPriorityBadge', () => ({ EmailPriorityBadge: () => null }));
vi.mock('../../lib/sanitizeEmailHtml', () => ({ sanitizeEmailHtml: (s: string) => s }));

function makeMessage(overrides: Record<string, unknown> = {}) {
  return {
    id: 'm1',
    thread_id: 't1',
    subject: 'Sujet',
    from_email: 'a@b.com',
    from_name: 'A',
    to_emails: ['me@x.com'],
    date: '2026-06-09T09:00:00Z',
    snippet: 'aperçu',
    is_read: true,
    is_starred: false,
    body_plain: null,
    body_html: null,
    labels: [],
    priority: null,
    priority_score: null,
    ...overrides,
  };
}

describe("BUG-102 - corps du mail chargé à l'ouverture", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockCreateFollowUp.mockResolvedValue({});
    mockDeleteEmailMessage.mockResolvedValue({});
  });

  it('récupère le corps complet quand il manque (liste = métadonnées seules)', async () => {
    storeMessages = [makeMessage()];
    mockGetEmailMessage.mockResolvedValue({
      body_plain: 'Contenu complet',
      body_html: null,
      snippet: 'aperçu',
    });

    const { EmailDetail } = await import('./EmailDetail');
    render(<EmailDetail accountId="acc1" messageId="m1" />);

    await waitFor(() => {
      expect(mockGetEmailMessage).toHaveBeenCalledWith('acc1', 'm1');
      expect(mockUpdateMessage).toHaveBeenCalledWith(
        'm1',
        expect.objectContaining({ body_plain: 'Contenu complet' })
      );
    });
  });

  it("ne recharge pas le corps s'il est déjà présent", async () => {
    storeMessages = [makeMessage({ id: 'm2', body_plain: 'déjà chargé' })];

    const { EmailDetail } = await import('./EmailDetail');
    render(<EmailDetail accountId="acc1" messageId="m2" />);

    await new Promise((r) => setTimeout(r, 20));
    expect(mockGetEmailMessage).not.toHaveBeenCalled();
  });

  it('crée une relance explicite depuis le message', async () => {
    storeMessages = [makeMessage({ body_plain: 'déjà chargé' })];
    const { EmailDetail } = await import('./EmailDetail');
    render(<EmailDetail accountId="acc1" messageId="m1" />);

    fireEvent.click(screen.getByRole('button', { name: 'Créer une relance' }));
    fireEvent.change(screen.getByLabelText('Échéance de la relance'), { target: { value: '2026-07-20' } });
    fireEvent.change(screen.getByLabelText('Note de la relance'), { target: { value: 'Rappeler Camille' } });
    fireEvent.click(screen.getByRole('button', { name: 'Créer la relance' }));

    await waitFor(() => expect(mockCreateFollowUp).toHaveBeenCalledWith({
      email_message_id: 'm1',
      due_date: '2026-07-20T09:00:00',
      note: 'Rappeler Camille',
    }));
  });

  it('attend la confirmation 0.40 avec aperçu avant la mise à la corbeille', async () => {
    storeMessages = [makeMessage({ body_plain: 'déjà chargé' })];
    const { EmailDetail } = await import('./EmailDetail');
    render(
      <PrototypeExternalActionConfirmationProvider>
        <EmailDetail accountId="acc1" messageId="m1" />
      </PrototypeExternalActionConfirmationProvider>,
    );

    fireEvent.click(screen.getByRole('button', { name: 'Mettre à la corbeille' }));

    const preview = screen.getByTestId('external-action-confirmation');
    expect(preview).toHaveTextContent('A');
    expect(preview).toHaveTextContent('Sujet');
    expect(mockDeleteEmailMessage).not.toHaveBeenCalled();

    fireEvent.click(within(preview).getByRole('button', { name: 'Mettre à la corbeille' }));

    await waitFor(() => {
      expect(mockDeleteEmailMessage).toHaveBeenCalledWith('acc1', 'm1', false);
      expect(mockRemoveMessage).toHaveBeenCalledWith('m1');
    });
  });

  it('conserve la mise à la corbeille directe en mode classique', async () => {
    storeMessages = [makeMessage({ body_plain: 'déjà chargé' })];
    const { EmailDetail } = await import('./EmailDetail');
    render(<EmailDetail accountId="acc1" messageId="m1" />);

    fireEvent.click(screen.getByRole('button', { name: 'Mettre à la corbeille' }));

    await waitFor(() => {
      expect(mockDeleteEmailMessage).toHaveBeenCalledWith('acc1', 'm1', false);
    });
    expect(screen.queryByTestId('external-action-confirmation')).not.toBeInTheDocument();
  });
});
