/**
 * P-159 : le contexte réellement transmis se lit près de la réponse.
 */
import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { MessageBubble } from './MessageBubble';
import type { Message } from '../../stores/chatStore';

vi.mock('../../services/api', async () => {
  const actual = await vi.importActual<typeof import('../../services/api')>('../../services/api');
  return { ...actual, downloadSkillFile: vi.fn(), fetchImageObjectUrl: vi.fn() };
});

function messageDe(over: Partial<Message> = {}): Message {
  return {
    id: 'm1',
    role: 'assistant',
    content: 'Voici la réponse.',
    timestamp: new Date(),
    ...over,
  };
}

describe('MessageBubble — contexte transmis (P-159)', () => {
  it('affiche les messages relus, au clavier et pour le lecteur d’écran', () => {
    render(<MessageBubble message={messageDe({
      contexte: { messages_relus: 12, messages_transmis: 12 },
    })} />);
    const ligne = screen.getByText('Contexte : 12 messages relus');
    expect(ligne).toHaveAttribute('tabindex', '0');
    expect(ligne).not.toHaveAttribute('aria-hidden');
    ligne.focus();
    expect(document.activeElement).toBe(ligne);
  });

  it('dit que le contexte a été raccourci, et de combien', () => {
    render(<MessageBubble message={messageDe({
      contexte: { messages_relus: 50, messages_transmis: 30 },
      provider: 'ollama',
    })} />);
    expect(screen.getByText('Contexte raccourci : 30 messages sur 50')).toBeInTheDocument();
    expect(screen.getByText('Local')).toBeInTheDocument();
  });

  it('reste masqué tant que la réponse s’écrit', () => {
    render(<MessageBubble message={messageDe({
      isStreaming: true,
      contexte: { messages_relus: 12, messages_transmis: 12 },
    })} />);
    expect(screen.queryByText(/Contexte/)).not.toBeInTheDocument();
  });
});
