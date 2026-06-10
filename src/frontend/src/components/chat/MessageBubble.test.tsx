/**
 * US-010 : tableaux markdown rendus (remark-gfm) + memo réparé.
 *
 * Avant : react-markdown sans remark-gfm ne parse PAS la syntaxe de tableau
 * GFM (| a | b |) → les tableaux arrivaient en texte brut. Et le memo de
 * MessageBubble était cassé par la prop onSaveAsCommand recréée à chaque
 * rendu (closure inline dans MessageList).
 */
import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { MessageBubble, arePropsEqual } from './MessageBubble';
import type { Message } from '../../stores/chatStore';

function makeMessage(over: Partial<Message> = {}): Message {
  return {
    id: 'm1',
    role: 'assistant',
    content: 'Bonjour',
    timestamp: new Date(),
    ...over,
  } as Message;
}

describe('MessageBubble - tableaux GFM (US-010)', () => {
  it('rend un tableau markdown GFM en vrai <table>', () => {
    const md = [
      '| Offre | Prix |',
      '| --- | --- |',
      '| FORGER | 490 |',
      '| PROPULSER | 2490 |',
    ].join('\n');
    render(<MessageBubble message={makeMessage({ content: md })} />);

    const table = screen.getByRole('table');
    expect(table).toBeTruthy();
    expect(screen.getByText('FORGER')).toBeTruthy();
    expect(screen.getAllByRole('columnheader').length).toBe(2);
  });

  it('rend le texte barré GFM (~~)', () => {
    render(<MessageBubble message={makeMessage({ content: 'prix ~~2990~~ 2490' })} />);
    const del = document.querySelector('del');
    expect(del?.textContent).toBe('2990');
  });
});

describe('MessageBubble - comparateur memo (US-010)', () => {
  const msg = makeMessage();

  it('égal quand seul onSaveAsCommand change d identité (closure recréée)', () => {
    expect(
      arePropsEqual(
        { message: msg, onSaveAsCommand: () => {} },
        { message: msg, onSaveAsCommand: () => {} }
      )
    ).toBe(true);
  });

  it('inégal quand le message change (nouveau contenu streamé)', () => {
    expect(
      arePropsEqual(
        { message: msg },
        { message: { ...msg, content: 'Bonjour le monde' } }
      )
    ).toBe(false);
  });

  it('inégal quand onSaveAsCommand apparaît ou disparaît', () => {
    expect(arePropsEqual({ message: msg }, { message: msg, onSaveAsCommand: () => {} })).toBe(
      false
    );
  });
});
