/**
 * B-1924 : le bouton d'étoile n'a ni texte ni aria-label.
 * La corbeille, à côté, se nomme « Mettre à la corbeille ».
 */
import { fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, expect, it, vi } from 'vitest';
import { useEmailStore } from '../../stores/emailStore';
import { EmailDetail } from './EmailDetail';

vi.mock('../../services/api', async () => {
  const reel = await vi.importActual<typeof import('../../services/api')>('../../services/api');
  return { ...reel, modifyEmailMessage: vi.fn().mockResolvedValue({}) };
});
vi.mock('./ResponseGeneratorModal', () => ({ ResponseGeneratorModal: () => null }));
vi.mock('./EmailPriorityBadge', () => ({ EmailPriorityBadge: () => null }));

beforeEach(() => {
  useEmailStore.setState({
    messages: [{
      id: 'message', thread_id: 'fil', from_email: 'robot@example.fr', from_name: 'Robot',
      reply_to_emails: [], to_emails: ['moi@example.fr'], cc_emails: [],
      subject: 'Point', body_plain: 'Bonjour', date: '2026-10-28T10:00:00Z',
      is_read: true, is_starred: false, is_draft: false, has_attachments: false,
      snippet: null, body_html: null, labels: [],
    }],
  });
});

it('B-1924 : l’étoile se nomme, puis dit qu’on peut la retirer', async () => {
  render(<EmailDetail accountId="compte" messageId="message" />);
  fireEvent.click(screen.getByRole('button', { name: 'Marquer d’une étoile' }));
  expect(await screen.findByRole('button', { name: 'Retirer l’étoile' })).toBeInTheDocument();
});
