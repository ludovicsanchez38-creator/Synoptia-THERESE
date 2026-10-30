/**
 * Tour 11 (relecture 10) : l'avis s'affiche avec le message, la copie ne
 * reprend que le contenu, et le rechargement le relit dans `extra_data`.
 */
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { expect, it, vi } from 'vitest';
import { MessageBubble } from './MessageBubble';
import { formatMessageFromResponse } from '../../hooks/useConversationSync';

const AVIS = '*(1 ancienne préférence ou correction attend ta confirmation dans Mémoire.)*';

it('affiche l’avis hors du contenu et ne le copie pas', async () => {
  const ecrire = vi.fn().mockResolvedValue(undefined);
  Object.assign(navigator, { clipboard: { writeText: ecrire } });
  render(<MessageBubble message={{ id: 'm1', role: 'assistant', content: 'Bonjour Paul,', timestamp: new Date(), avis: [AVIS] }} />);
  expect(screen.getByRole('note')).toHaveTextContent('1 ancienne préférence ou correction attend ta confirmation dans Mémoire.');
  fireEvent.click(screen.getByTitle('Copier le message'));
  await waitFor(() => expect(ecrire).toHaveBeenCalledWith('Bonjour Paul,'));
});

it('relit les avis conservés à part au rechargement', () => {
  const message = formatMessageFromResponse({
    id: 'm1', conversation_id: 'c', role: 'assistant', content: 'Bonjour Paul,', created_at: '2026-10-30T10:00:00Z',
    extra_data: JSON.stringify({ avis: [AVIS], provenance_documents: 'sans_document' }),
  } as never);
  expect(message.content).toBe('Bonjour Paul,');
  expect(message.avis).toEqual([AVIS]);
});
