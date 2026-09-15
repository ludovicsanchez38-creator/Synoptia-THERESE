/**
 * B-812 (cycle 9) : pendant l'attente d'une réponse, deux emplacements
 * s'affichaient : la bulle d'assistant vide (curseur clignotant) ET l'indicateur
 * « Réflexion... » du pied de liste. Un seul emplacement suffit.
 */
import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { useChatStore } from '../../stores/chatStore';
import { MessageList } from './MessageList';

vi.mock('react-virtuoso', () => ({
  Virtuoso: ({ components, data, itemContent }: { components?: { Header?: React.ComponentType; Footer?: React.ComponentType }; data?: unknown[]; itemContent?: (i: number, d: unknown) => React.ReactNode }) => {
    const Header = components?.Header; const Footer = components?.Footer;
    return <div>{Header ? <Header /> : null}{(data ?? []).map((d, i) => <div key={i}>{itemContent?.(i, d)}</div>)}{Footer ? <Footer /> : null}</div>;
  },
}));

const conversation = (messages: unknown[]) => ({ id: 'c1', title: 'Fil', messages, createdAt: new Date(), updatedAt: new Date(), messageCount: messages.length, synced: true });

describe('MessageList - B-812, un seul emplacement de réponse pendant l’attente', () => {
  beforeEach(() => useChatStore.setState({ currentConversationId: 'c1', isStreaming: true } as never));

  it('quand la bulle d’assistant en flux existe déjà, pas d’indicateur « Réflexion » en plus', () => {
    useChatStore.setState({ conversations: [conversation([
      { id: 'm1', role: 'user', content: 'Que peux-tu faire ?', timestamp: new Date() },
      { id: 'm2', role: 'assistant', content: '', timestamp: new Date(), isStreaming: true },
    ])] } as never);
    render(<MessageList />);
    expect(screen.queryByText(/Réflexion/)).toBeNull();
  });

  it('avant la première bulle d’assistant, l’indicateur reste', () => {
    useChatStore.setState({ conversations: [conversation([
      { id: 'm1', role: 'user', content: 'Que peux-tu faire ?', timestamp: new Date() },
    ])] } as never);
    render(<MessageList />);
    expect(screen.getByText(/Réflexion/)).toBeInTheDocument();
  });
});
