/**
 * B-495 : transférer ou répondre à un message HTML seul (body_plain vide)
 * envoyait un corps vide, ou citait l'extrait tronqué. Le texte se dérive
 * désormais du HTML quand le texte brut manque.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { fireEvent, render, screen } from '@testing-library/react';
import { PrototypeExternalActionConfirmationProvider } from '../app/ExternalActionConfirmation';

const mockStartComposing = vi.fn();
let storeMessages: Array<Record<string, unknown>> = [];

vi.mock('../../services/api', () => ({
  getEmailMessage: vi.fn(),
  modifyEmailMessage: vi.fn().mockResolvedValue({}),
  deleteEmailMessage: vi.fn(),
  createFollowUp: vi.fn(),
}));
vi.mock('../../stores/emailStore', () => ({
  useEmailStore: () => ({
    messages: storeMessages,
    setCurrentMessage: vi.fn(),
    updateMessage: vi.fn(),
    removeMessage: vi.fn(),
    startComposing: (...a: unknown[]) => mockStartComposing(...a),
    setNeedsReauth: vi.fn(),
  }),
}));
vi.mock('./ResponseGeneratorModal', () => ({ ResponseGeneratorModal: () => null }));
vi.mock('./EmailPriorityBadge', () => ({ EmailPriorityBadge: () => null }));

const message = {
  id: 'h1', thread_id: 't1', subject: 'Devis', from_email: 'a@b.com', from_name: 'A',
  to_emails: ['me@x.com'], date: '2026-06-09T09:00:00Z', snippet: 'Bonjour Ma…',
  is_read: true, is_starred: false, body_plain: '',
  body_html: '<style>p{color:red}</style><p>Bonjour <b>Marie</b>,</p><p>voici le devis.</p>',
  labels: [], priority: null, priority_score: null,
};

describe('EmailDetail - message HTML seul (B-495)', () => {
  beforeEach(() => { vi.clearAllMocks(); storeMessages = [message]; });

  it('transfère le texte dérivé du HTML, sans le CSS', async () => {
    const { EmailDetail } = await import('./EmailDetail');
    render(<PrototypeExternalActionConfirmationProvider><EmailDetail accountId="acc1" messageId="h1" /></PrototypeExternalActionConfirmationProvider>);
    fireEvent.click(screen.getByRole('button', { name: /Transférer/ }));
    const corps = String(mockStartComposing.mock.calls[0]?.[2] ?? '');
    expect(corps).toContain('Bonjour Marie,');
    expect(corps).toContain('voici le devis.');
    expect(corps).not.toContain('color:red');
  });

  it('répond en citant le texte dérivé du HTML plutôt que l’extrait tronqué', async () => {
    const { EmailDetail } = await import('./EmailDetail');
    render(<PrototypeExternalActionConfirmationProvider><EmailDetail accountId="acc1" messageId="h1" /></PrototypeExternalActionConfirmationProvider>);
    fireEvent.click(screen.getByRole('button', { name: /^Répondre$/ }));
    const corps = String(mockStartComposing.mock.calls[0]?.[2] ?? '');
    expect(corps).toContain('> voici le devis.');
    expect(corps).not.toContain('Bonjour Ma…');
  });
});
