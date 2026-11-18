/**
 * B-1918 : le markdown de la bulle est dans prose-invert. Le thème clair
 * éclaircit alors le texte sur un fond clair. Le bandeau de code, lui,
 * reste sombre dans les deux thèmes.
 */
import { render, screen } from '@testing-library/react';
import { expect, it } from 'vitest';
import { MessageBubble } from './MessageBubble';
import type { Message } from '../../stores/chatStore';

it('B-1918 : le paragraphe suit l’encre de la charte et le bandeau de code reste sombre', () => {
  const message = {
    id: 'm1',
    role: 'assistant',
    content: 'Bonjour Paul.\n\n```python\nprint(1)\n```',
    timestamp: new Date(),
  } as Message;

  const { container } = render(<MessageBubble message={message} />);
  const prose = container.querySelector('.prose');
  expect(prose).not.toBeNull();
  expect(prose!.className.split(/\s+/)).not.toContain('prose-invert');
  expect(screen.getByText('Bonjour Paul.').className.split(/\s+/)).toContain('text-text');

  const langage = screen.getByText('python');
  expect(langage.className).toContain('text-[#B6C7DA]');
  expect(langage.parentElement?.className).toContain('bg-[#1e1e1e]');
});
