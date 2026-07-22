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
// BUG-151 : la VRAIE sanitisation est nécessaire (blocage des images
// distantes + opt-in allowRemoteImages) - l'ancien mock identité masquait
// tout le comportement testé ici.
vi.mock('../../lib/sanitizeEmailHtml', async (importOriginal) => await importOriginal());

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

// BUG-151 (Capov) : les images distantes étaient remplacées par des cadres
// vides SANS aucun moyen de les afficher. Opt-in par message : bandeau
// « Afficher les images » qui re-sanitise avec allowRemoteImages.
describe('BUG-151 - images distantes opt-in', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  const HTML_AVEC_IMAGE = '<p>Bonjour</p><img src="https://cdn.example.com/logo.png" alt="Logo">';

  it('bloque les images par défaut et propose de les afficher', async () => {
    storeMessages = [makeMessage({ id: 'm-img', body_html: HTML_AVEC_IMAGE })];

    const { EmailDetail } = await import('./EmailDetail');
    const { container } = render(<EmailDetail accountId="acc1" messageId="m-img" />);

    expect(container.querySelector('img[src^="https:"]')).toBeNull();
    expect(screen.getByRole('button', { name: /Afficher les images/ })).toBeInTheDocument();
  });

  it('affiche les images distantes après le clic', async () => {
    storeMessages = [makeMessage({ id: 'm-img2', body_html: HTML_AVEC_IMAGE })];

    const { EmailDetail } = await import('./EmailDetail');
    const { container } = render(<EmailDetail accountId="acc1" messageId="m-img2" />);

    fireEvent.click(screen.getByRole('button', { name: /Afficher les images/ }));

    await waitFor(() => {
      expect(container.querySelector('img[src="https://cdn.example.com/logo.png"]')).not.toBeNull();
    });
    expect(screen.queryByRole('button', { name: /Afficher les images/ })).not.toBeInTheDocument();
  });

  it("ne montre pas le bandeau quand le mail n'a pas d'image distante", async () => {
    storeMessages = [makeMessage({ id: 'm-sans', body_html: '<p>Texte pur</p>' })];

    const { EmailDetail } = await import('./EmailDetail');
    render(<EmailDetail accountId="acc1" messageId="m-sans" />);

    expect(screen.queryByRole('button', { name: /Afficher les images/ })).not.toBeInTheDocument();
  });

  it("F3 revue : l'opt-in du mail A ne fuit pas sur le mail B (état dérivé du messageId)", async () => {
    storeMessages = [
      makeMessage({ id: 'm-a', body_html: HTML_AVEC_IMAGE }),
      makeMessage({ id: 'm-b', body_html: '<p>B</p><img src="https://tracker.example.com/b.gif" alt="b">' }),
    ];

    const { EmailDetail } = await import('./EmailDetail');
    const { container, rerender } = render(<EmailDetail accountId="acc1" messageId="m-a" />);
    fireEvent.click(screen.getByRole('button', { name: /Afficher les images/ }));
    await waitFor(() => {
      expect(container.querySelector('img[src^="https:"]')).not.toBeNull();
    });

    // Changement de message SANS remontage : le PREMIER rendu de B doit déjà
    // être bloqué (un reset en effet post-commit laissait partir le pixel).
    rerender(<EmailDetail accountId="acc1" messageId="m-b" />);

    expect(container.querySelector('img[src^="https:"]')).toBeNull();
    expect(screen.getByRole('button', { name: /Afficher les images/ })).toBeInTheDocument();
  });
});
