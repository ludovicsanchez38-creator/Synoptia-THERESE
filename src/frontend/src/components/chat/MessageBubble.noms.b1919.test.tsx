/**
 * B-1919 : « Enregistrer l'image » et « Copier le message » n'ont qu'un title.
 * Le nom accessible doit être un aria-label, comme « Enregistrer comme commande ».
 */
import { render, screen } from '@testing-library/react';
import { expect, it } from 'vitest';
import { MessageBubble } from './MessageBubble';
import type { Message } from '../../stores/chatStore';

function message(over: Partial<Message>): Message {
  return {
    id: 'm1',
    role: 'assistant',
    content: 'Bonjour',
    timestamp: new Date(),
    ...over,
  } as Message;
}

it("B-1919 : Enregistrer l'image et Copier l'image ont un aria-label", () => {
  render(<MessageBubble message={message({ imageId: 'img-1', content: '' })} />);
  expect(screen.getByTitle("Enregistrer l'image")).toHaveAttribute('aria-label', "Enregistrer l'image");
  expect(screen.getByTitle("Copier l'image")).toHaveAttribute('aria-label', "Copier l'image");
});

it('B-1919 : Copier le message a un aria-label', () => {
  render(<MessageBubble message={message({ content: 'Bonjour' })} />);
  expect(screen.getByTitle('Copier le message')).toHaveAttribute('aria-label', 'Copier le message');
});
