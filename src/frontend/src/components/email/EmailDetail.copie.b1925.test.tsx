/**
 * B-1925 : les destinataires en copie n'apparaissent pas dans l'en-tête,
 * alors que Répondre à tous les ajoute.
 */
import { render, screen } from '@testing-library/react';
import { beforeEach, expect, it, vi } from 'vitest';
import { useEmailStore } from '../../stores/emailStore';
import { EmailDetail } from './EmailDetail';

vi.mock('./ResponseGeneratorModal', () => ({ ResponseGeneratorModal: () => null }));
vi.mock('./EmailPriorityBadge', () => ({ EmailPriorityBadge: () => null }));

function message(cc: string[]) {
  useEmailStore.setState({
    messages: [{
      id: 'message', thread_id: 'fil', from_email: 'robot@example.fr', from_name: 'Robot',
      reply_to_emails: [], to_emails: ['moi@example.fr'], cc_emails: cc,
      subject: 'Point', body_plain: 'Bonjour', date: '2026-10-28T10:00:00Z',
      is_read: true, is_starred: false, is_draft: false, has_attachments: false,
      snippet: null, body_html: null, labels: [],
    }],
  });
}

beforeEach(() => message(['copie@example.fr', 'autre@example.fr']));

it('B-1925 : l’en-tête affiche les destinataires en copie', () => {
  render(<EmailDetail accountId="compte" messageId="message" />);
  expect(screen.getByText('À : moi@example.fr')).toBeInTheDocument();
  expect(screen.getByText('Cc : copie@example.fr, autre@example.fr')).toBeInTheDocument();
});

it('B-1925 : sans copie, la ligne Cc est absente', () => {
  message([]);
  render(<EmailDetail accountId="compte" messageId="message" />);
  expect(screen.queryByText(/^Cc :/)).not.toBeInTheDocument();
});
