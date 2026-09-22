/** B-942 : état réellement créé par ChatInput avant d'attendre le premier jeton. */
import { act, render, screen } from '@testing-library/react';
import type { ComponentType, ReactNode } from 'react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { useChatStore, type Message } from '../../stores/chatStore';
import { useDemoStore } from '../../stores/demoStore';
import { MessageList } from './MessageList';

// JSDOM n'a pas de viewport : seule la virtualisation est remplacée.
// MessageBubble et TypingIndicator restent les composants de production.
vi.mock('react-virtuoso', () => ({
  Virtuoso: ({ components, data, itemContent }: {
    components?: { Header?: ComponentType; Footer?: ComponentType };
    data?: Message[];
    itemContent?: (index: number, message: Message) => ReactNode;
  }) => {
    const Header = components?.Header;
    const Footer = components?.Footer;
    return <div>
      {Header && <Header />}
      {(data ?? []).map((message, index) => <div key={message.id}>{itemContent?.(index, message)}</div>)}
      {Footer && <Footer />}
    </div>;
  },
}));

describe('B-942 : repère de durée dans la réponse locale en attente', () => {
  beforeEach(() => {
    useDemoStore.setState({ enabled: false });
    useChatStore.setState({
      conversations: [{
        id: 'c10-attente', title: 'Attente du premier jeton',
        createdAt: new Date(), updatedAt: new Date(), synced: true,
        messages: [
          { id: 'c10-question', role: 'user', content: 'Explique cette idée', timestamp: new Date() },
          { id: 'c10-reponse', role: 'assistant', content: '', timestamp: new Date(), isStreaming: true },
        ],
      }],
      currentConversationId: 'c10-attente',
      isStreaming: true,
      fournisseurCourant: 'ollama',
    });
  });

  it('garde le repère « plusieurs minutes » avec la bulle assistant vide sous Ollama', () => {
    render(<MessageList />);
    expect(screen.getAllByTestId('chat-message-item')).toHaveLength(2);
    expect(screen.getAllByText(/Avec un modèle local, cela peut prendre plusieurs minutes/)).toHaveLength(1);
    // B-812 reste respecté : pas de second emplacement « Réflexion... ».
    expect(screen.queryByText('Réflexion...')).not.toBeInTheDocument();
  });

  it('retire le repère lorsque le flux se termine', () => {
    render(<MessageList />);
    expect(screen.getAllByText(/plusieurs minutes/)).toHaveLength(1);
    act(() => {
      useChatStore.getState().updateMessage('c10-reponse', 'Réponse terminée');
      useChatStore.getState().setStreaming(false);
    });
    expect(screen.queryByText(/plusieurs minutes/)).not.toBeInTheDocument();
  });

  it('ne double pas le repère avant la création de la bulle assistant', () => {
    useChatStore.setState(state => ({ conversations: state.conversations.map(conversation => ({
      ...conversation, messages: conversation.messages.filter(message => message.role === 'user'),
    })) }));
    render(<MessageList />);
    expect(screen.getAllByText(/plusieurs minutes/)).toHaveLength(1);
    expect(screen.getAllByText('Réflexion...')).toHaveLength(1);
  });

  it('ne montre pas ce repère local pour la même attente chez un fournisseur distant', () => {
    useChatStore.setState({ fournisseurCourant: 'anthropic' });
    render(<MessageList />);
    expect(screen.getAllByTestId('chat-message-item')).toHaveLength(2);
    expect(screen.queryByText(/plusieurs minutes/)).not.toBeInTheDocument();
    expect(screen.queryByText('Réflexion...')).not.toBeInTheDocument();
  });
});
