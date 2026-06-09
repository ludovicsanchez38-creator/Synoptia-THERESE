/**
 * THÉRÈSE v2 - EmailDetail Tests
 *
 * Régression BUG-102 (capov, 0.20) : le mail s'affichait vide et la réponse ne
 * citait rien, car la liste ne charge que les métadonnées (snippet) et le détail
 * n'allait jamais chercher le corps complet via getEmailMessage.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, waitFor } from '@testing-library/react';

const mockGetEmailMessage = vi.fn();
const mockUpdateMessage = vi.fn();

let storeMessages: Array<Record<string, unknown>> = [];

vi.mock('../../services/api', () => ({
  getEmailMessage: (...a: unknown[]) => mockGetEmailMessage(...a),
  modifyEmailMessage: vi.fn().mockResolvedValue({}),
  deleteEmailMessage: vi.fn().mockResolvedValue({}),
}));

vi.mock('../../stores/emailStore', () => ({
  useEmailStore: () => ({
    messages: storeMessages,
    setCurrentMessage: vi.fn(),
    updateMessage: mockUpdateMessage,
    removeMessage: vi.fn(),
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
});
